import os
from jdaviz.configs.cubeviz.plugins.tools import SelectSlice


ICON_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), 'data', 'icons'))


# Override SelectSlice tool visibility to include 1D light curves
def _selectslice_is_visible(self):
    # visible if any 1D light curve or 3D cube-like data is present
    for dc in self.viewer.jdaviz_app.data_collection:
        if dc.ndim in (1, 3):
            return True
    return False


def _selectslice_label(self):
    viewer_label = getattr(self.viewer, '_slice_tool_label', 'cube slice')
    return f'Select {viewer_label}'


SelectSlice.is_visible = _selectslice_is_visible
SelectSlice.action_text = property(_selectslice_label)
SelectSlice.tool_tip = property(_selectslice_label)


__all__ = []
