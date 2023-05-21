import numpy as np

from traitlets import Bool, List, Unicode, observe

from jdaviz.core.custom_traitlets import FloatHandleEmpty, IntHandleEmpty
from jdaviz.core.registries import tray_registry
from jdaviz.core.template_mixin import (PluginTemplateMixin, SelectPluginComponent,
                                        DatasetSelectMixin, AddResultsMixin)
from jdaviz.core.user_api import PluginUserApi

from lcviz.marks import LivePreviewTrend, LivePreviewDetrended


__all__ = ['Detrending']


@tray_registry('detrending', label="Detrending")
class Detrending(PluginTemplateMixin, DatasetSelectMixin, AddResultsMixin):
    """
    See the :ref:`Detrending Plugin Documentation <detrending>` for more details.

    Only the following attributes and methods are available through the
    public plugin API.

    * ``show_live_preview``
    * ``default_to_overwrite``
    * ``dataset`` (:class:`~jdaviz.core.template_mixin.DatasetSelect`):
      Dataset to detrend.
    * ``method`` (:class:`~jdaviz.core.template_mixing.SelectPluginComponent`):
      Method/algorithm.
    * ``add_results`` (:class:`~jdaviz.core.template_mixin.AddResults`)
    """
    template_file = __file__, "detrending.vue"

    show_live_preview = Bool(True).tag(sync=True)
    default_to_overwrite = Bool(True).tag(sync=True)
    detrend_err = Unicode().tag(sync=True)

    method_items = List().tag(sync=True)
    method_selected = Unicode().tag(sync=True)

    # TODO: concept of "sub-plugin" where exposed args change based on method
    flatten_window_length = IntHandleEmpty(101).tag(sync=True)
    flatten_polyorder = IntHandleEmpty(2).tag(sync=True)
    flatten_break_tolerance = IntHandleEmpty(5).tag(sync=True)
    flatten_niters = IntHandleEmpty(3).tag(sync=True)
    flatten_sigma = FloatHandleEmpty(3).tag(sync=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.method = SelectPluginComponent(self,
                                            items='method_items',
                                            selected='method_selected',
                                            manual_options=['flatten'])

    @property
    def user_api(self):
        expose = ['show_live_preview', 'default_to_overwrite',
                  'dataset', 'method', 'detrend']
        return PluginUserApi(self, expose=expose)

    @property
    def marks(self):
        trend_marks = {}
        detrended_marks = {}

        for id, viewer in self.app._viewer_store.items():
            has_trend, has_detrended = False, False
            for mark in viewer.figure.marks:
                if isinstance(mark, LivePreviewTrend):
                    trend_marks[id] = mark
                    has_trend = True
                elif isinstance(mark, LivePreviewDetrended):
                    detrended_marks[id] = mark
                    has_detrended = True
                if has_trend and has_detrended:
                    break
            if not has_trend:
                mark = LivePreviewTrend(viewer, visible=self.plugin_opened)
                viewer.figure.marks = viewer.figure.marks + [mark]
                trend_marks[id] = mark
            if not has_detrended:
                mark = LivePreviewDetrended(viewer, visible=self.plugin_opened)
                viewer.figure.marks = viewer.figure.marks + [mark]
                detrended_marks[id] = mark

        return trend_marks, detrended_marks

    @observe('default_to_overwrite', 'dataset_selected', 'method_selected')
    def _set_default_results_label(self, event={}):
        '''Generate a label and set the results field to that value'''
        if not hasattr(self, 'dataset'):
            return

        self.add_results.label_whitelist_overwrite = [self.dataset_selected]

        if self.default_to_overwrite:
            self.results_label_default = self.dataset_selected
        else:
            self.results_label_default = f"{self.method_selected} {self.dataset_selected}"

    def detrend(self, add_data=True):
        input_lc = self.dataset.selected_obj

        if self.method_selected == 'flatten':
            output_lc, trend_lc = input_lc.flatten(return_trend=True,
                                                   window_length=self.flatten_window_length,
                                                   polyorder=self.flatten_polyorder,
                                                   break_tolerance=self.flatten_break_tolerance,
                                                   niters=self.flatten_niters,
                                                   sigma=self.flatten_sigma)
        else:
            raise NotImplementedError(f"not implemented for method='{self.method_selected}'")

        if add_data:
            # add data to the collection/viewer
            self.add_results.add_results_from_plugin(output_lc)

        return output_lc, trend_lc

    def _clear_marks(self):
        for mark_set in self.marks:
            for mark in mark_set.values():
                if mark.visible:
                    mark.clear()
                    mark.visible = False

    @observe('show_live_preview', 'plugin_opened', 'method_selected',
             'flatten_window_length', 'flatten_polyorder', 'flatten_break_tolerance',
             'flatten_niters', 'flatten_sigma')
    def _live_update(self, event={}):
        if not self.show_live_preview or not self.plugin_opened:
            self._clear_marks()
            self.detrend_err = ''
            return

        input_lc = self.dataset.selected_obj
        try:
            output_lc, trend_lc = self.detrend(add_data=False)
        except Exception as e:
            self.detrend_err = str(e)
            self._clear_marks()
            return
        self.detrend_err = ''

        ref_time = trend_lc.meta.get('reference_time', 0)
        times = trend_lc.time - ref_time
        trend_marks, detrended_marks = self.marks
        for mark in trend_marks.values():
            # TODO: need to account for phasing
            mark.update_xy(times.value, trend_lc.flux.value)
            mark.visible = True
        for mark in detrended_marks.values():
            mark.update_xy(times.value, output_lc.flux.value * np.nanmedian(input_lc.flux.value))
            mark.visible = True

    def vue_apply(self, *args, **kwargs):
        try:
            self.detrend(add_data=True)
        except Exception as e:
            self.detrend_err = str(e)
        else:
            self.detrend_err = ''
