import os
from jdaviz.core.tools import SidebarShortcutPlotOptions, SidebarShortcutExportPlot
from jdaviz.configs.cubeviz.plugins.tools import SelectSlice


ICON_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), 'data', 'icons'))

# point to the lcviz-version of plot options instead of jdaviz's
SidebarShortcutPlotOptions.plugin_name = 'lcviz-plot-options'
SidebarShortcutExportPlot.plugin_name = 'lcviz-export'


# Override SelectSlice tool visibility to include 1D light curves
def _selectslice_is_visible(self):
    # visible if any 1D light curve or 3D cube-like data is present
    for dc in self.viewer.jdaviz_app.data_collection:
        if dc.ndim in (1, 3):
            return True
    return False


SelectSlice.is_visible = _selectslice_is_visible


__all__ = []
