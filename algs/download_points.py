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
from datetime import datetime

from qgis.PyQt.QtCore import QMetaType, QUrl, QDateTime
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
    QgsProcessingParameterExtent,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
)

from openlittermap.algorithm import OpenLitterMapAlgorithm


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
                Qgis.ProcessingNumberParameterType.Integer,
                2024,
                minValue=2017,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr("Output"))
        )

    def processAlgorithm(self, parameters, context, feedback):
        self.feedback = feedback

        crs_wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
        extent = self.parameterAsExtent(parameters, self.EXTENT, context, crs_wgs84)

        year = self.parameterAsInt(parameters, self.YEAR, context)
        current_year = datetime.now().year
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

        feedback.pushInfo(self.tr("Parsing data…"))
        content = reply.content().data().decode()
        try:
            data = json.loads(content)
        except json.decoder.JSONDecodeError as e:
            feedback.reportError(self.tr("Server reply is not a valid JSON"), True)

        fields = QgsFields()
        fields.append(QgsField("descr", QMetaType.QString))
        fields.append(QgsField("photo", QMetaType.QString))
        fields.append(QgsField("date", QMetaType.QDateTime))

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.OUTPUT, context, fields, Qgis.WkbType.Point, crs_wgs84
        )
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        for point in data["features"]:
            if feedback.isCanceled():
                break

            attrs = point["properties"]

            f = QgsFeature()
            f.setFields(fields)
            f["descr"] = attrs["result_string"]
            f["photo"] = attrs["filename"]
            f["date"] = QDateTime.fromString(attrs["datetime"], "yyyy-MM-dd HH:mm:ss")

            coords = point["geometry"]["coordinates"]
            g = QgsGeometry.fromPointXY(QgsPointXY(coords[1], coords[0]))
            f.setGeometry(g)

            sink.addFeature(f, QgsFeatureSink.Flag.FastInsert)

        return {self.OUTPUT: dest_id}

    def download_progress(self, bytes_received: int, bytes_total: int):
        if not self.feedback.isCanceled() and bytes_total > 0:
            progress = (bytes_received * 100) / bytes_total
            if progress < 100:
                self.feedback.setProgress(progress)
