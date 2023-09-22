import numpy as np

from glue.core.subset_group import GroupedSubset
from jdaviz.configs.imviz.plugins.coords_info import CoordsInfo
from jdaviz.core.events import ViewerRenamedMessage
from jdaviz.core.registries import tool_registry

from lcviz.viewers import TimeScatterView, PhaseScatterView

__all__ = ['CoordsInfo']


@tool_registry('lcviz-coords-info')
class CoordsInfo(CoordsInfo):
    _supported_viewer_classes = (TimeScatterView, PhaseScatterView)
    _viewer_classes_with_marker = (TimeScatterView, PhaseScatterView)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO: move to jdaviz if/once viewer renaming supported
        self.hub.subscribe(self, ViewerRenamedMessage,
                           handler=self._viewer_renamed)

    def _viewer_renamed(self, msg):
        self._marks[msg.new_viewer_ref] = self._marks.pop(msg.old_viewer_ref)

    def update_display(self, viewer, x, y):
        self._dict = {}

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
            self._dict['phase'] = x if is_phase else np.nan
            self._dict['flux'] = y
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

            # glue-jupyter 1.18 changed from lyr.scatter to lyr.scatter_mark
            # TODO: once glue-jupyter is pinned to 1.18 or later, update this to:
            # scatter = lyr.scatter_mark
            scatter = getattr(lyr, 'scatter_mark', getattr(lyr, 'scatter', None))
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
            self._dict['phase'] = closest_x
            self._dict['ephemeris'] = viewer.reference.split(':')[1]
        else:
            self.row2_text = f'{closest_x:10.5e} {x_unit}'
            self._dict['time'] = closest_x
            self._dict['phase'] = np.nan
            self._dict['ephemeris'] = ''

        self._dict['axes_x'] = closest_x
        self._dict['axes_x:unit'] = x_unit
        self._dict['index'] = float(closest_i)

        self.row3_title = 'Flux'
        self.row3_text = f'{closest_y:10.5e} {y_unit}'
        self._dict['axes_y'] = closest_y
        self._dict['axes_y:unit'] = y_unit
        self._dict['flux'] = closest_y

        self.icon = closest_icon

        self.marks[viewer._reference_id].update_xy([closest_x], [closest_y])  # noqa
        self.marks[viewer._reference_id].visible = True
