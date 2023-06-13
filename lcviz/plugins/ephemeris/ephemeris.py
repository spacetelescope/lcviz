import numpy as np
from traitlets import Bool, Float, List, Unicode, observe

from glue.core.link_helpers import LinkSame
from glue.core.message import DataCollectionAddMessage
from jdaviz.core.custom_traitlets import FloatHandleEmpty
from jdaviz.core.events import (NewViewerMessage, ViewerAddedMessage, ViewerRemovedMessage)
from jdaviz.core.registries import tray_registry
from jdaviz.core.template_mixin import (PluginTemplateMixin, SelectPluginComponent,
                                        DatasetSelectMixin)
from jdaviz.core.user_api import PluginUserApi

from lightkurve import periodogram

from lcviz.template_mixin import EditableSelectPluginComponent
from lcviz.viewers import PhaseScatterView


__all__ = ['Ephemeris']

_default_t0 = 0
_default_period = 1
_default_dpdt = 0


@tray_registry('ephemeris', label="Ephemeris")
class Ephemeris(PluginTemplateMixin, DatasetSelectMixin):
    """
    See the :ref:`Ephemeris Plugin Documentation <ephemeris>` for more details.

    Only the following attributes and methods are available through the
    public plugin API.

    * ``component`` (:class:`~lcviz.template_mixin.EditableSelectPluginComponent`):
      Label of the component corresponding to the active ephemeris.
    * :attr:`t0`:
      Zeropoint of the ephemeris.
    * :attr:`period`:
      Period of the ephemeris, defined at ``t0``.
    * :attr:`dpdt`:
      First derivative of the period of the ephemeris.
    * :meth:`ephemeris`
    * :meth:`ephemerides`
    * :meth:`update_ephemeris`
    * :meth:`create_phase_viewer`
    * :meth:`add_component`
    * :meth:`rename_component`
    * :meth:`times_to_phases`
    * ``dataset`` (:class:`~jdaviz.core.template_mixin.DatasetSelect`):
      Dataset to use for determining the period.
    * ``method`` (:class:`~jdaviz.core.template_mixing.SelectPluginComponent`):
      Method/algorithm to determine the period.
    """
    template_file = __file__, "ephemeris.vue"

    # EPHEMERIS
    component_mode = Unicode().tag(sync=True)
    component_edit_value = Unicode().tag(sync=True)
    component_items = List().tag(sync=True)
    component_selected = Unicode().tag(sync=True)

    phase_viewer_exists = Bool(False).tag(sync=True)

    t0 = FloatHandleEmpty(_default_t0).tag(sync=True)
    t0_step = Float(0.1).tag(sync=True)
    period = FloatHandleEmpty(_default_period).tag(sync=True)
    period_step = Float(0.1).tag(sync=True)
    dpdt = FloatHandleEmpty(_default_dpdt).tag(sync=True)
    dpdt_step = Float(0.1).tag(sync=True)

    # PERIOD FINDING
    method_items = List().tag(sync=True)
    method_selected = Unicode().tag(sync=True)

    method_spinner = Bool().tag(sync=True)
    method_err = Unicode().tag(sync=True)

    period_at_max_power = Float().tag(sync=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._ignore_ephem_change = False
        self._ephemerides = {}

        self.component = EditableSelectPluginComponent(self,
                                                       mode='component_mode',
                                                       edit_value='component_edit_value',
                                                       items='component_items',
                                                       selected='component_selected',
                                                       manual_options=['default'],
                                                       on_rename=self._on_component_rename,
                                                       on_remove=self._on_component_remove)
        # force the original entry in ephemerides with defaults
        self._change_component()

        self.method = SelectPluginComponent(self,
                                            items='method_items',
                                            selected='method_selected',
                                            manual_options=['Lomb-Scargle', 'Box Least Squares'])

        # TODO: could optimize by only updating for the new data entry only
        # (would require some refactoring and probably wouldn't have significant gains)
        self.hub.subscribe(self, DataCollectionAddMessage, handler=self._update_all_phase_arrays)
        self.hub.subscribe(self, ViewerAddedMessage, handler=self._check_if_phase_viewer_exists)
        self.hub.subscribe(self, ViewerRemovedMessage, handler=self._check_if_phase_viewer_exists)

    @property
    def user_api(self):
        expose = ['component', 'period', 'dpdt', 't0',
                  'ephemeris', 'ephemerides',
                  'update_ephemeris', 'create_phase_viewer',
                  'add_component', 'remove_component', 'rename_component',
                  'times_to_phases',
                  'dataset', 'method']
        return PluginUserApi(self, expose=expose)

    def _phase_comp_lbl(self, component):
        return f'phase:{component}'

    @property
    def phase_comp_lbl(self):
        return self._phase_comp_lbl(self.component_selected)

    def _phase_viewer_id(self, component):
        return f'flux-vs-phase:{component}'

    @property
    def phase_viewer_ids(self):
        viewer_ids = self.app.get_viewer_ids()
        return [self._phase_viewer_id(component) for component in self.component.choices
                if self._phase_viewer_id(component) in viewer_ids]

    @property
    def phase_viewer_id(self):
        return self._phase_viewer_id(self.component_selected)

    @property
    def ephemerides(self):
        return self._ephemerides

    @property
    def ephemeris(self):
        return self.ephemerides.get(self.component_selected, {})

    def _times_to_phases_callable(self, component):
        if component == self.component_selected:
            # retrieving from traitlets is cheaper than dictionaries
            t0 = self.t0
            period = self.period
            dpdt = self.dpdt
        else:
            ephem = self.ephemerides.get(component, {})
            t0 = ephem.get('t0', _default_t0)
            period = ephem.get('period', _default_period)
            dpdt = ephem.get('dpdt', _default_dpdt)

        def _callable(times):
            if dpdt != 0:
                return np.mod(1./dpdt * np.log(1 + dpdt/period*(times-t0)), 1.0)  # noqa
            else:
                return np.mod((times-t0)/period, 1.0)

        return _callable

    def times_to_phases(self, times, component=None):
        if component is None:
            component = self.component.selected

        return self._times_to_phases_callable(component)(times)

    def _update_all_phase_arrays(self, *args, component=None):
        if component is None:
            for component in self.component.choices:
                self._update_all_phase_arrays(component=component)
            return

        dc = self.app.data_collection

        phase_comp_lbl = self._phase_comp_lbl(component)

        # we'll create the callable function for this component once so it can be re-used
        _times_to_phases = self._times_to_phases_callable(component)

        new_links = []
        for i, data in enumerate(dc):
            times = data.get_component('World 0').data
            phases = _times_to_phases(times)

            if phase_comp_lbl in [comp.label for comp in data.components]:
                data.update_components({data.get_component(phase_comp_lbl): phases})
            else:
                data.add_component(phases, phase_comp_lbl)
                if i != 0:
                    # then we need to link this column back to dc[0]
                    # TODO: there must be a better way (again)...
                    dc0_comps = {str(comp): comp for comp in dc[0].components}
                    data_comps = {str(comp): comp for comp in data.components}
                    new_links += [LinkSame(dc0_comps.get(phase_comp_lbl),
                                           data_comps.get(phase_comp_lbl))]

        if len(new_links):
            dc.set_links(new_links)

        # update any plugin markers
        # TODO: eventually might need to loop over multiple matching viewers
        phase_viewer_id = self._phase_viewer_id(component)
        if phase_viewer_id in self.app.get_viewer_ids():
            phase_viewer = self.app.get_viewer(phase_viewer_id)
            for mark in phase_viewer.custom_marks:
                if hasattr(mark, 'update_phase_folding'):
                    mark.update_phase_folding()

        return phase_comp_lbl

    def create_phase_viewer(self):
        """
        Create a new phase viewer corresponding to ``component`` and populate the phase arrays
        with the current ephemeris, if necessary.
        """
        phase_viewer_id = self.phase_viewer_id
        dc = self.app.data_collection

        # check to see if this component already has a phase array.  We'll just check the first
        # item in the data-collection since the rest of the logic in this plugin /should/ populate
        # the arrays across all entries.
        if self.phase_comp_lbl not in [comp.label for comp in dc[0].components]:
            self.update_ephemeris()  # calls _update_all_phase_arrays

        if not self.phase_viewer_exists:
            # TODO: stack horizontally by default?
            self.app._on_new_viewer(NewViewerMessage(PhaseScatterView, data=None, sender=self.app),
                                    vid=phase_viewer_id, name=phase_viewer_id)

            time_viewer_item = self.app._get_viewer_item(self.app._jdaviz_helper._default_time_viewer_reference_name)  # noqa
            for data in dc:
                data_id = self.app._data_id_from_label(data.label)
                visible = time_viewer_item['selected_data_items'].get(data_id, 'hidden')
                self.app.set_data_visibility(phase_viewer_id, data.label, visible == 'visible')

        pv = self.app.get_viewer(phase_viewer_id)
        # TODO: there must be a better way to do this...
        pv.state.x_att = [comp for comp in dc[0].components if comp.label == self.phase_comp_lbl][0]
        return pv

    def vue_create_phase_viewer(self, *args):
        self.create_phase_viewer()

    def vue_period_halve(self, *args):
        self.period /= 2

    def vue_period_double(self, *args):
        self.period *= 2

    def _check_if_phase_viewer_exists(self, *args):
        self.phase_viewer_exists = self.phase_viewer_id in self.app.get_viewer_ids()

    def _on_component_rename(self, old_lbl, new_lbl):
        # this is triggered when the plugin component detects a change to the component name
        self._ephemerides[new_lbl] = self._ephemerides.pop(old_lbl, {})
        if self._phase_viewer_id(old_lbl) in self.app.get_viewer_ids():
            self.app._rename_viewer(self._phase_viewer_id(old_lbl), self._phase_viewer_id(new_lbl))
        self._check_if_phase_viewer_exists()

    def _on_component_remove(self, lbl):
        _ = self._ephemerides.pop(lbl, {})
        # remove the corresponding viewer, if it exists
        viewer_item = self.app._viewer_item_by_id(self._phase_viewer_id(lbl))
        if viewer_item is None:
            return
        cid = viewer_item.get('id', None)
        if cid is not None:
            self.app.vue_destroy_viewer_item(cid)

    def rename_component(self, old_lbl, new_lbl):
        # NOTE: the component will call _on_component_rename after updating
        self.component.rename_choice(old_lbl, new_lbl)

    def add_component(self, lbl, set_as_selected=True):
        self.component.add_choice(lbl, set_as_selected=set_as_selected)

    def remove_component(self, lbl):
        # NOTE: the component will call _on_component_remove after updating
        self.component.remove_choice(lbl)

    @observe('component_selected')
    def _change_component(self, *args):
        if not hasattr(self, 'component'):
            # plugin/traitlet startup
            return
        if self.component_selected == '':
            # no component selected (this can happen when removing all components)
            return
        self._check_if_phase_viewer_exists()
        ephem = self._ephemerides.get(self.component_selected, {})

        # we'll temporarily disable updating the phasing so that we can set all
        # traitlets simultaneously and THEN revising phase arrays if necessary
        self._ignore_ephem_change = True
        self.t0 = ephem.get('t0', self.t0)
        self.period = ephem.get('period', self.period)
        self.dpdt = ephem.get('dpdt', self.dpdt)

        # if this is a new component, update those default values back to the dictionary
        self.update_ephemeris(t0=self.t0, period=self.period, dpdt=self.dpdt)
        self._ignore_ephem_change = False
        if ephem:
            # if there were any changes applied by accessing the dictionary,
            # then we need to update phasing, etc (since we set _ignore_ephem_change)
            # otherwise, this is a new component and there is no need.
            self._ephem_traitlet_changed()

    def update_ephemeris(self, component=None, t0=None, period=None, dpdt=None):
        """
        Update the ephemeris for a given component.

        Parameters
        ----------
        component : str, optional
            label of the component.  If not provided or ``None``, will default to plugin value.
        t0 : float, optional
            value of t0 to replace
        period : float, optional
            value of period to replace
        dpdt : float, optional
            value of period to replace

        Returns
        -------
        dictionary of ephemeris corresponding to ``component``
        """
        if component is None:
            component = self.component_selected

        if component not in self.component.choices:
            raise ValueError(f"component must be one of {self.component.choices}")

        existing_ephem = self._ephemerides.get(component, {})
        for name, value in {'t0': t0, 'period': period, 'dpdt': dpdt}.items():
            if value is not None:
                existing_ephem[name] = value
                if component == self.component_selected:
                    setattr(self, name, value)

        self._ephemerides[component] = existing_ephem
        self._update_all_phase_arrays(component=component)
        return existing_ephem

    @observe('period', 'dpdt', 't0')
    def _ephem_traitlet_changed(self, event={}):
        if self._ignore_ephem_change:
            return
        for value in (self.period, self.dpdt, self.t0):
            if not isinstance(value, (int, float)):
                return
        if self.period <= 0:
            return

        def round_to_1(x):
            return round(x, -int(np.floor(np.log10(abs(x)))))

        # if phase-viewer doesn't yet exist in the app, create it now
        self.create_phase_viewer()

        # update value in the dictionary (to support multi-ephems)
        if event:
            self.update_ephemeris(**{event.get('name'): event.get('new')})
            # will call _update_all_phase_arrays
        else:
            self._update_all_phase_arrays(component=self.component_selected)

        # update step-sizes
        self.period_step = round_to_1(self.period/5000)
        self.dpdt_step = max(round_to_1(abs(self.period * self.dpdt)/1000) if self.dpdt != 0 else 0,
                             1./1000000)
        self.t0_step = round_to_1(self.period/1000)

    @observe('dataset_selected', 'method_selected')
    def _update_periodogram(self, *args):
        if not (hasattr(self, 'method') and hasattr(self, 'dataset')):
            return
        # TODO: support multiselect on self.dataset and combine light curves (or would that be a
        # dedicated plugin of its own)?
        self.method_spinner = True
        self.method_err = ''
        if self.method == 'Box Least Squares':
            try:
                per = periodogram.BoxLeastSquaresPeriodogram.from_lightcurve(self.dataset.selected_obj)  # noqa
            except Exception as err:
                self.method_spinner = False
                self.method_err = str(err)
                return
        elif self.method == 'Lomb-Scargle':
            try:
                per = periodogram.LombScarglePeriodogram.from_lightcurve(self.dataset.selected_obj)
            except Exception as err:
                self.method_spinner = False
                self.method_err = str(err)
                return
        else:
            self.method_spinner = False
            raise NotImplementedError(f"periodogram not implemented for {self.method}")

        # TODO: will need to return in display units once supported
        self.period_at_max_power = per.period_at_max_power.value
        self.method_spinner = False

    def vue_adopt_period_at_max_power(self, *args):
        self.period = self.period_at_max_power
