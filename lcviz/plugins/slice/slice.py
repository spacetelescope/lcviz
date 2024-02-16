from glue_jupyter.bqplot.scatter import BqplotScatterView
from glue.core.message import (DataCollectionAddMessage,
                               DataCollectionDeleteMessage)


from jdaviz.configs.cubeviz.plugins import Slice
from jdaviz.core.registries import tray_registry

#from lcviz.viewers import CubeView

__all__ = ['Slice']


@tray_registry('lcviz-slice', label="Slice")
class Slice(Slice):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.docs_link = f"https://lcviz.readthedocs.io/en/{self.vdocs}/plugins.html#slice"
        self.docs_description = "Select time to show in the image viewer.  The slice can also be changed interactively in any time viewer by activating the slice tool."  # noqa
        self.value_label = 'Time'
        self.value_unit = 'd'

        for id, viewer in self.app._viewer_store.items():
            if isinstance(viewer, BqplotScatterView) or len(viewer.data()):
                self._watch_viewer(viewer, True)

        for msg in (DataCollectionAddMessage, DataCollectionDeleteMessage):
            self.session.hub.subscribe(self, msg, handler=self._update_relevant)
        self._update_relevant()

    @property
    def slice_component_label(self):
        # label of the component in the cubes corresponding to the slice axis
        # calling data_collection_item.get_component(slice_component_label) on any
        # input cube-data must work
        return 'dt'

    @property
    def slice_index(self):
        # index in viewer.slices corresponding to the slice axis
        return 0

    @property
    def slice_axis(self):
        # global display unit "axis" corresponding to the slice axis
        return 'time'

    def _update_relevant(self, *args):
        # whether the plugin is currently relevant and should appear in the tray
        # TODO: if adding a button in the slice plugin to create an image viewer, then this
        # should be changed to check for cube data in the data-collection instead
        for data in self.app.data_collection:
            if data.ndim == 3:
                self.irrelevant_msg = ''
                return
        self.irrelevant_msg = 'Slice plugin is only relevant when cube-like data (e.g., TPF data) is loaded in the app'  # noqa

    @property
    def user_api(self):
        api = super().user_api
        # can be removed after deprecated upstream attributes for wavelength/wavelength_value
        # are removed in the lowest supported version of jdaviz
        api._expose = [e for e in api._expose if e not in ('wavelength', 'wavelength_value', 'show_wavelength')]  # noqa
        return api

    def _watch_viewer(self, viewer, watch=True):
        super()._watch_viewer(viewer, watch=watch)
        # image viewer watching handled upstream
        if isinstance(viewer, BqplotScatterView):
            if self._x_all is None and len(viewer.data()):
                # cache values (wavelengths/freqs) so that value <> slice conversion can efficient
                self._update_data(viewer.data()[0].time)

            if viewer not in self._indicator_viewers:
                self._indicator_viewers.append(viewer)
                # if the units (or data) change, we need to update internally
# need to subscribe to add_data instead of reference_data....
#                viewer.state.add_callback("reference_data",
#                                          self._update_reference_data)

    def _update_reference_data(self, reference_data):
        if reference_data is None:
            return  # pragma: no cover
        self._update_data(reference_data.get_object().time)

#    def _viewer_slices_changed(self, value):
#        if len(value) == 3:
#            self.slice = float(value[0])

#    def _set_viewer_to_slice(self, viewer, value):
#        viewer.state.slices = (value, 0, 0)
