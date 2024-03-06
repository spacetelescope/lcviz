from jdaviz.configs.default.plugins import ViewerCreator
from jdaviz.core.registries import tool_registry, viewer_registry
from lcviz.events import EphemerisComponentChangedMessage
from lcviz.viewers import ephem_component_from_phase_viewer_name

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
            phase_viewers = [{'name': 'lcviz-phase-viewer', 'label': f'flux-vs-phase:{e}'}
                              for e in self.app._jdaviz_helper.plugins['Ephemeris'].component.choices]  # noqa
        else:
            phase_viewers = []

        self.viewer_types = [v for v in self.viewer_types if v['name'].startswith('lcviz')
                             and v['label'] != 'flux-vs-phase'] + phase_viewers

    def vue_create_viewer(self, name):
        for viewer_item in self.viewer_types:
            if viewer_item['name'] == name:
                label = viewer_item['label']
                break
        else:
            label = viewer_registry.members[name]['label']

        if label in self.app._jdaviz_helper.viewers:
            # clone whenever possible
            # TODO: update this to not rely directly on the label for phase-viewers, but rather
            # checking for the same ephemeris
            self.app._jdaviz_helper.viewers[label]._obj.clone_viewer()
            return

        if name == 'lcviz-phase-viewer':
            ephem_comp = ephem_component_from_phase_viewer_name(label)
            ephem_plg = self.app._jdaviz_helper.plugins['Ephemeris']
            ephem_plg.create_phase_viewer(ephem_comp)
            return

        super().vue_create_viewer(name)
