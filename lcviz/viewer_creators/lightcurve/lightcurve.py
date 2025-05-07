from traitlets import observe
from traitlets.config import Configurable

from jdaviz.core.viewer_creators import BaseViewerCreator
from jdaviz.core.registries import viewer_creator_registry
from jdaviz.core.user_api import ViewerCreatorUserApi

from lcviz.components import EphemerisSelectMixin
from lcviz.viewers import TimeScatterView, PhaseScatterView
from lcviz.utils import is_lc, is_tpf

__all__ = ['FluxVsTimeViewerCreator']


@viewer_creator_registry('Flux vs Time')
class FluxVsTimeViewerCreator(BaseViewerCreator):
    template_file = __file__, "../base_viewer_creator.vue"

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self.dataset.filters = [is_lc]
        self.viewer_label_default = 'flux-vs-time'  # TODO: append suffix if taken

    @property
    def viewer_class(self):
        return TimeScatterView


@viewer_creator_registry('Flux vs Phase')
class FluxVsPhaseViewerCreator(BaseViewerCreator, EphemerisSelectMixin):
    template_file = __file__, "./phase_viewer_creator.vue"

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self.dataset.filters = [is_lc]
        self.viewer_label_default = 'flux-vs-phase'  # TODO: append suffix if taken

    @property
    def viewer_class(self):
        return PhaseScatterView

    @property
    def user_api(self):
        return ViewerCreatorUserApi(self, expose=['ephemeris'])

    @observe('ephemeris_items')
    def _update_ephemeris_items(self, change):
        self._set_is_relevant()
        if not self.ephemeris_selected:
            self.ephemeris.select_default()

    @observe('ephemeris_selected')
    def _ephemeris_selected_changed(self, change):
        self.viewer_label_default = f'flux-vs-phase:{self.ephemeris.selected}'

    def _set_is_relevant(self):
        if not len(self.dataset_items) or not len(self.ephemeris_items):
            self.is_relevant = False
        else:
            self.is_relevant = True

    def __call__(self):
        nv = super().__call__()
        ephem_plg = self.app._jdaviz_helper.plugins['Ephemeris']
        ephem_plg._obj._set_viewer_to_ephem_component(nv._obj, self.ephemeris.selected)
        return nv
