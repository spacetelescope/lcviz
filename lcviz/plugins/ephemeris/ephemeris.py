from traitlets import observe

from jdaviz.core.custom_traitlets import FloatHandleEmpty
from jdaviz.core.events import NewViewerMessage
from jdaviz.core.registries import tray_registry
from jdaviz.core.template_mixin import PluginTemplateMixin, DatasetSelectMixin
from jdaviz.core.user_api import PluginUserApi

from lcviz.viewers import PhaseScatterView


__all__ = ['Ephemeris']


@tray_registry('ephemeris', label="Ephemeris")
class Ephemeris(PluginTemplateMixin, DatasetSelectMixin):
    """
    See the :ref:`Ephemeris Plugin Documentation <ephemeris>` for more details.

    Only the following attributes and methods are available through the
    public plugin API.

    * :attr:`period`:
      Period of the ephemeris.
    * :attr:`t0`:
      Zeropoint of the ephemeris.
    * :meth:`create_phase_viewer`

    """
    period = FloatHandleEmpty().tag(sync=True)
    t0 = FloatHandleEmpty().tag(sync=True)

    template_file = __file__, "ephemeris.vue"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def user_api(self):
        expose = ['period', 'create_phase_viewer']
        return PluginUserApi(self, expose=expose)

    def create_phase_viewer(self, phase_viewer_id='phase-viewer'):
        if phase_viewer_id not in self.app.get_viewer_ids():
            # TODO: stack horizontally by default?
            self.app._on_new_viewer(NewViewerMessage(PhaseScatterView, data=None, sender=self.app),
                                    vid=phase_viewer_id, name=phase_viewer_id)

            time_viewer_item = self.app._get_viewer_item(self.app._jdaviz_helper._default_time_viewer_reference_name)
            for data in self.app.data_collection:
                data_id = self.app._data_id_from_label(data.label)
                visible = time_viewer_item['selected_data_items'].get(data_id, 'hidden')
                self.app.set_data_visibility(phase_viewer_id, data.label, visible=='visible')

    @observe('period', 't0')
    def _period_changed(self, *args):
        for value in (self.period, self.t0):
            if not isinstance(value, (int, float)):
                return
        if self.period <= 0:
            return

        # if phase-viewer doesn't yet exist in the app, create it now
        self.create_phase_viewer('phase-viewer')
