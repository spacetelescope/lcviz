import numpy as np

from traitlets import Bool, Unicode, observe

from jdaviz.core.custom_traitlets import FloatHandleEmpty, IntHandleEmpty
from jdaviz.core.events import ViewerAddedMessage
from jdaviz.core.registries import tray_registry
from jdaviz.core.template_mixin import (PluginTemplateMixin,
                                        DatasetSelectMixin, AddResultsMixin)
from jdaviz.core.user_api import PluginUserApi

from lcviz.marks import LivePreviewTrend, LivePreviewFlattened
from lcviz.utils import data_not_folded
from lcviz.viewers import TimeScatterView, PhaseScatterView
from lcviz.parsers import _data_with_reftime

__all__ = ['Flatten']


@tray_registry('flatten', label="Flatten")
class Flatten(PluginTemplateMixin, DatasetSelectMixin, AddResultsMixin):
    """
    See the :ref:`Flatten Plugin Documentation <flatten>` for more details.

    Only the following attributes and methods are available through the
    public plugin API.

    * ``show_live_preview``
    * ``default_to_overwrite``
    * ``dataset`` (:class:`~jdaviz.core.template_mixin.DatasetSelect`):
      Dataset to flatten.
    * ``add_results`` (:class:`~jdaviz.core.template_mixin.AddResults`)
    * ``window_length``
    * ``polyorder``
    * ``break_tolerance``
    * ``niters``
    * ``sigma``
    * ``unnormalize``
    * :meth:`flatten`
    """
    template_file = __file__, "flatten.vue"
    uses_active_status = Bool(True).tag(sync=True)

    show_live_preview = Bool(True).tag(sync=True)
    default_to_overwrite = Bool(True).tag(sync=True)
    flatten_err = Unicode().tag(sync=True)

    window_length = IntHandleEmpty(101).tag(sync=True)
    polyorder = IntHandleEmpty(2).tag(sync=True)
    break_tolerance = IntHandleEmpty(5).tag(sync=True)
    niters = IntHandleEmpty(3).tag(sync=True)
    sigma = FloatHandleEmpty(3).tag(sync=True)
    unnormalize = Bool(False).tag(sync=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # do not support flattening data in phase-space
        self.dataset.add_filter(data_not_folded)

        # marks do not exist for the new viewer, so force another update to compute and draw
        # those marks
        self.hub.subscribe(self, ViewerAddedMessage, handler=lambda _: self._live_update())

    @property
    def user_api(self):
        expose = ['show_live_preview', 'default_to_overwrite',
                  'dataset', 'add_results',
                  'window_length', 'polyorder', 'break_tolerance',
                  'niters', 'sigma', 'unnormalize', 'flatten']
        return PluginUserApi(self, expose=expose)

    @property
    def marks(self):
        trend_marks = {}
        flattened_marks = {}

        for id, viewer in self.app._viewer_store.items():
            needs_trend = isinstance(viewer, TimeScatterView) and not isinstance(viewer, PhaseScatterView)  # noqa
            needs_flattened = isinstance(viewer, (TimeScatterView, PhaseScatterView))
            for mark in viewer.figure.marks:
                if isinstance(mark, LivePreviewTrend):
                    trend_marks[id] = mark
                    needs_trend = False
                elif isinstance(mark, LivePreviewFlattened):
                    flattened_marks[id] = mark
                    needs_flattened = False
                if not needs_trend and not needs_flattened:
                    break
            if needs_trend:
                mark = LivePreviewTrend(viewer, visible=self.is_active)
                viewer.figure.marks = viewer.figure.marks + [mark]
                trend_marks[id] = mark
            if needs_flattened:
                mark = LivePreviewFlattened(viewer, visible=self.is_active)
                viewer.figure.marks = viewer.figure.marks + [mark]
                flattened_marks[id] = mark

        return trend_marks, flattened_marks

    @observe('default_to_overwrite', 'dataset_selected')
    def _set_default_results_label(self, event={}):
        '''Generate a label and set the results field to that value'''
        if not hasattr(self, 'dataset'):  # pragma: no cover
            return

        self.add_results.label_whitelist_overwrite = [self.dataset_selected]

        if self.default_to_overwrite:
            self.results_label_default = self.dataset_selected
        else:
            self.results_label_default = f"{self.dataset_selected} (flattened)"

    def flatten(self, add_data=True):
        """
        Flatten the input light curve (``dataset``) using lightkurve.flatten.

        Parameters
        ----------
        add_data : bool
            Whether to add the resulting trace to the application, according to the options
            defined in the plugin.

        Returns
        -------
        output_lc : `~lightkurve.LightCurve`
            The flattened light curve.
        trend_lc : `~lightkurve.LightCurve`
            The trend used to flatten the light curve.
        """
        input_lc = self.dataset.selected_obj
        if input_lc is None:  # pragma: no cover
            raise ValueError("no input dataset selected")

        output_lc, trend_lc = input_lc.flatten(return_trend=True,
                                               window_length=self.window_length,
                                               polyorder=self.polyorder,
                                               break_tolerance=self.break_tolerance,
                                               niters=self.niters,
                                               sigma=self.sigma)

        if self.unnormalize:
            factor = np.nanmedian(trend_lc.flux.value)
            output_lc.flux *= factor
            output_lc.flux_err *= factor
            output_lc.meta['NORMALIZED'] = False

        if add_data:
            # add data to the collection/viewer
            data = _data_with_reftime(self.app, output_lc)
            self.add_results.add_results_from_plugin(data)

        return output_lc, trend_lc

    def _clear_marks(self):
        for mark_set in self.marks:
            for mark in mark_set.values():
                if mark.visible:
                    mark.clear()
                    mark.visible = False

    @observe('show_live_preview', 'is_active',
             'dataset_selected',
             'window_length', 'polyorder', 'break_tolerance',
             'niters', 'sigma')
    def _live_update(self, event={}):
        if not self.show_live_preview or not self.is_active:
            self._clear_marks()
            self.flatten_err = ''
            return

        try:
            output_lc, trend_lc = self.flatten(add_data=False)
        except Exception as e:
            self.flatten_err = str(e)
            self._clear_marks()
            return
        self.flatten_err = ''

        if self.unnormalize:
            output_flux = output_lc.flux.value
        else:
            output_flux = output_lc.flux.value * np.nanmedian(trend_lc.flux.value)

        ref_time = trend_lc.meta.get('reference_time', 0)
        times = trend_lc.time - ref_time
        trend_marks, flattened_marks = self.marks
        for mark in trend_marks.values():
            # TODO: need to account for phasing
            mark.update_ty(times.value, trend_lc.flux.value)
            mark.visible = True
        for mark in flattened_marks.values():
            mark.update_ty(times.value, output_flux)
            mark.visible = True

    def vue_apply(self, *args, **kwargs):
        try:
            self.flatten(add_data=True)
        except Exception as e:
            self.flatten_err = str(e)
        else:
            self.flatten_err = ''
        if self.add_results.label_overwrite:
            # then this will change the input data without triggering a
            # change to dataset_selected
            self._live_update()
