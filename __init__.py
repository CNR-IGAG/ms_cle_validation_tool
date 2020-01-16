# -*- coding: utf-8 -*-
"""
/***************************************************************************
 validation_tool
                                 A QGIS plugin
 Validation tool for Seismic Microzonation projects
                             -------------------
        begin                : 2019-12-08
        copyright            : (C) 2019 by IGAG-CNR
        email                : labgis@igag.cnr.it
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load validation_tool class from file validation_tool.

    :param iface: A QGIS interface instance.
    :type iface: QgisInterface
    """
    #
    from .validation_tool import validation_tool
    return validation_tool(iface)
