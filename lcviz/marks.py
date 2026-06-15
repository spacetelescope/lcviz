from astropy import units as u
import numpy as np

from jdaviz.core.marks import PluginLine, PluginScatter, SliceIndicatorMarks
from lcviz.viewers import PhaseScatterView

__all__ = ['LivePreviewTrend', 'LivePreviewFlattened', 'LivePreviewBinning']


def _slice_indicator_get_slice_axis(self, data):
    if hasattr(data, 'time'):
        return data.time.value * u.d
    return [] * u.dimensionless_unscaled


def _slice_indicator_set_visibility(self):
    # Override for lcviz: show indicator for 1D light curves, not just 3D cubes
    for dc in self._viewer.jdaviz_app.data_collection:
        # Show for 1D light curves (shape length 1) or 3D cubes
        if len(dc.shape) in (1, 3):
            self.visible = True
            self.label.visible = self._show_value
            return
    self.visible = False
    self.label.visible = False


SliceIndicatorMarks._get_slice_axis = _slice_indicator_get_slice_axis
SliceIndicatorMarks._set_visibility = _slice_indicator_set_visibility


class WithoutPhaseSupport:
    def update_ty(self, times, y):
        self.times = np.asarray(times)
        self.x = self.times
        self.y = np.asarray(y)


class WithPhaseSupport(WithoutPhaseSupport):
    def update_ty(self, times, y):
        self.times = np.asarray(times)
        self.update_phase_folding()
        self.y = np.asarray(y)

    def update_phase_folding(self):
        if not hasattr(self, 'times'):
            # update_ty has not been called yet, so there is
            # nothing to phase-fold
            return
        if isinstance(self.viewer, PhaseScatterView):
            self.x = self.viewer.times_to_phases(self.times)
        else:
            self.x = self.times


class LivePreviewTrend(PluginLine, WithoutPhaseSupport):
    def __init__(self, viewer, *args, **kwargs):
        self.viewer = viewer
        super().__init__(viewer, *args, **kwargs)


class LivePreviewFlattened(PluginScatter, WithPhaseSupport):
    def __init__(self, viewer, **kwargs):
        self.viewer = viewer
        kwargs.setdefault('default_size', 16)
        super().__init__(viewer, **kwargs)


class LivePreviewBinning(PluginScatter, WithPhaseSupport):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default_size', 16)
        super().__init__(*args, **kwargs)
