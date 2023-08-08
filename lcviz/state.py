from echo import delay_callback
import numpy as np

from glue.viewers.scatter.state import ScatterViewerState

__all__ = ['ScatterViewerState']


class ScatterViewerState(ScatterViewerState):
    def _reset_att_limits(self, ax):
        # override glue's _reset_x/y_limits to account for all layers,
        # not just reference data
        att = f'{ax}_att'
        if getattr(self, att) is None:
            return

        ax_min, ax_max = np.inf, -np.inf
        for layer in self.layers:
            ax_data = layer.layer.data.get_data(getattr(self, att))
            if len(ax_data) > 0:
                ax_min = min(ax_min, np.nanmin(ax_data))
                ax_max = max(ax_max, np.nanmax(ax_data))

        if not np.all(np.isfinite([ax_min, ax_max])):
            return

        with delay_callback(self, f'{ax}_min', f'{ax}_max'):
            setattr(self, f'{ax}_min', ax_min)
            setattr(self, f'{ax}_max', ax_max)

    def _reset_x_limit(self, *event):
        self._reset_att_limits('x')

    def _reset_y_limits(self, *event):
        self._reset_att_limits('y')

    def reset_limits(self, *event):
        x_min, x_max = np.inf, -np.inf
        y_min, y_max = np.inf, -np.inf

        for layer in self.layers:
            if not layer.visible:
                continue

            x_data = layer.layer.data.get_data(self.x_att)
            y_data = layer.layer.data.get_data(self.y_att)

            x_min = min(x_min, np.nanmin(x_data))
            x_max = max(x_max, np.nanmax(x_data))
            y_min = min(y_min, np.nanmin(y_data))
            y_max = max(y_max, np.nanmax(y_data))

        with delay_callback(self, 'x_min', 'x_max', 'y_min', 'y_max'):
            self.x_min = x_min
            self.x_max = x_max
            self.y_min = y_min
            self.y_max = y_max
            # We need to adjust the limits in here to avoid triggering all
            # the update events then changing the limits again.
            self._adjust_limits_aspect()
