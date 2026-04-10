import numpy as np

from glue.core.subset_group import GroupedSubset
from glue_jupyter.bqplot.image.layer_artist import BqplotImageSubsetLayerArtist
from jdaviz.configs.imviz.plugins.coords_info import CoordsInfo

from lcviz.viewers import TimeScatterView, PhaseScatterView, CubeView

__all__ = []


def _lc_viewer_update(self, viewer, x, y, mouseevent=True):
    """CoordsInfo update handler for TimeScatterView and PhaseScatterView."""
    if not len(viewer.state.layers):
        return

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
            closest_icon = self._app.state.layer_icons.get(lyr.layer.label, '')
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


def _lcviz_tpf_image_viewer_update(self, viewer, x, y, mouseevent=True):
    """CoordsInfo update handler for CubeView (TPF image viewer)."""
    if not len(viewer.state.layers):
        return

    active_layer = viewer.active_image_layer
    if active_layer is None:
        self._viewer_mouse_clear_event(viewer)
        return

    if self.dataset.selected == 'auto':
        image = active_layer.layer
    elif self.dataset.selected == 'none':
        active_layer = viewer.layers[0].state
        image = viewer.layers[0].layer
    else:
        for layer in viewer.layers:
            if layer.layer.label == self.dataset.selected and layer.visible:
                if isinstance(layer, BqplotImageSubsetLayerArtist):
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

    if self.dataset.selected != 'none' and image is not None:
        self.icon = self._app.state.layer_icons.get(image.label, '')
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
        if time is None:
            self._viewer_mouse_clear_event(viewer)
            return
        # TODO: store slice unit within image viewer to avoid this assumption?
        tvs = self._app.get_viewers_of_cls(TimeScatterView)
        if len(tvs):
            time_unit = str(tvs[0].time_unit)
        else:
            time_unit = 's'
        self.row2_title = 'Time'
        self.row2_text = f'{time:0.5f} {time_unit}'
        self._dict['time'] = time
        self._dict['time:unit'] = time_unit

    maxsize = int(np.ceil(np.log10(np.max(active_layer.layer.shape)))) + 3
    fmt = 'x={0:0' + str(maxsize) + '.1f} y={1:0' + str(maxsize) + '.1f}'
    self.row1a_title = 'Pixel'
    self.row1a_text = fmt.format(x, y)
    self._dict['pixel'] = (float(x), float(y))

    if self.dataset.selected == 'none' or image is None:
        self.row1b_title = ''
        self.row1b_text = ''
        return

    # TPF cube shape is [time, y, x] so ix_shape=2, iy_shape=1
    ix_shape, iy_shape = 2, 1

    if (-0.5 < x < image.shape[ix_shape] - 0.5 and -0.5 < y < image.shape[iy_shape] - 0.5
            and hasattr(active_layer, 'attribute')):
        attribute = active_layer.attribute
        arr = image.get_component(attribute).data
        unit = image.get_component(attribute).units
        # TPF cube indexing: arr[time_slice, y, x]
        value = arr[viewer.state.slices[0], int(round(y)), int(round(x))]
        self.row1b_title = 'Value'
        self.row1b_text = f'{value:+10.5e} {unit}'
        self._dict['value'] = float(value)
        self._dict['value:unit'] = unit
    else:
        self.row1b_title = ''
        self.row1b_text = ''


# Register lcviz viewer classes and their update handlers with the upstream CoordsInfo.
CoordsInfo.register_viewer_class(TimeScatterView, with_marker=True)
CoordsInfo.register_viewer_class(PhaseScatterView, with_marker=True)
CoordsInfo.register_viewer_class(CubeView, with_marker=False)

CoordsInfo.register_viewer_update_handler(TimeScatterView, _lc_viewer_update)
CoordsInfo.register_viewer_update_handler(PhaseScatterView, _lc_viewer_update)
CoordsInfo.register_viewer_update_handler(CubeView, _lcviz_tpf_image_viewer_update)

