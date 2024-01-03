from astropy import units as u
from ipyvuetify import VuetifyTemplate
from glue.core import HubListener
from traitlets import List, Unicode

from jdaviz.core.template_mixin import SelectPluginComponent

from lcviz.events import FluxOriginChangedMessage

__all__ = ['FluxOriginSelect', 'FluxOriginSelectMixin']


class FluxOriginSelect(SelectPluginComponent):
    def __init__(self, plugin, items, selected, dataset):
        super().__init__(plugin,
                         items=items,
                         selected=selected,
                         dataset=dataset)

        self.add_observe(selected, self._on_change_selected)
        self.add_observe(self.dataset._plugin_traitlets['selected'],
                         self._on_change_dataset)

        # sync between instances in different plugins
        self.hub.subscribe(self, FluxOriginChangedMessage,
                           handler=self._on_flux_origin_changed_msg)

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
            # TODO: need to think about flatten losing units in the flux column
            return lk_obj[col].unit != u.pix

        lk_obj = self.dataset.selected_obj
        if lk_obj is None:
            return
        self.choices = [col for col in lk_obj.columns if _include_col(lk_obj, col)]
        flux_origin = lk_obj.meta.get('FLUX_ORIGIN')
        if flux_origin in self.choices:
            self.selected = flux_origin
        else:
            self.selected = ''

    def _on_flux_origin_changed_msg(self, msg):
        if msg.dataset != self.dataset.selected:
            return

        # need to clear the cache due to the change in metadata made to the data-collection entry
        self.dataset._clear_cache('selected_obj', 'selected_dc_item')
        self._on_change_dataset()
        self.selected = msg.flux_origin

    def _on_change_selected(self, *args):
        if self.selected == '':
            return

        dc_item = self.dataset.selected_dc_item
        old_flux_origin = dc_item.meta.get('FLUX_ORIGIN')
        if self.selected == old_flux_origin:
            # nothing to do here!
            return

        # instead of using lightkurve's select_flux and having to reparse the data entry, we'll
        # manipulate the arrays in the data-collection directly, and modify FLUX_ORIGIN so that
        # exporting back to a lightkurve object works as expected
        self.app._jdaviz_helper._set_data_component(dc_item, 'flux', dc_item[self.selected])
        self.app._jdaviz_helper._set_data_component(dc_item, 'flux_err', dc_item[self.selected+"_err"])  # noqa
        dc_item.meta['FLUX_ORIGIN'] = self.selected

        self.hub.broadcast(FluxOriginChangedMessage(dataset=self.dataset.selected,
                                                    flux_origin=self.selected,
                                                    sender=self))

    def add_new_flux_column(self, flux, flux_err, label, selected=False):
        dc_item = self.dataset.selected_dc_item
        self.app._jdaviz_helper._set_data_component(dc_item,
                                                    label,
                                                    flux)
        self.app._jdaviz_helper._set_data_component(dc_item,
                                                    f"{label}_err",
                                                    flux_err)

        # broadcast so all instances update to get the new column and selection (if applicable)
        self.hub.broadcast(FluxOriginChangedMessage(dataset=self.dataset.selected,
                                                    flux_origin=label if selected else self.selected,  # noqa
                                                    sender=self))


class FluxOriginSelectMixin(VuetifyTemplate, HubListener):
    flux_origin_items = List().tag(sync=True)
    flux_origin_selected = Unicode().tag(sync=True)
    # assumes DatasetSelectMixin is also used (DatasetSelectMixin must appear after in inheritance)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.flux_origin = FluxOriginSelect(self,
                                            'flux_origin_items',
                                            'flux_origin_selected',
                                            dataset='dataset')
