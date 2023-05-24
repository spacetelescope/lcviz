import jdaviz
from jdaviz.core.events import SnackbarMessage
from jdaviz.core.template_mixin import SelectPluginComponent
from jdaviz.core.template_mixin import ViewerSelect
from lcviz.events import ViewerRenamedMessage

__all__ = ['EditableSelectPluginComponent']


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
