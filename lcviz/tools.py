import os

from glue.config import viewer_tool
from glue.viewers.common.tool import Tool

from jdaviz.core.tools import SidebarShortcutPlotOptions, SidebarShortcutExportPlot

ICON_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), 'data', 'icons'))

# point to the lcviz-version of plot options instead of jdaviz's
SidebarShortcutPlotOptions.plugin_name = 'lcviz-plot-options'
SidebarShortcutExportPlot.plugin_name = 'lcviz-export'


__all__ = ['ViewerClone']


@viewer_tool
class ViewerClone(Tool):
    icon = os.path.join(ICON_DIR, 'viewer_clone')
    tool_id = 'lcviz:viewer_clone'
    action_text = 'Clone viewer'
    tool_tip = 'Clone this viewer'

    def activate(self):
        self.viewer.clone_viewer()
