from glue.core.message import Message

__all__ = ['ViewerRenamedMessage']


class ViewerRenamedMessage(Message):
    """Message emitted after a viewer is destroyed by the application."""
    def __init__(self, old_viewer_ref, new_viewer_ref, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._old_viewer_ref = old_viewer_ref
        self._new_viewer_ref = new_viewer_ref

    @property
    def old_viewer_ref(self):
        return self._old_viewer_ref

    @property
    def new_viewer_ref(self):
        return self._new_viewer_ref
