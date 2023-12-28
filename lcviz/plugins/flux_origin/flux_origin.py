from traitlets import List, Unicode, observe

from jdaviz.core.registries import tray_registry
from jdaviz.core.template_mixin import (PluginTemplateMixin,
                                        DatasetSelectMixin, SelectPluginComponent)
from jdaviz.core.user_api import PluginUserApi

__all__ = ['FluxOrigin']


@tray_registry('flux-origin', label="Flux Origin")
class FluxOrigin(PluginTemplateMixin, DatasetSelectMixin):
    """
    See the :ref:`Flux Origin Plugin Documentation <flux-origin>` for more details.

    Only the following attributes and methods are available through the
    public plugin API.

    * ``dataset`` (:class:`~jdaviz.core.template_mixin.DatasetSelect`):
      Dataset to bin.
    """
    template_file = __file__, "flux_origin.vue"

    origin_items = List().tag(sync=True)
    origin_selected = Unicode().tag(sync=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.origin = SelectPluginComponent(self,
                                            items='origin_items',
                                            selected='origin_selected')

    @property
    def user_api(self):
        expose = ['dataset', 'origin']
        return PluginUserApi(self, expose=expose)

    @observe('dataset_selected')
    def _on_change_dataset(self, *args):
        def _include_col(lk_obj, col):
            if col == 'flux' and lk_obj.meta.get('FLUX_ORIGIN') != 'flux':
                # this is the currently active column (and should be copied elsewhere unless)
                return False
            if col in ('time', 'cadn', 'cadenceno', 'quality'):
                return False
            if col.startswith('phase:'):
                # internal jdaviz ephemeris phase columns
                return False
            if col.startswith('time'):
                return False
            if col.startswith('centroid'):
                return False
            if col.startswith('cbv'):
                # cotrending basis vector
                return False
            if col.endswith('_err'):
                return False
            if col.endswith('quality'):
                return False
            # TODO: need to think about flatten losing units in the flux column (and that other
            # columns still exist but are not flattened)
            return lk_obj[col].unit == lk_obj['flux'].unit

        lk_obj = self.dataset.selected_obj
        if lk_obj is None:
            return
        self.origin.choices = [col for col in lk_obj.columns if _include_col(lk_obj, col)]
        flux_origin = lk_obj.meta.get('FLUX_ORIGIN')
        if flux_origin in self.origin.choices:
            self.origin.selected = flux_origin
        else:
            self.origin.selected = ''

    @observe('origin_selected')
    def _on_change_origin(self, *args):
        if self.origin_selected == '':
            return

        dc_item = self.dataset.selected_dc_item
        old_flux_origin = dc_item.meta.get('FLUX_ORIGIN')
        if self.origin.selected == old_flux_origin:
            # nothing to do here!
            return

        # instead of using lightkurve's select_flux and having to reparse the data entry, we'll
        # manipulate the arrays in the data-collection directly, and modify FLUX_ORIGIN so that
        # exporting back to a lightkurve object works as expected
        dc_item = self.dataset.selected_dc_item

        self.app._jdaviz_helper._set_data_component(dc_item, 'flux', dc_item[self.origin.selected])
        dc_item.meta['FLUX_ORIGIN'] = self.origin.selected
        # need to clear the cache manually due to the change in metadata made to the data-collection
        # entry
        self.dataset._clear_cache('selected_obj')
