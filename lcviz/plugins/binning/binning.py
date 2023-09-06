from astropy.time import Time
from traitlets import Bool, observe
from glue.config import data_translator

from jdaviz.core.custom_traitlets import IntHandleEmpty
from jdaviz.core.events import (ViewerAddedMessage, ViewerRemovedMessage)
from jdaviz.core.registries import tray_registry
from jdaviz.core.template_mixin import (PluginTemplateMixin,
                                        DatasetSelectMixin, AddResultsMixin)
from jdaviz.core.user_api import PluginUserApi

from lcviz.events import EphemerisChangedMessage
from lcviz.helper import _default_time_viewer_reference_name
from lcviz.marks import LivePreviewBinning
from lcviz.template_mixin import EphemerisSelectMixin


__all__ = ['Binning']


@tray_registry('binning', label="Binning")
class Binning(PluginTemplateMixin, DatasetSelectMixin, EphemerisSelectMixin, AddResultsMixin):
    """
    See the :ref:`Binning Plugin Documentation <binning>` for more details.

    Only the following attributes and methods are available through the
    public plugin API.

    * ``dataset`` (:class:`~jdaviz.core.template_mixin.DatasetSelect`):
      Dataset to bin.
    * ``ephemeris`` (:class:`~jdaviz.core.template_mixin.SelectPluginComponent`):
      Label of the component corresponding to the active ephemeris.
    * :meth:`input_lc`
      Data used as input to binning, based on ``dataset`` and ``ephemeris``.
    * ``n_bins``
    * ``add_results`` (:class:`~jdaviz.core.template_mixin.AddResults`)
    * :meth:`bin`
    """
    template_file = __file__, "binning.vue"
    uses_active_status = Bool(True).tag(sync=True)

    show_live_preview = Bool(True).tag(sync=True)

    n_bins = IntHandleEmpty(100).tag(sync=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._set_results_viewer()

        # TODO: replace with add_filter('not_from_this_plugin') if upstream PR accepted/released
        # https://github.com/spacetelescope/jdaviz/pull/2239
        def not_from_binning_plugin(data):
            return data.meta.get('Plugin', None) != self.__class__.__name__
        self.dataset.add_filter(not_from_binning_plugin)

        self.hub.subscribe(self, ViewerAddedMessage, handler=self._set_results_viewer)
        self.hub.subscribe(self, ViewerRemovedMessage, handler=self._set_results_viewer)
        self.hub.subscribe(self, EphemerisChangedMessage, handler=self._on_ephemeris_update)

    @property
    def user_api(self):
        expose = ['dataset', 'ephemeris', 'input_lc',
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
        for id, viewer in self.app._viewer_store.items():
            for mark in viewer.figure.marks:
                if isinstance(mark, LivePreviewBinning):
                    marks[id] = mark
                    break
            else:
                mark = LivePreviewBinning(viewer, visible=self.is_active)
                viewer.figure.marks = viewer.figure.marks + [mark]
                marks[id] = mark
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
                return viewer.reference == _default_time_viewer_reference_name
            if 'flux-vs-phase:' not in viewer.reference:
                # ephemeris selected, but no active phase viewers
                return False
            return viewer.reference.split('flux-vs-phase:')[1] == self.ephemeris_selected

        self.add_results.viewer.filters = [viewer_filter]

    @observe('show_live_preview', 'is_active',
             'dataset_selected', 'ephemeris_selected',
             'n_bins')
    def _live_update(self, event={}):
        if not self.show_live_preview or not self.is_active:
            self._clear_marks()
            return

        lc = self.bin(add_data=False)
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
                visible = True
                # TODO: fix this to be general and not rely on ugly id
                do_phase = viewer_id != 'lcviz-0'
            else:
                # TODO: try to fix flashing as traitlets update
                visible = viewer_id.split(':')[-1] == self.ephemeris_selected
                do_phase = False

            if visible:
                if do_phase:
                    mark.update_ty(times, lc.flux.value)
                else:
                    mark.times = []
                    mark.update_xy(times, lc.flux.value)
            else:
                mark.clear()
            mark.visible = visible

    def _on_ephemeris_update(self, msg):
        if not self.show_live_preview or not self.is_active:
            return

        if msg.ephemeris_label != self.ephemeris_selected:
            return

        self._live_update()

    def bin(self, add_data=True):
        input_lc = self.input_lc

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
            data = None

        if add_data:
            # add data to the collection/viewer
            # NOTE: lc will have _LCVIZ_EPHEMERIS set if phase-folded
            self._set_results_viewer()
            self.add_results.add_results_from_plugin(data or lc)

            if self.ephemeris_selected != 'No ephemeris':
                # prevent phase axis from becoming a time axis:
                viewer_id = self.ephemeris_plugin._obj.phase_viewer_id
                pv = self.app.get_viewer(viewer_id)
                phase_comp_lbl = self.app._jdaviz_helper._phase_comp_lbl(self.ephemeris_selected)
                pv.state.x_att = self.app._jdaviz_helper._component_ids[phase_comp_lbl]

        return lc

    def vue_apply(self, event={}):
        self.bin(add_data=True)
