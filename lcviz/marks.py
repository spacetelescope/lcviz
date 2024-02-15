from astropy import units as u
import numpy as np

from jdaviz.core.marks import PluginLine, PluginScatter, SliceIndicatorMarks
from lcviz.viewers import PhaseScatterView

__all__ = ['LivePreviewTrend', 'LivePreviewFlattened', 'LivePreviewBinning']


def _slice_indicator_get_slice_axis(self, data):
    if hasattr(data, 'time'):
        return data.time.value * u.d
    return [] * u.dimensionless_unscaled


SliceIndicatorMarks._get_slice_axis = _slice_indicator_get_slice_axis


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
    def __init__(self, viewer, *args, **kwargs):
        self.viewer = viewer
        kwargs.setdefault('default_size', 16)
        super().__init__(viewer, *args, **kwargs)


class LivePreviewBinning(PluginScatter, WithPhaseSupport):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default_size', 16)
        super().__init__(*args, **kwargs)
