from jdaviz.configs.default.plugins import ViewerCreator
from jdaviz.core.registries import tool_registry, viewer_registry
from lcviz.events import EphemerisComponentChangedMessage

__all__ = ['ViewerCreator']


@tool_registry('lcviz-viewer-creator')
class ViewerCreator(ViewerCreator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.hub.subscribe(self, EphemerisComponentChangedMessage,
                           handler=self._rebuild_available_viewers)
        self._rebuild_available_viewers()

    def _rebuild_available_viewers(self, *args):
        # filter to lcviz-specific viewers only
        # list of dictionaries with name (registry name)
        # and label (what appears in dropdown and the default label of the viewer)

        if self.app._jdaviz_helper is not None:
            phase_viewers = [{'name': f'lcviz-phase-viewer:{e}', 'label': f'flux-vs-phase:{e}'}
                              for e in self.app._jdaviz_helper.plugins['Ephemeris'].component.choices]  # noqa
        else:
            phase_viewers = []

        self.viewer_types = [v for v in self.viewer_types if v['name'].startswith('lcviz')
                             and not v['label'].startswith('flux-vs-phase')] + phase_viewers
        self.send_state('viewer_types')

    def vue_create_viewer(self, name):
        if name.startswith('lcviz-phase-viewer') or name.startswith('flux-vs-phase'):
            ephem_comp = name.split(':')[1]
            ephem_plg = self.app._jdaviz_helper.plugins['Ephemeris']
            ephem_plg.create_phase_viewer(ephem_comp)
            return
        if name == 'flux-vs-time':
            # allow passing label and map to the name for upstream support
            name = 'lcviz-time-viewer'

        super().vue_create_viewer(name)
