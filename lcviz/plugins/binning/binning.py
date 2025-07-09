from astropy.time import Time
from traitlets import Bool, observe
from glue.config import data_translator

from jdaviz.core.custom_traitlets import IntHandleEmpty
from jdaviz.core.events import (ViewerAddedMessage, ViewerRemovedMessage)
from jdaviz.core.registries import tray_registry
from jdaviz.core.template_mixin import (PluginTemplateMixin,
                                        DatasetSelectMixin, AddResultsMixin,
                                        skip_if_no_updates_since_last_active,
                                        with_spinner, with_temp_disable)
from jdaviz.core.user_api import PluginUserApi

from lcviz.components import FluxColumnSelectMixin
from lcviz.events import EphemerisChangedMessage
from lcviz.marks import LivePreviewBinning
from lcviz.parsers import _data_with_reftime
from lcviz.viewers import TimeScatterView, PhaseScatterView
from lcviz.components import EphemerisSelectMixin
from lcviz.utils import is_not_tpf


__all__ = ['Binning']


@tray_registry('binning', label="Binning")
class Binning(PluginTemplateMixin, FluxColumnSelectMixin, DatasetSelectMixin,
              EphemerisSelectMixin, AddResultsMixin):
    """
    See the :ref:`Binning Plugin Documentation <binning>` for more details.

    Only the following attributes and methods are available through the
    :ref:`public plugin API <plugin-apis>`:

    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.show`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.open_in_tray`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.close_in_tray`
    * ``dataset`` (:class:`~jdaviz.core.template_mixin.DatasetSelect`):
      Dataset to bin.
    * ``ephemeris`` (:class:`~jdaviz.core.template_mixin.SelectPluginComponent`):
      Label of the component corresponding to the active ephemeris.
    * :meth:`input_lc`
      Data used as input to binning, based on ``dataset`` and ``ephemeris``.
    * ``n_bins`` : int
    * ``add_results`` (:class:`~jdaviz.core.template_mixin.AddResults`)
    * :meth:`bin`
    """
    template_file = __file__, "binning.vue"
    uses_active_status = Bool(True).tag(sync=True)

    show_live_preview = Bool(True).tag(sync=True)

    n_bins = IntHandleEmpty(100).tag(sync=True)
    bin_enabled = Bool(True).tag(sync=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._plugin_description = 'Bin input light curve.'

        self._set_results_viewer()

        # TODO: replace with add_filter('not_from_this_plugin') if upstream PR accepted/released
        # https://github.com/spacetelescope/jdaviz/pull/2239
        def not_from_binning_plugin(data):
            return data.meta.get('Plugin', None) != self.__class__.__name__
        self.dataset.add_filter(not_from_binning_plugin, is_not_tpf)

        # TODO: viewer added also needs to repopulate marks
        self.hub.subscribe(self, ViewerAddedMessage, handler=self._on_add_viewer)
        self.hub.subscribe(self, ViewerRemovedMessage, handler=self._set_results_viewer)
        self.hub.subscribe(self, EphemerisChangedMessage, handler=self._on_ephemeris_update)

    @property
    def user_api(self):
        expose = ['show_live_preview', 'dataset', 'ephemeris', 'input_lc',
                  'n_bins', 'add_results', 'bin']
        return PluginUserApi(self, expose=expose)

    @property
    def ephemeris_plugin(self):
        return self.ephemeris.ephemeris_plugin

    @property
    def ephemeris_dict(self):
        if self.ephemeris_selected == 'No ephemeris':
            return {}
        return self.ephemeris_plugin.ephemerides.get(self.ephemeris_selected)

    @property
    def input_lc(self):
        return self.ephemeris.get_data_for_dataset(self.dataset)

    @property
    def marks(self):
        marks = {}
        for viewer in self.app._viewer_store.values():
            for mark in viewer.figure.marks:
                if isinstance(mark, LivePreviewBinning):
                    marks[viewer.reference] = mark
                    break
            else:
                mark = LivePreviewBinning(viewer, visible=self.is_active)
                viewer.figure.marks = viewer.figure.marks + [mark]
                marks[viewer.reference] = mark
        return marks

    def _clear_marks(self):
        for mark in self.marks.values():
            if mark.visible:
                mark.clear()
                mark.visible = False

    @observe("dataset_selected", "ephemeris_selected")
    def _set_default_results_label(self, event={}):
        '''Generate a label and set the results field to that value'''
        if not hasattr(self, 'ephemeris'):
            return
        label = f"binned {self.dataset_selected}"
        if self.ephemeris_selected not in self.ephemeris._manual_options:
            label += f":{self.ephemeris_selected}"
        self.results_label_default = label

    @observe("ephemeris_selected")
    def _set_results_viewer(self, event={}):
        if not hasattr(self, 'ephemeris'):
            return

        def viewer_filter(viewer):
            if self.ephemeris_selected in self.ephemeris._manual_options:
                return isinstance(viewer, TimeScatterView)
            if not isinstance(viewer, PhaseScatterView):
                # ephemeris selected, but no active phase viewers
                return False
            return viewer._ephemeris_component == self.ephemeris_selected

        self.add_results.viewer.filters = [viewer_filter]

    def _on_add_viewer(self, msg):
        self._set_results_viewer()
        self._live_update()

    @observe('is_active', 'show_live_preview')
    def _toggle_marks(self, event={}):
        visible = self.show_live_preview and self.is_active

        for viewer_ref, mark in self.marks.items():
            if not visible:
                this_visible = False
            elif self.ephemeris_selected == 'No ephemeris':
                this_visible = True
            else:
                viewer = self.app.get_viewer(viewer_ref)
                viewer_ephem = getattr(viewer, '_ephemeris_component', None)
                this_visible = viewer_ephem == self.ephemeris_selected

            mark.visible = this_visible

        if visible and event.get('name', '') in ('is_active', 'show_live_preview'):
            # then the marks themselves need to be updated
            self._live_update(event)

    @observe('flux_column_selected', 'dataset_selected',
             'ephemeris_selected',
             'n_bins', 'previews_temp_disabled')
    @skip_if_no_updates_since_last_active()
    @with_temp_disable(timeout=0.3)
    def _live_update(self, event={}):
        self.bin_enabled = self.n_bins != '' and self.n_bins > 0

        if not self.show_live_preview or not self.is_active or not self.bin_enabled:
            self._clear_marks()
            return

        if event.get('name', '') not in ('is_active', 'show_live_preview'):
            # mark visibility hasn't been handled yet
            self._toggle_marks()

        try:
            lc = self.bin(add_data=False)
        except Exception:
            self._clear_marks()
            self.bin_enabled = False
            return
        else:
            self.bin_enabled = True

        # TODO: remove the need for this (inconsistent quantity vs value setting in lc object)
        lc_time = getattr(lc.time, 'value', lc.time)

        if self.ephemeris_selected == 'No ephemeris':
            ref_time = lc.meta.get('reference_time', 0)
            ref_time = getattr(ref_time, 'value', ref_time)
            times = lc_time - ref_time
        else:
            times = lc_time

        for viewer_id, mark in self.marks.items():
            if self.ephemeris_selected == 'No ephemeris':
                # TODO: fix this to be general and not rely on ugly id
                do_phase = viewer_id != 'lcviz-0'
            else:
                do_phase = False

            if do_phase:
                mark.update_ty(times, lc.flux.value)
            else:
                mark.times = []
                mark.update_xy(times, lc.flux.value)

    def _on_ephemeris_update(self, msg):
        if not self.show_live_preview or not self.is_active:
            return

        if msg.ephemeris_label != self.ephemeris_selected:
            return

        self._live_update()

    @with_spinner()
    def bin(self, add_data=True):
        if self.n_bins == '' or self.n_bins <= 0:
            raise ValueError("n_bins must be a positive integer")

        input_lc = self.input_lc

        # fix for bug in py310, see:
        # https://github.com/spacetelescope/lcviz/pull/194
        if "NORMALIZE_PHASE" not in input_lc.meta:
            input_lc.meta["NORMALIZE_PHASE"] = False

        lc = input_lc.bin(time_bin_size=(input_lc.time[-1]-input_lc.time[0]).value/self.n_bins)
        if self.ephemeris_selected != 'No ephemeris':
            # lc.time.value are actually phases, so convert to times starting at time t0
            times = self.ephemeris_plugin.phases_to_times(lc.time.value, self.ephemeris_selected)

            # set the time_original column, leaving the time column as phases
            time_col = Time(times,
                            format=input_lc.time_original.format,
                            scale=input_lc.time_original.scale)
            lc.add_column(time_col, name="time_original", index=len(lc._required_columns))

            lc.meta.update({'_LCVIZ_BINNED': True})

            # convert to glue Data manually, so we may edit the `phase` component:
            handler, _ = data_translator.get_handler_for(lc)
            data = handler.to_data(lc)
            phase_comp_lbl = self.app._jdaviz_helper._phase_comp_lbl(self.ephemeris_selected)

            # here we use the `value` attribute of `lc.time`, which has units of *phase*:
            self.app._jdaviz_helper._set_data_component(data, phase_comp_lbl, lc.time.value)

        else:
            # need to send through parser-logic to assign the correct reference time
            data = _data_with_reftime(self.app, lc)

        if add_data:
            # add data to the collection/viewer
            # NOTE: lc will have _LCVIZ_EPHEMERIS set if phase-folded
            self._set_results_viewer()
            self.add_results.add_results_from_plugin(data or lc)

            if self.ephemeris_selected != 'No ephemeris':
                # prevent phase axis from becoming a time axis:
                ephemeris_plugin = self.app._jdaviz_helper.plugins['Ephemeris']
                phase_comp_lbl = self.app._jdaviz_helper._phase_comp_lbl(self.ephemeris_selected)
                phase_comp = self.app._jdaviz_helper._component_ids[phase_comp_lbl]
                for pv in ephemeris_plugin._obj._get_phase_viewers(self.ephemeris_selected):
                    pv.state.x_att = phase_comp
                # by resetting x_att, the preview marks may have dissappeared
                self._live_update()

        return lc

    def vue_apply(self, event={}):
        self.bin(add_data=True)
