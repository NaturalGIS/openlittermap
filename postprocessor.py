# -*- coding: utf-8 -*-

"""
***************************************************************************
    postprocessor.py
    ---------------------
    Date                 : August 2024
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

from qgis.core import (
    QgsProcessingLayerPostProcessorInterface,
    QgsVectorLayer,
    QgsEditorWidgetSetup,
)


class SetStylePostprocessor(QgsProcessingLayerPostProcessorInterface):

    instance = None

    def postProcessLayer(self, layer, context, feedback):

        if not isinstance(layer, QgsVectorLayer):
            return

        config = {}
        config["DocumentViewer"] = 1
        config["FileWidget"] = True
        config["UseLink"] = True
        config["FullUrl"] = True
        config["StorageType"] = "AWSS3"
        params = {}
        params["properties"] = {
            "storageUrl": {"active": True, "field": "photo", "type": 2}
        }
        params["type"] = "collection"
        config["PropertyCollection"] = params
        layer.setEditorWidgetSetup(
            layer.fields().lookupField("photo"),
            QgsEditorWidgetSetup("ExternalResource", config),
        )

    @staticmethod
    def create():
        SetStylePostprocessor.instance = SetStylePostprocessor()
        return SetStylePostprocessor.instance
