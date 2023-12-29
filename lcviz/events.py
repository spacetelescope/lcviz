from glue.core.message import Message

__all__ = ['EphemerisComponentChangedMessage',
           'EphemerisChangedMessage',
           'FluxOriginChangedMessage']


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
        else:  # pragma: no cover
            raise ValueError("must provide at least one of old_lbl or new_lbl")


class EphemerisChangedMessage(Message):
    """Message emitted when the parameters of an ephemeris are updated/changed
    in the ephemeris plugin"""
    def __init__(self, ephemeris_label, *args, **kwargs):
        self.ephemeris_label = ephemeris_label


class FluxOriginChangedMessage(Message):
    """Message emitted by the FluxOriginSelect component when the selection has been changed.
    To subscribe to a change for a particular dataset, consider using FluxOriginSelect directly
    and observing the traitlet, rather than subscribing to this message"""
    def __init__(self, dataset, flux_origin, *args, **kwargs):
        self.dataset = dataset
        self.flux_origin = flux_origin
