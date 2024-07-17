# -*- coding: utf-8 -*-

"""
***************************************************************************
    algorithm.py
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

import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication

from qgis.core import QgsProcessingAlgorithm
from openlittermap.utils import PLUGIN_ROOT


class OpenLitterMapAlgorithm(QgsProcessingAlgorithm):
    def __init__(self):
        super().__init__()

    def createInstance(self):
        return type(self)()

    def icon(self):
        return QIcon(os.path.join(PLUGIN_ROOT, "icons", "openlittermap.svg"))

    def tr(self, text):
        return QCoreApplication.translate(self.__class__.__name__, text)
