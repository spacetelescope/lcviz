from traitlets import Bool, Unicode, observe
from lightkurve import LightCurve, LightCurveCollection

from jdaviz.core.registries import tray_registry
from jdaviz.core.template_mixin import (PluginTemplateMixin,
                                        DatasetMultiSelectMixin,
                                        AddResultsMixin,
                                        with_spinner)
from jdaviz.core.user_api import PluginUserApi

from lcviz.utils import data_not_folded, is_not_tpf

__all__ = ['Stitch']


@tray_registry('stitch', label="Stitch")
class Stitch(PluginTemplateMixin, DatasetMultiSelectMixin, AddResultsMixin):
    """
    See the :ref:`Stitch Plugin Documentation <stitch>` for more details.

    Only the following attributes and methods are available through the
    :ref:`public plugin API <plugin-apis>`:

    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.show`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.open_in_tray`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.close_in_tray`
    * ``dataset`` (:class:`~jdaviz.core.template_mixin.DatasetSelect`):
      Datasets to stitch.
    * ``remove_input_datasets``
    * ``add_results`` (:class:`~jdaviz.core.template_mixin.AddResults`)
    * :meth:`stitch`
    """
    template_file = __file__, "stitch.vue"
    uses_active_status = Bool(False).tag(sync=False)

    remove_input_datasets = Bool(False).tag(sync=True)
    stitch_err = Unicode().tag(sync=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._plugin_description = 'Stitch light curves together.'

        self.dataset.multiselect = True
        # do not support stitching data in phase-space
        # do not allow TPF as input
        self.dataset.add_filter(data_not_folded, is_not_tpf)

        self.results_label_default = 'stitched'

    @property
    def user_api(self):
        expose = ['dataset', 'stitch', 'remove_input_datasets', 'add_results']
        return PluginUserApi(self, expose=expose)

    @observe('dataset_items')
    def _set_relevent(self, *args):
        if len(self.dataset_items) < 2:
            self.irrelevant_msg = 'Requires at least two datasets loaded into viewers'
        else:
            self.irrelevant_msg = ''

    @with_spinner()
    def stitch(self, add_data=True):
        """
        Stitch multiple light curves (``dataset``) together using lightkurve.stitch.

        Parameters
        ----------
        add_data : bool
            Whether to add the resulting light curve to the app.

        Returns
        -------
        output_lc : `~lightkurve.LightCurve`
            The flattened light curve.
        """
        if not self.dataset.multiselect:
            raise ValueError("dataset must be in multiselect mode")
        if len(self.dataset.selected) < 2:
            raise ValueError("multiple datasets must be selected")
        lcc = LightCurveCollection([dci.get_object(LightCurve)
                                    for dci in self.dataset.selected_dc_item])
        stitched_lc = lcc.stitch(corrector_func=lambda x: x)

        if add_data:
            self.add_results.add_results_from_plugin(stitched_lc)
            if self.remove_input_datasets:
                for dataset in self.dataset.selected:
                    self.app.data_item_remove(dataset)
        return stitched_lc

    def vue_apply(self, *args, **kwargs):
        try:
            self.stitch(add_data=True)
        except Exception as e:
            self.stitch_err = str(e)
        else:
            self.stitch_err = ''
