import os
from jdaviz.core.tools import SidebarShortcutPlotOptions, SidebarShortcutExportPlot


ICON_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), 'data', 'icons'))

# point to the lcviz-version of plot options instead of jdaviz's
SidebarShortcutPlotOptions.plugin_name = 'lcviz-plot-options'
SidebarShortcutExportPlot.plugin_name = 'lcviz-export'


__all__ = []
