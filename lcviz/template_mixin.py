from functools import cached_property
from traitlets import List, Unicode
from ipyvuetify import VuetifyTemplate
from glue.core import HubListener

import jdaviz
from jdaviz.core.template_mixin import ViewerSelect, DatasetSelect, SelectPluginComponent
from lcviz.events import ViewerRenamedMessage, EphemerisComponentChangedMessage

__all__ = ['EphemerisSelect', 'EphemerisSelectMixin']


# TODO: remove this if/when jdaviz supports renaming viewers natively
class ViewerSelect(ViewerSelect):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hub.subscribe(self, ViewerRenamedMessage, handler=self._on_viewers_changed)


# monkey-patch upstream version so all plugins use the viewer-renamed logic
jdaviz.core.template_mixin.ViewerSelect = ViewerSelect


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
