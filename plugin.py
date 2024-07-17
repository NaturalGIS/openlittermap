# -*- coding: utf-8 -*-

"""
***************************************************************************
    plugin.py
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

from qgis.PyQt.QtCore import QCoreApplication, QTranslator
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon

from qgis.core import QgsApplication

from openlittermap.provider import OpenLitterMapProvider
from openlittermap.utils import PLUGIN_ROOT


class OpenLitterMapPlugin:
    def __init__(self, iface):
        self.iface = iface

        locale = QgsApplication.locale()
        qm_path = os.path.join(PLUGIN_ROOT, "i18n", f"openlittermap_{locale}.qm")

        if os.path.exists(qm_path):
            self.translator = QTranslator()
            self.translator.load(qm_path)
            QCoreApplication.installTranslator(self.translator)

        self.provider = OpenLitterMapProvider()

    def initProcessing(self):
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)

    def tr(self, text):
        return QCoreApplication.translate(self.__class__.__name__, text)
