# -*- coding: utf-8 -*-

"""
***************************************************************************
    provider.py
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

from qgis.core import QgsProcessingProvider

from openlittermap.algs.download_points import DownloadPoints
from openlittermap.utils import PLUGIN_ROOT


class OpenLitterMapProvider(QgsProcessingProvider):
    def __init__(self):
        super().__init__()
        self.algs = list()

    def id(self):
        return "openlittermap"

    def name(self):
        return "OpenLitterMap"

    def longName(self):
        return "OpenLitterMap"

    def icon(self):
        return QIcon(os.path.join(PLUGIN_ROOT, "icons", "openlittermap.svg"))

    def load(self):
        self.refreshAlgorithms()
        return True

    def unload(self):
        pass

    def loadAlgorithms(self):
        self.algs = [DownloadPoints()]
        for a in self.algs:
            self.addAlgorithm(a)

    def tr(self, string):
        return QCoreApplication.translate(self.__class__.__name__, string)
