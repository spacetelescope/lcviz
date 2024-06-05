import numpy as np
from astropy.time import Time
from traitlets import Bool, Float, List, Unicode, observe

from glue.core.link_helpers import LinkSame
from glue.core.message import DataCollectionAddMessage
from jdaviz.core.custom_traitlets import FloatHandleEmpty
from jdaviz.core.events import (NewViewerMessage, ViewerAddedMessage, ViewerRemovedMessage)
from jdaviz.core.registries import tray_registry
from jdaviz.core.template_mixin import (PluginTemplateMixin, DatasetSelectMixin,
                                        SelectPluginComponent, EditableSelectPluginComponent)
from jdaviz.core.user_api import PluginUserApi

from lightkurve import periodogram, FoldedLightCurve

from lcviz.events import EphemerisComponentChangedMessage, EphemerisChangedMessage
from lcviz.viewers import PhaseScatterView
from lcviz.utils import is_not_tpf

__all__ = ['Ephemeris']

_default_t0 = 0.0
_default_period = 1.0
_default_dpdt = 0.0
_default_wrap_at = 1.0


@tray_registry('ephemeris', label="Ephemeris")
class Ephemeris(PluginTemplateMixin, DatasetSelectMixin):
    """
    See the :ref:`Ephemeris Plugin Documentation <ephemeris>` for more details.

    Only the following attributes and methods are available through the
    :ref:`public plugin API <plugin-apis>`:

    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.show`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.open_in_tray`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.close_in_tray`
    * ``component`` (:class:`~jdaviz.core.template_mixin.EditableSelectPluginComponent`):
      Label of the component corresponding to the active ephemeris.
    * :attr:`t0` : float
      Zeropoint of the ephemeris.
    * :attr:`period` : float
      Period of the ephemeris, defined at ``t0``.
    * :attr:`dpdt` : float
      First derivative of the period of the ephemeris.
    * :attr:`wrap_at` : float
      Phase at which to wrap (phased data will encompass the range 1-wrap_at to wrap_at).
    * :meth:`ephemeris`
    * :meth:`ephemerides`
    * :meth:`update_ephemeris`
    * :meth:`create_phase_viewer`
    * :meth:`add_component`
    * :meth:`rename_component`
    * :meth:`times_to_phases`
    * :meth:`phases_to_times`
    * :meth:`get_data`
    * ``dataset`` (:class:`~jdaviz.core.template_mixin.DatasetSelect`):
      Dataset to use for determining the period.
    * ``method`` (:class:`~jdaviz.core.template_mixin.SelectPluginComponent`):
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
    wrap_at = FloatHandleEmpty(_default_wrap_at).tag(sync=True)

    # PERIOD FINDING
    method_items = List().tag(sync=True)
    method_selected = Unicode().tag(sync=True)

    method_spinner = Bool().tag(sync=True)
    method_err = Unicode().tag(sync=True)

    period_at_max_power = Float().tag(sync=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._default_initialized = False
        self._ignore_ephem_change = False
        self._ephemerides = {}
        self._prev_wrap_at = _default_wrap_at

        self.dataset.add_filter(is_not_tpf)

        self.component = EditableSelectPluginComponent(self,
                                                       name='ephemeris',
                                                       mode='component_mode',
                                                       edit_value='component_edit_value',
                                                       items='component_items',
                                                       selected='component_selected',
                                                       manual_options=['default'],
                                                       on_add=self._on_component_add,
                                                       on_rename_after_selection=self._on_component_rename,  # noqa
                                                       on_remove_after_selection=self._on_component_remove,  # noqa
                                                       validate_choice=self._validate_component)

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
        expose = ['component', 'period', 'dpdt', 't0', 'wrap_at',
                  'ephemeris', 'ephemerides',
                  'update_ephemeris', 'create_phase_viewer',
                  'add_component', 'remove_component', 'rename_component',
                  'times_to_phases', 'phases_to_times', 'get_data',
                  'dataset', 'method', 'period_at_max_power', 'adopt_period_at_max_power']
        return PluginUserApi(self, expose=expose)

    def _phase_comp_lbl(self, component=None):
        if component is None:
            component = self.component_selected
        if self.app._jdaviz_helper is None:
            # duplicate logic from helper in case this is ever called before the helper
            # is fully intialized
            return f'phase:{component}'
        return self.app._jdaviz_helper._phase_comp_lbl(component)

    @property
    def phase_comp_lbl(self):
        return self._phase_comp_lbl()

    def _generate_phase_viewer_id(self, component=None):
        if component is None:
            component = self.component_selected
        return self.app._jdaviz_helper._get_clone_viewer_reference(f'flux-vs-phase:{component}')

    def _get_phase_viewers(self, lbl=None):
        if lbl is None:
            lbl = self.component_selected
        return [viewer for vid, viewer in self.app._viewer_store.items()
                if isinstance(viewer, PhaseScatterView)
                and viewer._ephemeris_component == lbl]

    @property
    def default_phase_viewer(self):
        if not self.phase_viewer_exists:
            return None
        # we'll just treat the "default" as the first viewer connected to this
        # ephemeris component
        return self._get_phase_viewers()[0]

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
            wrap_at = self.wrap_at
        else:
            ephem = self.ephemerides.get(component, {})
            t0 = ephem.get('t0', _default_t0)
            period = ephem.get('period', _default_period)
            dpdt = ephem.get('dpdt', _default_dpdt)
            wrap_at = ephem.get('wrap_at', _default_wrap_at)

        def _callable(times):
            if hasattr(times, '__len__') and not len(times):
                return []
            if dpdt != 0:
                return np.mod(1./dpdt * np.log(1 + dpdt/period*(times-t0)) + (1-wrap_at), 1.0) - (1-wrap_at)  # noqa
            else:
                return np.mod((times-t0)/period + (1-wrap_at), 1.0) - (1-wrap_at)

        return _callable

    def times_to_phases(self, times, ephem_component=None):
        if ephem_component is None:
            ephem_component = self.component.selected

        return self._times_to_phases_callable(ephem_component)(times)

    def phases_to_times(self, phases, ephem_component=None):
        if ephem_component is None:
            ephem_component = self.component.selected

        # this is not used internally, so we don't need the traitlet
        # and callable optimizations
        ephem = self.ephemerides.get(ephem_component, {})
        t0 = ephem.get('t0', _default_t0)
        period = ephem.get('period', _default_period)
        dpdt = ephem.get('dpdt', _default_dpdt)

        if dpdt != 0:
            return t0 + period/dpdt*(np.exp(dpdt*(phases))-1.0)
        else:
            return t0 + (phases)*period

    def _update_all_phase_arrays(self, *args, ephem_component=None):
        # `ephem_component` is the name given to the
        # *ephemeris* component in the orbiting system, e.g. "default",
        # rather than the glue Data Component ID:

        if ephem_component is None:
            for ephem_component in self.component.choices:
                self._update_all_phase_arrays(ephem_component=ephem_component)
            return

        dc = self.app.data_collection

        phase_comp_lbl = self._phase_comp_lbl(ephem_component)

        # we'll create the callable function for this component once so it can be re-used
        _times_to_phases = self._times_to_phases_callable(ephem_component)

        new_links = []
        for i, data in enumerate(dc):
            data_is_folded = '_LCVIZ_EPHEMERIS' in data.meta.keys()
            if data_is_folded:
                continue

            times = data.get_component('World 0').data
            phases = _times_to_phases(times)

            self.app._jdaviz_helper._set_data_component(
                data, phase_comp_lbl, phases
            )

            if i != 0:
                ref_data = dc[0]
                new_link = LinkSame(
                    cid1=ref_data.world_component_ids[0],
                    cid2=data.world_component_ids[0],
                    data1=ref_data,
                    data2=data,
                    labels1=ref_data.label,
                    labels2=data.label
                )

                new_links.append(new_link)

        dc.add_link(new_links)

        # update any plugin markers
        for viewer in self._get_phase_viewers(ephem_component):
            for mark in viewer.custom_marks:
                if hasattr(mark, 'update_phase_folding'):
                    mark.update_phase_folding()

        return phase_comp_lbl

    def create_phase_viewer(self, ephem_component=None):
        """
        Create a new phase viewer corresponding to ``component`` and populate the phase arrays
        with the current ephemeris, if necessary.

        Parameters
        ----------
        ephem_component : str, optional
            label of the component.  If not provided or ``None``, will default to plugin value.
        """
        if ephem_component is None:
            ephem_component = self.component_selected
        phase_comp_lbl = self._phase_comp_lbl(ephem_component)
        dc = self.app.data_collection

        # check to see if this component already has a phase array.  We'll just check the first
        # item in the data-collection since the rest of the logic in this plugin /should/ populate
        # the arrays across all entries.
        if phase_comp_lbl not in [comp.label for comp in dc[0].components]:
            self.update_ephemeris()  # calls _update_all_phase_arrays

        phase_viewer_id = self._generate_phase_viewer_id(ephem_component)
        # TODO: stack horizontally by default?
        self.app._on_new_viewer(NewViewerMessage(PhaseScatterView, data=None, sender=self.app),
                                vid=phase_viewer_id, name=phase_viewer_id,
                                open_data_menu_if_empty=False)

        # access new viewer, set bookkeeping for ephemeris component
        pv = self.app.get_viewer(phase_viewer_id)
        pv._ephemeris_component = ephem_component
        # since we couldn't set ephemeris_component right away, _check_if_phase_viewer_exists
        # might be out-of-date
        self._check_if_phase_viewer_exists()

        # set default data visibility
        time_viewer_item = self.app._get_viewer_item(self.app._jdaviz_helper.default_time_viewer._obj.reference)  # noqa
        for data in dc:
            if data.ndim > 1:
                # skip image/cube entries
                continue
            data_id = self.app._data_id_from_label(data.label)
            visible = time_viewer_item['selected_data_items'].get(data_id, 'hidden')
            self.app.set_data_visibility(phase_viewer_id, data.label, visible == 'visible')

        # set x_att
        phase_comp = self.app._jdaviz_helper._component_ids[phase_comp_lbl]
        pv.state.x_att = phase_comp

        # set viewer limits
        pv.state.x_min, pv.state.x_max = (self.wrap_at-1, self.wrap_at)

        return pv.user_api

    def vue_create_phase_viewer(self, *args):
        if not self.phase_viewer_exists:
            self.create_phase_viewer()

    def vue_period_halve(self, *args):
        self.period /= 2

    def vue_period_double(self, *args):
        self.period *= 2

    def _check_if_phase_viewer_exists(self, *args):
        self.phase_viewer_exists = len(self._get_phase_viewers()) > 0

    def _validate_component(self, lbl):
        if '[' in lbl or ']' in lbl:
            return 'cannot contain square brackets'
        if ':' in lbl:
            return 'cannot contain colon'
        return ''

    def _on_component_add(self, lbl):
        self.hub.broadcast(EphemerisComponentChangedMessage(old_lbl=None, new_lbl=lbl,
                                                            sender=self))

    def _on_component_rename(self, old_lbl, new_lbl):
        # this is triggered when the plugin component detects a change to the component name
        self._ephemerides[new_lbl] = self._ephemerides.pop(old_lbl, {})
        for viewer in self._get_phase_viewers(old_lbl):
            self.app._update_viewer_reference_name(
                viewer._ref_or_id,
                viewer._ref_or_id.replace(old_lbl, new_lbl),
                update_id=True
            )
            viewer._ephemeris_component = new_lbl

        # update metadata entries so that they can be used for filtering applicable entries in
        # data menus
        for dc_item in self.app.data_collection:
            if dc_item.meta.get('_LCVIZ_EPHEMERIS', {}).get('ephemeris', None) == old_lbl:
                dc_item.meta['_LCVIZ_EPHEMERIS']['ephemeris'] = new_lbl
        for data_item in self.app.state.data_items:
            if data_item.get('meta', {}).get('_LCVIZ_EPHEMERIS', {}).get('ephemeris', None) == old_lbl:  # noqa
                data_item['meta']['_LCVIZ_EPHEMERIS']['ephemeris'] = new_lbl

        self._check_if_phase_viewer_exists()
        self.hub.broadcast(EphemerisComponentChangedMessage(old_lbl=old_lbl, new_lbl=new_lbl,
                                                            sender=self))

    def _on_component_remove(self, lbl):
        _ = self._ephemerides.pop(lbl, {})
        # remove the corresponding viewer(s), if any exist
        for viewer in self._get_phase_viewers(lbl):
            self.app.vue_destroy_viewer_item(viewer._ref_or_id)
        self.hub.broadcast(EphemerisComponentChangedMessage(old_lbl=lbl, new_lbl=None,
                                                            sender=self))

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
        self.wrap_at = ephem.get('wrap_at', self.wrap_at)

        # if this is a new component, update those default values back to the dictionary
        self.update_ephemeris(t0=self.t0, period=self.period, dpdt=self.dpdt, wrap_at=self.wrap_at)
        self._ignore_ephem_change = False
        if ephem:
            # if there were any changes applied by accessing the dictionary,
            # then we need to update phasing, etc (since we set _ignore_ephem_change)
            # otherwise, this is a new component and there is no need.
            self._ephem_traitlet_changed()

    def update_ephemeris(self, ephem_component=None, t0=None, period=None, dpdt=None, wrap_at=None):
        """
        Update the ephemeris for a given component.

        Parameters
        ----------
        ephem_component : str, optional
            label of the component.  If not provided or ``None``, will default to plugin value.
        t0 : float, optional
            value of t0 to replace
        period : float, optional
            value of period to replace
        dpdt : float, optional
            value of dpdt to replace
        wrap_at : float, optional
            value of wrap_at to replace

        Returns
        -------
        dictionary of ephemeris corresponding to ``component``
        """
        if ephem_component is None:
            ephem_component = self.component_selected

        if ephem_component not in self.component.choices:  # pragma: no cover
            raise ValueError(f"component must be one of {self.component.choices}")

        existing_ephem = self._ephemerides.get(ephem_component, {})
        for name, value in {'t0': t0, 'period': period, 'dpdt': dpdt, 'wrap_at': wrap_at}.items():
            if value is not None:
                existing_ephem[name] = value
                if ephem_component == self.component_selected:
                    setattr(self, name, value)

        self._ephemerides[ephem_component] = existing_ephem
        self._update_all_phase_arrays(ephem_component=ephem_component)
        self.hub.broadcast(EphemerisChangedMessage(ephemeris_label=ephem_component,
                                                   sender=self))
        return existing_ephem

    @observe('period', 'dpdt', 't0', 'wrap_at')
    def _ephem_traitlet_changed(self, event={}):
        if self._ignore_ephem_change:
            return
        for value in (self.period, self.dpdt, self.t0, self.wrap_at):
            if not isinstance(value, (int, float)):
                return
        if self.period <= 0:
            return

        def round_to_1(x):
            return round(x, -int(np.floor(np.log10(abs(x)))))

        # if phase-viewer doesn't yet exist in the app, create it now
        if not self.phase_viewer_exists:
            self.create_phase_viewer()

        # update value in the dictionary (to support multi-ephems)
        if event:
            self.update_ephemeris(**{event.get('name'): event.get('new')})
            # will call _update_all_phase_arrays
        else:
            self._update_all_phase_arrays(ephem_component=self.component_selected)

        # update zoom-limits if wrap_at was changed
        if event.get('name') == 'wrap_at':
            old = event.get('old') if event.get('old') != '' else self._prev_wrap_at
            if event.get('new') != '':
                delta_phase = event.get('new') - old
                for pv in self._get_phase_viewers():
                    pvs = pv.state
                    pvs.x_min, pvs.x_max = pvs.x_min + delta_phase, pvs.x_max + delta_phase
                # we need to cache the old value since it could become a string
                # if the widget is cleared
                self._prev_wrap_at = event.get('new')

        # update step-sizes
        self.period_step = round_to_1(self.period/5000)
        self.dpdt_step = max(round_to_1(abs(self.period * self.dpdt)/1000) if self.dpdt != 0 else 0,
                             1./1000000)
        self.t0_step = round_to_1(self.period/1000)

        if not self._default_initialized:
            # other plugins that use EphemerisSelect don't see the first entry yet
            self._default_initialized = True
            self._on_component_add(self.component_selected)

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
        else:  # pragma: no cover
            self.method_spinner = False
            raise NotImplementedError(f"periodogram not implemented for {self.method}")

        # TODO: will need to return in display units once supported
        self.period_at_max_power = per.period_at_max_power.value
        self.method_spinner = False

    def adopt_period_at_max_power(self):
        self.period = self.period_at_max_power

    def vue_adopt_period_at_max_power(self, *args):
        self.adopt_period_at_max_power()

    def get_data(self, dataset, ephem_component=None):
        # TODO: support subset_to_apply and then include a wrapper at the helper-level?
        # (would need to catch when cls does not result in a lightkurve object or write
        # behaviors for other cases as well)
        if ephem_component is None:
            ephem_component = self.component.selected

        lc = self.app._jdaviz_helper.get_data(dataset)
        data = next((x for x in self.app.data_collection if x.label == dataset))

        comps = {str(comp): comp for comp in data.components}
        xcomp = f'phase:{ephem_component}'
        phases = data.get_component(comps.get(xcomp)).data

        # the following code is adopted directly from lightkurve
        # 2. Create the folded object
        phlc = FoldedLightCurve(data=lc)
        # 3. Restore the folded time
        with phlc._delay_required_column_checks():
            phlc.remove_column("time")
            # TODO: phased lc shouldn't have the same time format/scale, but this is needed
            # in order for binning to work (until there's a fix to lightkurve)
            phlc.add_column(Time(phases, format=lc.time.format, scale=lc.time.scale),
                            name="time", index=0)
            phlc.add_column(lc.time.copy(), name="time_original", index=len(lc._required_columns))

        # Add extra column and meta data specific to FoldedLightCurve
        ephemeris = self.ephemerides.get(ephem_component)
        phlc.meta["_LCVIZ_EPHEMERIS"] = {'ephemeris': ephem_component, **ephemeris}
        phlc.meta["PERIOD"] = ephemeris.get('period')
        phlc.meta["EPOCH_TIME"] = ephemeris.get('t0')
        phlc.sort("time")

        return phlc
