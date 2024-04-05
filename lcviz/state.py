import numpy as np

from glue.viewers.scatter.state import ScatterViewerState

__all__ = ['ScatterViewerState']


class ScatterViewerState(ScatterViewerState):
    def _reset_att_limits(self, ax):
        # override glue's _reset_x/y_limits to account for all layers,
        # not just reference data
        att = f'{ax}_att'
        if getattr(self, att) is None:  # pragma: no cover
            return

        ax_min, ax_max = np.inf, -np.inf
        for layer in self.layers:
            ax_data = layer.layer.data.get_data(getattr(self, att))
            if len(ax_data) > 0:
                ax_min = min(ax_min, np.nanmin(ax_data))
                ax_max = max(ax_max, np.nanmax(ax_data))

        if not np.all(np.isfinite([ax_min, ax_max])):  # pragma: no cover
            return

        lim_helper = getattr(self, f'{ax}_lim_helper')
        lim_helper.lower = ax_min
        lim_helper.upper = ax_max
        lim_helper.update_values()

    def _reset_x_limits(self, *event):
        self._reset_att_limits('x')

    def _reset_y_limits(self, *event):
        self._reset_att_limits('y')

    def reset_limits(self, *event):
        x_min, x_max = np.inf, -np.inf
        y_min, y_max = np.inf, -np.inf

        for layer in self.layers:
            if not layer.visible:  # pragma: no cover
                continue

            x_data = layer.layer.data.get_data(self.x_att)
            y_data = layer.layer.data.get_data(self.y_att)

            x_min = min(x_min, np.nanmin(x_data))
            x_max = max(x_max, np.nanmax(x_data))
            y_min = min(y_min, np.nanmin(y_data))
            y_max = max(y_max, np.nanmax(y_data))

        x_lim_helper = getattr(self, 'x_lim_helper')
        x_lim_helper.lower = x_min
        x_lim_helper.upper = x_max

        y_lim_helper = getattr(self, 'y_lim_helper')
        y_lim_helper.lower = y_min
        y_lim_helper.upper = y_max

        x_lim_helper.update_values()
        y_lim_helper.update_values()

        self._adjust_limits_aspect()
