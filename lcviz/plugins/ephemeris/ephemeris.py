import numpy as np
from traitlets import Float, List, Unicode, observe

from jdaviz.core.custom_traitlets import FloatHandleEmpty
from jdaviz.core.events import NewViewerMessage
from jdaviz.core.registries import tray_registry
from jdaviz.core.template_mixin import PluginTemplateMixin, SelectPluginComponent
from jdaviz.core.user_api import PluginUserApi

from lcviz.viewers import PhaseScatterView


__all__ = ['Ephemeris']


@tray_registry('ephemeris', label="Ephemeris")
class Ephemeris(PluginTemplateMixin):
    """
    See the :ref:`Ephemeris Plugin Documentation <ephemeris>` for more details.

    Only the following attributes and methods are available through the
    public plugin API.

    * ``component`` (:class:`~jdaviz.core.template_mixin.SelectPluginComponent`):
      Label of the component corresponding to the active ephemeris.
    * :attr:`t0`:
      Zeropoint of the ephemeris.
    * :attr:`period`:
      Period of the ephemeris, defined at ``t0``.
    * :attr:`dpdt`:
      First derivative of the period of the ephemeris.
    * :meth:`create_phase_viewer`

    """
    template_file = __file__, "ephemeris.vue"

    component_items = List().tag(sync=True)
    component_selected = Unicode().tag(sync=True)

    t0 = FloatHandleEmpty(0).tag(sync=True)
    t0_step = Float(0.1).tag(sync=True)
    period = FloatHandleEmpty(1).tag(sync=True)
    period_step = Float(0.1).tag(sync=True)
    dpdt = FloatHandleEmpty(0).tag(sync=True)
    dpdt_step = Float(0.1).tag(sync=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO: support renaming components (including renaming the applicable viewer)
        # TODO: support for creating new components
        self.component = SelectPluginComponent(self,
                                               items='component_items',
                                               selected='component_selected',
                                               manual_options=['default'])

    @property
    def user_api(self):
        expose = ['component', 'period', 'dpdt', 't0', 'create_phase_viewer']
        return PluginUserApi(self, expose=expose)

    @property
    def phase_comp_lbl(self):
        return f'phase:{self.component.selected}'

    def _update_all_phase_arrays(self):
        dc = self.app.data_collection
        phase_comp_lbl = self.phase_comp_lbl

        for data in dc:
            times = data.get_component('World 0').data
            if self.dpdt != 0:
                phases = np.mod(1./self.dpdt * np.log(1 + self.dpdt/self.period*(times-self.t0)), 1.0)  # noqa
            else:
                phases = np.mod((times-self.t0)/self.period, 1.0)

            if phase_comp_lbl in [comp.label for comp in data.components]:
                data.update_components({data.get_component(phase_comp_lbl): phases})
            else:
                data.add_component(phases, phase_comp_lbl)

        return phase_comp_lbl

    def create_phase_viewer(self):
        """
        Create a new phase viewer corresponding to ``component`` and populate the phase arrays
        with the current ephemeris, if necessary.
        """
        # TODO: depending on how adding a new component is implemented, we might need a check
        # and return here

        phase_viewer_id = f'flux-vs-phase:{self.component.selected}'
        dc = self.app.data_collection

        # check to see if this component already has a phase array.  We'll just check the first
        # item in the data-collection since the rest of the logic in this plugin /should/ populate
        # the arrays across all entries.
        # TODO: this requires having a listener on adding data to the app to create phase arrays!
        if self.phase_comp_lbl not in [comp.label for comp in dc[0].components]:
            self._update_all_phase_arrays()

        if phase_viewer_id not in self.app.get_viewer_ids():
            # TODO: stack horizontally by default?
            self.app._on_new_viewer(NewViewerMessage(PhaseScatterView, data=None, sender=self.app),
                                    vid=phase_viewer_id, name=phase_viewer_id)

            time_viewer_item = self.app._get_viewer_item(self.app._jdaviz_helper._default_time_viewer_reference_name)
            for data in dc:
                data_id = self.app._data_id_from_label(data.label)
                visible = time_viewer_item['selected_data_items'].get(data_id, 'hidden')
                self.app.set_data_visibility(phase_viewer_id, data.label, visible=='visible')

        pv = self.app.get_viewer(phase_viewer_id)
        # TODO: there must be a better way to do this...
        pv.state.x_att = [comp for comp in dc[0].components if comp.label == self.phase_comp_lbl][0]
        return pv

    @observe('period', 'dpdt', 't0')
    def _period_changed(self, *args):
        for value in (self.period, self.dpdt, self.t0):
            if not isinstance(value, (int, float)):
                return
        if self.period <= 0:
            return

        def round_to_1(x):
            return round(x, -int(np.floor(np.log10(abs(x)))))

        self._update_all_phase_arrays()

        # if phase-viewer doesn't yet exist in the app, create it now
        self.create_phase_viewer()

        # update step-sizes
        self.period_step = round_to_1(self.period/5000)
        self.dpdt_step = max(round_to_1(abs(self.dpdt)/10000) if self.dpdt != 0 else 0, 0.00001)
        self.t0_step = round_to_1(self.period/1000)
