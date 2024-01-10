from astropy import units as u
from functools import cached_property

from ipyvuetify import VuetifyTemplate
from glue.core import HubListener
from traitlets import List, Unicode

from jdaviz.core.template_mixin import DatasetSelect, SelectPluginComponent

from lcviz.events import (EphemerisComponentChangedMessage,
                          FluxColumnChangedMessage)

__all__ = ['EphemerisSelect', 'EphemerisSelectMixin',
           'FluxColumnSelect', 'FluxColumnSelectMixin']


class EphemerisSelect(SelectPluginComponent):
    """
    Plugin select for ephemeris components defined by the Ephemeris plugin.

    Useful API methods/attributes:

    * :meth:`~SelectPluginComponent.choices`
    * ``selected``
    * :attr:`selected_obj`
    * :meth:`~SelectPluginComponent.select_default`
    """

    """
    Traitlets (in the object, custom traitlets in the plugin):

    * ``items`` (list of dicts with keys: label)
    * ``selected`` (string)

    Properties (in the object only):

    * ``selected_obj``

    To use in a plugin:

    * create traitlets with default values
    * register with all the automatic logic in the plugin's init by passing the string names
      of the respective traitlets
    * use component in plugin template (see below)
    * refer to properties above based on the interally stored reference to the
      instantiated object of this component

    Example template (label and hint are optional)::

      <plugin-ephemeris-select
        :items="ephemeris_items"
        :selected.sync="ephemeris_selected"
        label="Ephemeris"
        hint="Select ephemeris."
      />

    """
    def __init__(self, plugin, items, selected,
                 default_text='No ephemeris', manual_options=[],
                 default_mode='first'):
        """
        Parameters
        ----------
        plugin
            the parent plugin object
        items : str
            the name of the items traitlet defined in ``plugin``
        selected : str
            the name of the selected traitlet defined in ``plugin``
        default_text : str or None
            the text to show for no selection.  If not provided or None, no entry will be provided
            in the dropdown for no selection.
        manual_options: list
            list of options to provide that are not automatically populated by ephemerides.  If
            ``default`` text is provided but not in ``manual_options`` it will still be included as
            the first item in the list.
        """
        super().__init__(plugin, items=items, selected=selected,
                         default_text=default_text, manual_options=manual_options,
                         default_mode=default_mode)
        self.hub.subscribe(self, EphemerisComponentChangedMessage,
                           handler=self._ephem_component_change)

    @cached_property
    def ephemeris_plugin(self):
        return self.app._jdaviz_helper.plugins.get('Ephemeris', None)

    @cached_property
    def selected_obj(self):
        if self.selected in self._manual_options:
            return None
        return self.ephemeris_plugin.ephemerides.get(self.selected, None)

    def get_data_for_dataset(self, dataset, ycomp='flux'):
        if not isinstance(dataset, DatasetSelect):  # pragma: no cover
            raise ValueError("dataset must be DatasetSelect object")
        if self.selected in self._manual_options:
            return dataset.selected_obj
        return self.ephemeris_plugin.get_data(dataset.selected, self.selected)

    def _ephem_component_change(self, msg=None):
        type = getattr(msg, 'type', None)
        if type == 'remove' and msg.old_lbl in self.choices:
            self.items = [item for item in self.items if item['label'] != msg.old_lbl]
            self._apply_default_selection()
        elif type == 'rename' and msg.old_lbl in self.choices:
            was_selected = self.selected == msg.old_lbl
            self.items = [item if item['label'] != msg.old_lbl else {'label': msg.new_lbl}
                          for item in self.items]
            if was_selected:
                self.selected = msg.new_lbl
        elif type == 'add' and msg.new_lbl not in self.choices:
            self.items = self.items + [{'label': msg.new_lbl}]
        else:
            # something might be out of sync, build from scratch
            manual_items = [{'label': label} for label in self.manual_options]
            self.items = manual_items + [{'label': component}
                                         for component in self.ephemeris_plugin.ephemerides.keys()]
            self._apply_default_selection()


class EphemerisSelectMixin(VuetifyTemplate, HubListener):
    """
    Applies the EphemerisSelect component as a mixin in the base plugin.  This
    automatically adds traitlets as well as new properties to the plugin with minimal
    extra code.  For multiple instances or custom traitlet names/defaults, use the
    component instead.

    To use in a plugin:

    * add ``EphemerisSelectMixin`` as a mixin to the class
    * use the traitlets available from the plugin or properties/methods available from
      ``plugin.ephemeris``.

    Example template (label and hint are optional)::

      <plugin-ephemeris-select
        :items="ephemeris_items"
        :selected.sync="ephemeris_selected"
        label="Ephemeris"
        hint="Select ephemeris."
      />

    """
    ephemeris_items = List().tag(sync=True)
    ephemeris_selected = Unicode().tag(sync=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ephemeris = EphemerisSelect(self, 'ephemeris_items', 'ephemeris_selected')


class FluxColumnSelect(SelectPluginComponent):
    def __init__(self, plugin, items, selected, dataset):
        super().__init__(plugin,
                         items=items,
                         selected=selected,
                         dataset=dataset)

        self.add_observe(selected, self._on_change_selected)
        self.add_observe(self.dataset._plugin_traitlets['selected'],
                         self._on_change_dataset)

        # sync between instances in different plugins
        self.hub.subscribe(self, FluxColumnChangedMessage,
                           handler=self._on_flux_column_changed_msg)

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
        flux_column = lk_obj.meta.get('FLUX_ORIGIN')
        if flux_column in self.choices:
            self.selected = flux_column
        else:
            self.selected = ''

    def _on_flux_column_changed_msg(self, msg):
        if msg.dataset != self.dataset.selected:
            return

        # need to clear the cache due to the change in metadata made to the data-collection entry
        self.dataset._clear_cache('selected_obj', 'selected_dc_item')
        self._on_change_dataset()
        self.selected = msg.flux_column

    def _on_change_selected(self, *args):
        if self.selected == '':
            return

        dc_item = self.dataset.selected_dc_item
        old_flux_column = dc_item.meta.get('FLUX_ORIGIN')
        if self.selected == old_flux_column:
            # nothing to do here!
            return

        # instead of using lightkurve's select_flux and having to reparse the data entry, we'll
        # manipulate the arrays in the data-collection directly, and modify FLUX_ORIGIN so that
        # exporting back to a lightkurve object works as expected
        self.app._jdaviz_helper._set_data_component(dc_item, 'flux', dc_item[self.selected])
        self.app._jdaviz_helper._set_data_component(dc_item, 'flux_err', dc_item[self.selected+"_err"])  # noqa
        dc_item.meta['FLUX_ORIGIN'] = self.selected

        self.hub.broadcast(FluxColumnChangedMessage(dataset=self.dataset.selected,
                                                    flux_column=self.selected,
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
        self.hub.broadcast(FluxColumnChangedMessage(dataset=self.dataset.selected,
                                                    flux_column=label if selected else self.selected,  # noqa
                                                    sender=self))


class FluxColumnSelectMixin(VuetifyTemplate, HubListener):
    flux_column_items = List().tag(sync=True)
    flux_column_selected = Unicode().tag(sync=True)
    # assumes DatasetSelectMixin is also used (DatasetSelectMixin must appear after in inheritance)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.flux_column = FluxColumnSelect(self,
                                            'flux_column_items',
                                            'flux_column_selected',
                                            dataset='dataset')
