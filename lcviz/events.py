from glue.core.message import Message

__all__ = ['ViewerRenamedMessage', 'EphemerisComponentChangedMessage']


class ViewerRenamedMessage(Message):
    """Message emitted after a viewer is destroyed by the application."""
    def __init__(self, old_viewer_ref, new_viewer_ref, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.old_viewer_ref = old_viewer_ref
        self.new_viewer_ref = new_viewer_ref


class EphemerisComponentChangedMessage(Message):
    """Message emitted when an ephemeris component is added/renamed/removed in the
    ephemeris plugin"""
    def __init__(self, old_lbl, new_lbl, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.old_lbl = old_lbl
        self.new_lbl = new_lbl
        if old_lbl is not None and new_lbl is not None:
            self.type = 'rename'
        elif old_lbl is None and new_lbl is not None:
            self.type = 'add'
        elif old_lbl is not None and new_lbl is None:
            self.type = 'remove'
        else:
            raise ValueError("must provide at least one of old_lbl or new_lbl")
