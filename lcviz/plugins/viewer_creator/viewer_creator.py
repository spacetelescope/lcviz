from jdaviz.configs.default.plugins import ViewerCreator
from jdaviz.core.registries import tool_registry, viewer_registry
from lcviz.events import EphemerisComponentChangedMessage

__all__ = ['ViewerCreator']


@tool_registry('g-viewer-creator', overwrite=True)  # overwrite requires upstream changes, we can do without if we just lose the tooltip
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
            self.app._jdaviz_helper.viewers[label]._obj.clone_viewer()
            return

        if name == 'lcviz-phase-viewer':
            # TODO: parse label to get ephemeris
            # TODO: copy of plugin and set the correct ephemeris (or allow create_phase_viewer to take ephem component)
            self.app._jdaviz_helper.plugins['Ephemeris'].create_phase_viewer()
            return

        super().vue_create_viewer(name)
