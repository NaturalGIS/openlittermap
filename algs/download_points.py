# -*- coding: utf-8 -*-

"""
***************************************************************************
    download_points.py
    ---------------------
    Date                 : July 2024
    Copyright            : (C) 2024 by NaturalGIS
    Email                : info at naturalgis dot pt
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

import json

from qgis.PyQt.QtCore import QVariant, QUrl, QDateTime
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply

from qgis.core import (
    Qgis,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsPointXY,
    QgsFeature,
    QgsFeatureSink,
    QgsCoordinateReferenceSystem,
    QgsBlockingNetworkRequest,
    QgsProcessingException,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterExtent,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
)

from openlittermap.algorithm import OpenLitterMapAlgorithm
from openlittermap.postprocessor import SetStylePostprocessor


class DownloadPoints(OpenLitterMapAlgorithm):

    EXTENT = "EXTENT"
    YEAR = "YEAR"
    OUTPUT = "OUTPUT"

    def name(self):
        return "downloadpoints"

    def displayName(self):
        return self.tr("Download points")

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterExtent(self.EXTENT, self.tr("Area of interest"))
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.YEAR,
                self.tr("Year"),
                QgsProcessingParameterNumber.Integer,
                2024,
                minValue=2017,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr("Output"))
        )

    def processAlgorithm(self, parameters, context, feedback):
        self.multistep_feedback = QgsProcessingMultiStepFeedback(2, feedback)

        crs_wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
        extent = self.parameterAsExtent(parameters, self.EXTENT, context, crs_wgs84)

        year = self.parameterAsInt(parameters, self.YEAR, context)
        current_year = QDateTime.currentDateTime().date().year()
        if year > current_year:
            raise QgsProcessingException(
                self.tr("Input year could not be greater than current year.")
            )

        feedback.pushInfo(self.tr("Fetching data from the OpenLitterMap…"))

        # using zoom levels 0-16 will return clusters, but we want actual points
        # so we use zoom level 18
        url = (
            f"https://openlittermap.com/global/points?zoom=18&"
            f'bbox={{"left":{extent.xMinimum()},"bottom":{extent.yMinimum()},'
            f'"right":{extent.xMaximum()},"top":{extent.yMaximum()}}}'
            f"&year={year}"
        )

        request = QNetworkRequest(QUrl(url))
        blocking_request = QgsBlockingNetworkRequest()
        blocking_request.downloadProgress.connect(self.download_progress)
        res = blocking_request.get(request)

        if res != QgsBlockingNetworkRequest.NoError:
            feedback.reportError(blocking_request.errorMessage(), True)

        reply = blocking_request.reply()
        if reply.error() == QNetworkReply.OperationCanceledError:
            feedback.reportError(self.tr("Download was canceled"), True)

        if reply.error() != QNetworkReply.NoError:
            feedback.reportError(reply.errorString(), True)

        self.multistep_feedback.setCurrentStep(1)

        feedback.pushInfo(self.tr("Parsing data…"))
        content = reply.content().data().decode()
        try:
            data = json.loads(content)
        except json.decoder.JSONDecodeError as e:
            feedback.reportError(self.tr("Server reply is not a valid JSON"), True)

        fields = QgsFields()
        fields.append(QgsField("description", QVariant.String))
        fields.append(QgsField("photo", QVariant.String))
        fields.append(QgsField("date", QVariant.DateTime))
        fields.append(QgsField("verified", QVariant.Bool))
        fields.append(QgsField("picked_up", QVariant.Bool))
        fields.append(QgsField("username", QVariant.String))
        fields.append(QgsField("team", QVariant.String))

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.OUTPUT, context, fields, Qgis.WkbType.Point, crs_wgs84
        )
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        total = len(data["features"])
        step = 100 / total if total > 0 else 0
        for i, point in enumerate(data["features"]):
            if feedback.isCanceled():
                break

            attrs = point["properties"]

            f = QgsFeature()
            f.setFields(fields)
            f["description"] = attrs["result_string"]
            f["photo"] = attrs["filename"]
            f["date"] = QDateTime.fromString(attrs["datetime"], "yyyy-MM-dd HH:mm:ss")
            f["verified"] = attrs["verified"]
            f["picked_up"] = attrs["picked_up"]
            f["username"] = attrs["username"]
            f["team"] = attrs["team"]

            coords = point["geometry"]["coordinates"]
            g = QgsGeometry.fromPointXY(QgsPointXY(coords[1], coords[0]))
            f.setGeometry(g)

            sink.addFeature(f, QgsFeatureSink.Flag.FastInsert)
            self.multistep_feedback.setProgress(i * step)

        if context.willLoadLayerOnCompletion(dest_id):
            context.layerToLoadOnCompletionDetails(dest_id).setPostProcessor(
                SetStylePostprocessor.create()
            )

        return {self.OUTPUT: dest_id}

    def download_progress(self, bytes_received: int, bytes_total: int):
        if not self.multistep_feedback.isCanceled() and bytes_total > 0:
            progress = (bytes_received * 100) / bytes_total
            if progress < 100:
                self.multistep_feedback.setProgress(progress)
