from glue.core.message import (DataCollectionAddMessage,
                               DataCollectionDeleteMessage)
from jdaviz.configs.default.plugins import ViewerCreator
from jdaviz.core.events import NewViewerMessage
from jdaviz.core.registries import tool_registry
from lcviz.events import EphemerisComponentChangedMessage
from lcviz.viewers import TimeScatterView, CubeView

__all__ = ['ViewerCreator']


# overwrite requires upstream changes, we can do without if we just lose the tooltip
@tool_registry('g-viewer-creator', overwrite=True)
class ViewerCreator(ViewerCreator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for msg in (EphemerisComponentChangedMessage,
                    DataCollectionAddMessage,
                    DataCollectionDeleteMessage):
            self.hub.subscribe(self, msg,
                               handler=lambda x: self._rebuild_available_viewers())
        self._rebuild_available_viewers()

    def _rebuild_available_viewers(self, *args):
        # filter to lcviz-specific viewers only
        # list of dictionaries with name (registry name)
        # and label (what appears in dropdown and the default label of the viewer)

        if self.app._jdaviz_helper is not None:
            phase_viewers = [{'name': f'lcviz-phase-viewer:{e}', 'label': f'flux-vs-phase:{e}'}
                              for e in self.app._jdaviz_helper.plugins['Ephemeris'].component.choices]  # noqa
            if self.app._jdaviz_helper._has_cube_data:
                cube_viewers = [{'name': 'lcviz-cube-viewer', 'label': 'image'}]
            else:
                cube_viewers = []
        else:
            phase_viewers = [{'name': 'lcviz-phase-viewer:default',
                              'label': 'flux-vs-phase:default'}]
            cube_viewers = []

        self.viewer_types = [v for v in self.viewer_types if v['name'].startswith('lcviz')
                             and not v['label'].startswith('flux-vs-phase')
                             and not v['label'] in ('cube', 'image')] + phase_viewers + cube_viewers
        self.send_state('viewer_types')

    def vue_create_viewer(self, name):
        if name.startswith('lcviz-phase-viewer') or name.startswith('flux-vs-phase'):
            ephem_comp = name.split(':')[1]
            ephem_plg = self.app._jdaviz_helper.plugins['Ephemeris']
            ephem_plg.create_phase_viewer(ephem_comp)
            return
        if name in ('flux-vs-time', 'lcviz-time-viewer'):
            # allow passing label and map to the name for upstream support
            viewer_id = self.app._jdaviz_helper._get_clone_viewer_reference('flux-vs-time')
            self.app._on_new_viewer(NewViewerMessage(TimeScatterView, data=None, sender=self.app),
                                    vid=viewer_id, name=viewer_id)
            return
        if name in ('image', 'lcviz-cube-viewer'):
            viewer_id = self.app._jdaviz_helper._get_clone_viewer_reference('image')
            self.app._on_new_viewer(NewViewerMessage(CubeView, data=None, sender=self.app),
                                    vid=viewer_id, name=viewer_id)
            return

        super().vue_create_viewer(name)
