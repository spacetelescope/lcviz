import numpy as np

from glue.core.subset_group import GroupedSubset
from jdaviz.configs.imviz.plugins.coords_info import CoordsInfo
from jdaviz.core.events import ViewerRenamedMessage
from jdaviz.core.registries import tool_registry

from lcviz.viewers import TimeScatterView, PhaseScatterView, CubeView

__all__ = ['CoordsInfo']


@tool_registry('lcviz-coords-info')
class CoordsInfo(CoordsInfo):
    _supported_viewer_classes = (TimeScatterView, PhaseScatterView, CubeView)
    _viewer_classes_with_marker = (TimeScatterView, PhaseScatterView)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO: move to jdaviz if/once viewer renaming supported
        self.hub.subscribe(self, ViewerRenamedMessage,
                           handler=self._viewer_renamed)

    def _viewer_renamed(self, msg):
        self._marks[msg.new_viewer_ref] = self._marks.pop(msg.old_viewer_ref)

    def _image_shape_inds(self, image):
        if image.ndim == 3:
            # exception to the upstream cubeviz case of (0, 1)
            return (2, 1)
        return super()._image_shape_inds(image)

    def _get_cube_value(self, image, arr, x, y, viewer):
        if image.ndim == 3:
            # exception to the upstream cubeviz case of x, y, slice
            return arr[viewer.state.slices[0], int(round(y)), int(round(x))]
        return super()._get_cube_value(image, arr, x, y, viewer)

    def _lc_viewer_update(self, viewer, x, y):
        is_phase = isinstance(viewer, PhaseScatterView)
        # TODO: update with display_unit when supported in lcviz
        x_unit = '' if is_phase else str(viewer.time_unit)
        y_unit = str(viewer.data()[0].flux.unit)

        def _cursor_fallback():
            self._dict['axes_x'] = x
            self._dict['axes_x:unit'] = x_unit
            self._dict['axes_y'] = y
            self._dict['axes_y:unit'] = y_unit

            self._dict['data_label'] = ''
            self._dict['time'] = x if not is_phase else np.nan
            self._dict['time:unit'] = x_unit
            self._dict['phase'] = x if is_phase else np.nan
            self._dict['value'] = y
            self._dict['value:unit'] = y_unit
            self._dict['ephemeris'] = ''

            self.row2_title = ''
            self.row2_text = ''
            self.row3_title = ''
            self.row3_text = ''
            self.icon = 'mdi-cursor-default'
            self.marks[viewer._reference_id].visible = False

        self.row1a_title = 'Cursor'
        self.row1a_text = f'{x:10.5e}, {y:10.5e}'

        # show the locked marker/coords only if either no tool or the default tool is active
        if self.dataset.selected == 'none':
            _cursor_fallback()
            return

        xrange = abs(viewer.state.x_max - viewer.state.x_min)
        yrange = abs(viewer.state.y_max - viewer.state.y_min)

        # Snap to the closest data point
        closest_distsq = None
        closest_x = None
        closest_y = None
        closest_icon = None
        closest_lyr = None
        for lyr in viewer.layers:
            if isinstance(lyr.layer, GroupedSubset):
                continue
            if self.dataset.selected == 'auto' and not lyr.visible:
                continue
            if self.dataset.selected != 'auto' and self.dataset.selected != lyr.layer.label:
                continue

            scatter = lyr.scatter_mark
            lyr_x, lyr_y = scatter.x, scatter.y
            if not len(lyr_x):
                continue

            # NOTE: unlike specviz which determines the closest point in x per-layer,
            # this determines the closest point in x/y per-layer in pixel-space
            # (making it easier to get the snapping point into shallow eclipses, etc)
            distsqs = ((lyr_x - x)/xrange)**2 + ((lyr_y - y)/yrange)**2
            cur_i = np.nanargmin(distsqs)
            cur_x, cur_y = float(lyr_x[cur_i]), float(lyr_y[cur_i])
            cur_distsq = distsqs[cur_i]

            if (closest_distsq is None) or (cur_distsq < closest_distsq):
                closest_distsq = cur_distsq
                closest_i = cur_i
                closest_x = cur_x
                closest_y = cur_y
                closest_icon = self.app.state.layer_icons.get(lyr.layer.label, '')
                closest_lyr = lyr
                self._dict['data_label'] = lyr.layer.label

        if closest_lyr is None:
            _cursor_fallback()
            return

        self.row2_title = 'Phase' if is_phase else 'Time'
        if is_phase:
            self.row2_text = f'{closest_x:0.05f}'
            component_labels = [comp.label for comp in closest_lyr.layer.components]
            time_comp = closest_lyr.layer.components[component_labels.index('World 0')]
            times = closest_lyr.layer.get_data(time_comp)
            self._dict['time'] = float(times[closest_i])
            self._dict['time:unit'] = str(viewer.time_unit)  # x_unit is phase
            self._dict['phase'] = closest_x
            self._dict['ephemeris'] = viewer.reference.split(':')[1]
        else:
            self.row2_text = f'{closest_x:10.5e} {x_unit}'
            self._dict['time'] = closest_x
            self._dict['time:unit'] = x_unit
            self._dict['phase'] = np.nan
            self._dict['ephemeris'] = ''

        self._dict['axes_x'] = closest_x
        self._dict['axes_x:unit'] = x_unit
        self._dict['index'] = float(closest_i)

        self.row3_title = 'Flux'
        self.row3_text = f'{closest_y:10.5e} {y_unit}'
        self._dict['axes_y'] = closest_y
        self._dict['axes_y:unit'] = y_unit
        self._dict['value'] = closest_y
        self._dict['value:unit'] = y_unit

        self.icon = closest_icon

        self.marks[viewer._reference_id].update_xy([closest_x], [closest_y])  # noqa
        self.marks[viewer._reference_id].visible = True

    def _image_viewer_update(self, viewer, x, y):
        # Extract first dataset from visible layers and use this for coordinates - the choice
        # of dataset shouldn't matter if the datasets are linked correctly
        active_layer = viewer.active_image_layer
        if active_layer is None:
            self._viewer_mouse_clear_event(viewer)
            return

        # TODO: refactor this code block (to retrieve the active layer)
        # upstream to make it resuable
        from glue_jupyter.bqplot.image.layer_artist import BqplotImageSubsetLayerArtist

        if self.dataset.selected == 'auto':
            image = active_layer.layer
        elif self.dataset.selected == 'none':
            active_layer = viewer.layers[0].state
            image = viewer.layers[0].layer
        else:
            for layer in viewer.layers:
                if layer.layer.label == self.dataset.selected and layer.visible:
                    if isinstance(layer, BqplotImageSubsetLayerArtist):
                        # cannot expose info for spatial subset layers
                        continue
                    active_layer = layer.state
                    image = layer.layer
                    break
            else:
                image = None

        self._dict['axes_x'] = x
        self._dict['axes_x:unit'] = 'pix'
        self._dict['axes_y'] = y
        self._dict['axes_y:unit'] = 'pix'

        # set default empty values
        if self.dataset.selected != 'none' and image is not None:
            self.icon = self.app.state.layer_icons.get(image.label, '')  # noqa
            self._dict['data_label'] = image.label

        if self.dataset.selected == 'none' or image is None:
            self.icon = 'mdi-cursor-default'
            self._dict['data_label'] = ''
        else:
            try:
                time = viewer.slice_value
            except IndexError:
                self._viewer_mouse_clear_event(viewer)
                return
            # TODO: store slice unit within image viewer to avoid this assumption?
            time_unit = str(self.app._jdaviz_helper.default_time_viewer._obj.time_unit)
            self.row2_title = 'Time'
            self.row2_text = f'{time:0.5f} {time_unit}'
            self._dict['time'] = time
            self._dict['time:unit'] = time_unit

        maxsize = int(np.ceil(np.log10(np.max(active_layer.layer.shape)))) + 3
        fmt = 'x={0:0' + str(maxsize) + '.1f} y={1:0' + str(maxsize) + '.1f}'
        self.row1a_title = 'Pixel'
        self.row1a_text = (fmt.format(x, y))
        self._dict['pixel'] = (float(x), float(y))

        if self.dataset.selected == 'none' or image is None:
            # no data values to extract
            self.row1b_title = ''
            self.row1b_text = ''
            return

        # Extract data values at this position.
        # Check if shape is [x, y, z] or [y, x] and show value accordingly.
        ix_shape, iy_shape = self._image_shape_inds(image)

        if (-0.5 < x < image.shape[ix_shape] - 0.5 and -0.5 < y < image.shape[iy_shape] - 0.5
                and hasattr(active_layer, 'attribute')):
            attribute = active_layer.attribute
            arr = image.get_component(attribute).data
            unit = image.get_component(attribute).units
            value = self._get_cube_value(image, arr, x, y, viewer)
            self.row1b_title = 'Value'
            self.row1b_text = f'{value:+10.5e} {unit}'
            self._dict['value'] = float(value)
            self._dict['value:unit'] = unit
        else:
            self.row1b_title = ''
            self.row1b_text = ''

    def update_display(self, viewer, x, y):
        self._dict = {}

        if not len(viewer.state.layers):
            return

        if isinstance(viewer, (TimeScatterView, PhaseScatterView)):
            self._lc_viewer_update(viewer, x, y)
        elif isinstance(viewer, CubeView):
            self._image_viewer_update(viewer, x, y)
