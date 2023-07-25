from functools import cached_property
from traitlets import List, Unicode
from ipyvuetify import VuetifyTemplate
from glue.core import HubListener

import jdaviz
from jdaviz.core.events import SnackbarMessage
from jdaviz.core.template_mixin import SelectPluginComponent, DatasetSelect
from jdaviz.core.template_mixin import ViewerSelect
from lcviz.events import ViewerRenamedMessage, EphemerisComponentChangedMessage

__all__ = ['EditableSelectPluginComponent',
           'EphemerisSelect', 'EphemerisSelectMixin']


# TODO: remove this if/when jdaviz supports renaming viewers natively
class ViewerSelect(ViewerSelect):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hub.subscribe(self, ViewerRenamedMessage, handler=self._on_viewers_changed)


# monkey-patch upstream version so all plugins use the viewer-renamed logic
jdaviz.core.template_mixin.ViewerSelect = ViewerSelect


class EditableSelectPluginComponent(SelectPluginComponent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_multiselect:
            self._multiselect_changed()
        self.add_observe(kwargs.get('mode'), self._mode_changed)
        self.mode = 'select'  # select, rename, add
        self._on_add = kwargs.get('on_add', lambda *args: None)
        self._on_rename = kwargs.get('on_rename', lambda *args: None)
        self._on_remove = kwargs.get('on_remove', lambda *args: None)

    def _multiselect_changed(self):
        # already subscribed to traitlet by SelectPluginComponent
        if self.multiselect:
            raise ValueError("EditableSelectPluginComponent does not support multiselect")

    def _selected_changed(self, event):
        super()._selected_changed(event)
        self.edit_value = self.selected

    def _mode_changed(self, event):
        if self.mode == 'rename:accept':
            try:
                self.rename_choice(self.selected, self.edit_value)
            except ValueError:
                self.hub.broadcast(SnackbarMessage("Renaming ephemeris failed",
                                   sender=self, color="error"))
            else:
                self.mode = 'select'
                self.edit_value = self.selected
        elif self.mode == 'add:accept':
            try:
                self.add_choice(self.edit_value)
            except ValueError:
                self.hub.broadcast(SnackbarMessage("Adding ephemeris failed",
                                   sender=self, color="error"))
            else:
                self.mode = 'select'
                self.edit_value = self.selected
        elif self.mode == 'remove:accept':
            self.remove_choice(self.edit_value)
            if len(self.choices):
                self.mode = 'select'
            else:
                self.mode = 'add'

    def _update_items(self):
        self.items = [{"label": opt} for opt in self._manual_options]

    def _check_new_choice(self, label):
        if not len(label):
            raise ValueError("new choice must not be blank")
        if label in self.choices:
            raise ValueError(f"'{label}' is already a valid choice")

    def add_choice(self, label, set_as_selected=True):
        self._check_new_choice(label)
        self._manual_options += [label]
        self._update_items()
        self._on_add(label)
        if set_as_selected:
            self.selected = label

    def remove_choice(self, label=None):
        if label is None:
            label = self.selected
        if label not in self.choices:
            raise ValueError(f"'{label}' not one of available choices ({self.choices})")
        self._manual_options.remove(label)
        self._update_items()
        self._apply_default_selection(skip_if_current_valid=True)
        self._on_remove(label)

    def rename_choice(self, old, new):
        if old not in self.choices:
            raise ValueError(f"'{old}' not one of available choices ({self.choices})")
        self._check_new_choice(new)
        was_selected = self.selected == old
        self._manual_options[self._manual_options.index(old)] = new
        self._update_items()
        if was_selected:
            self.selected = new
        self._on_rename(old, new)


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
        if not isinstance(dataset, DatasetSelect):
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
