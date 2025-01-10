import numpy as np

from traitlets import Bool, Unicode, observe

from jdaviz.core.custom_traitlets import FloatHandleEmpty, IntHandleEmpty
from jdaviz.core.events import ViewerAddedMessage
from jdaviz.core.registries import tray_registry
from jdaviz.core.template_mixin import (PluginTemplateMixin,
                                        DatasetSelectMixin,
                                        AutoTextField,
                                        skip_if_no_updates_since_last_active,
                                        with_spinner, with_temp_disable)
from jdaviz.core.user_api import PluginUserApi

from lcviz.components import FluxColumnSelectMixin
from lcviz.marks import LivePreviewTrend, LivePreviewFlattened
from lcviz.utils import data_not_folded, is_not_tpf
from lcviz.viewers import TimeScatterView, PhaseScatterView
from lcviz.parsers import _data_with_reftime

__all__ = ['Flatten']


@tray_registry('flatten', label="Flatten")
class Flatten(PluginTemplateMixin, FluxColumnSelectMixin, DatasetSelectMixin):
    """
    See the :ref:`Flatten Plugin Documentation <flatten>` for more details.

    Only the following attributes and methods are available through the
    :ref:`public plugin API <plugin-apis>`:

    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.show`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.open_in_tray`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.close_in_tray`
    * ``show_live_preview`` : bool
        Whether to show the live-preview of the (unnormalized) flattened light curve
    * ``show_trend_preview`` : bool
        Whether to show the live-preview of the trend curve used to flatten the light curve
    * ``dataset`` (:class:`~jdaviz.core.template_mixin.DatasetSelect`):
      Dataset to flatten.
    * ``window_length`` : int
    * ``polyorder`` : int
    * ``break_tolerance`` : int
    * ``niters`` : int
    * ``sigma`` : float
    * ``unnormalize`` : bool
    * ``flux_label`` (:class:`~jdaviz.core.template_mixin.AutoTextField`):
      Label for the resulting flux column added to ``dataset`` and automatically selected as the new
      flux column (origin).
    * :meth:`flatten`
    """
    template_file = __file__, "flatten.vue"
    uses_active_status = Bool(True).tag(sync=True)

    show_live_preview = Bool(True).tag(sync=True)
    show_trend_preview = Bool(True).tag(sync=True)
    flatten_err = Unicode().tag(sync=True)

    window_length = IntHandleEmpty(101).tag(sync=True)
    polyorder = IntHandleEmpty(2).tag(sync=True)
    break_tolerance = IntHandleEmpty(5).tag(sync=True)
    niters = IntHandleEmpty(3).tag(sync=True)
    sigma = FloatHandleEmpty(3).tag(sync=True)
    unnormalize = Bool(False).tag(sync=True)

    flux_label_label = Unicode().tag(sync=True)
    flux_label_default = Unicode().tag(sync=True)
    flux_label_auto = Bool(True).tag(sync=True)
    flux_label_invalid_msg = Unicode('').tag(sync=True)
    flux_label_overwrite = Bool(False).tag(sync=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._plugin_description = 'Flatten input light curve.'
        self.flux_label = AutoTextField(self, 'flux_label_label',
                                        'flux_label_default', 'flux_label_auto',
                                        'flux_label_invalid_msg')

        # do not support flattening data in phase-space
        # do not allow TPF as input
        self.dataset.add_filter(data_not_folded, is_not_tpf)

        # marks do not exist for the new viewer, so force another update to compute and draw
        # those marks
        self.hub.subscribe(self, ViewerAddedMessage, handler=lambda _: self._live_update())

        self._set_default_label()

    @property
    def user_api(self):
        expose = ['show_live_preview', 'show_trend_preview',
                  'dataset',
                  'window_length', 'polyorder', 'break_tolerance',
                  'niters', 'sigma', 'unnormalize', 'flux_label', 'flatten']
        return PluginUserApi(self, expose=expose)

    @property
    def marks(self):
        trend_marks = {}
        flattened_marks = {}

        for viewer in self.app._viewer_store.values():
            needs_trend = isinstance(viewer, TimeScatterView) and not isinstance(viewer, PhaseScatterView)  # noqa
            needs_flattened = isinstance(viewer, (TimeScatterView, PhaseScatterView))
            for mark in viewer.figure.marks:
                if isinstance(mark, LivePreviewTrend):
                    trend_marks[viewer.reference] = mark
                    needs_trend = False
                elif isinstance(mark, LivePreviewFlattened):
                    flattened_marks[viewer.reference] = mark
                    needs_flattened = False
                if not needs_trend and not needs_flattened:
                    break
            if needs_trend:
                mark = LivePreviewTrend(viewer, visible=self.is_active)
                viewer.figure.marks = viewer.figure.marks + [mark]
                trend_marks[viewer.reference] = mark
            if needs_flattened:
                mark = LivePreviewFlattened(viewer, visible=self.is_active)
                viewer.figure.marks = viewer.figure.marks + [mark]
                flattened_marks[viewer.reference] = mark

        return trend_marks, flattened_marks

    @observe('dataset_selected', 'flux_column_selected')
    def _set_default_label(self, event={}):
        '''Generate a label and set the results field to that value'''
        if not hasattr(self, 'dataset'):  # pragma: no cover
            return

        # TODO: have an option to create new data entry and drop other columns?
        # (or should that just go through future data cloning)
        self.flux_label.default = f"{self.flux_column_selected}_flattened"

    @observe('flux_label_label', 'dataset')
    def _update_label_valid(self, event={}):
        if self.flux_label.value in self.flux_column.choices:
            self.flux_label.invalid_msg = ''
            self.flux_label_overwrite = True
        elif self.flux_label.value in getattr(self.dataset.selected_obj, 'columns', []):
            self.flux_label.invalid_msg = 'name already in use'
        else:
            self.flux_label.invalid_msg = ''
            self.flux_label_overwrite = False

    @with_spinner()
    def flatten(self, add_data=True):
        """
        Flatten the input light curve (``dataset``) using lightkurve.flatten.

        Parameters
        ----------
        add_data : bool
            Whether to add the resulting light curve as a flux column and select that as the new
            flux column (origin) for that data entry.

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
            # add data as a new flux and corresponding err columns in the existing data entry
            # and select as flux column (origin)
            data = _data_with_reftime(self.app, output_lc)
            self.flux_column.add_new_flux_column(flux=data['flux'],
                                                 flux_err=data['flux_err'],
                                                 label=self.flux_label.value,
                                                 selected=True)

        return output_lc, trend_lc

    def _clear_marks(self):
        for mark_set in self.marks:
            for mark in mark_set.values():
                if mark.visible:
                    mark.clear()
                    mark.visible = False

    @observe('is_active', 'show_live_preview', 'show_trend_preview')
    def _toggle_marks(self, event={}):
        live_visible = self.show_live_preview and self.is_active
        trend_visible = self.show_trend_preview and self.is_active

        trend_marks, flattened_marks = self.marks
        for mark in trend_marks.values():
            mark.visible = trend_visible
        for mark in flattened_marks.values():
            mark.visible = live_visible

        if ((live_visible or trend_visible) and
                event.get('name') in ('is_active', 'show_live_preview', 'show_trend_preview')):
            # then the marks themselves need to be updated
            self._live_update(event)

    @observe('dataset_selected', 'flux_column_selected',
             'window_length', 'polyorder', 'break_tolerance',
             'niters', 'sigma', 'previews_temp_disabled')
    @skip_if_no_updates_since_last_active()
    @with_temp_disable(0.3)
    def _live_update(self, event={}):
        if self.dataset_selected == '' or self.flux_column_selected == '':
            self._clear_marks()
            return

        try:
            output_lc, trend_lc = self.flatten(add_data=False)
        except Exception as e:
            self.flatten_err = str(e)
            self._clear_marks()
            return
        self.flatten_err = ''

        if event.get('name') not in ('is_active', 'show_live_preview', 'show_trend_preview'):
            # mark visibility hasn't been handled yet
            self._toggle_marks(event)

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
        for mark in flattened_marks.values():
            mark.update_ty(times.value, output_flux)

    def vue_apply(self, *args, **kwargs):
        try:
            self.flatten(add_data=True)
        except Exception as e:
            self.flatten_err = str(e)
        else:
            self.flatten_err = ''
