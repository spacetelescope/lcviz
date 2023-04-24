from astropy import units as u

from glue.core import BaseData

from glue_jupyter.bqplot.profile import BqplotProfileView

from jdaviz.core.registries import viewer_registry
from jdaviz.configs.default.plugins.viewers import JdavizViewerMixin

__all__ = ['TimeProfileView']


@viewer_registry("lcviz-time-viewer", label="Profile 1D (LCviz)")
class TimeProfileView(JdavizViewerMixin, BqplotProfileView):
    # categories: zoom resets, zoom, pan, subset, select tools, shortcuts
    tools_nested = [
                    ['jdaviz:homezoom', 'jdaviz:prevzoom'],
                    ['jdaviz:boxzoom', 'jdaviz:xrangezoom'],
                    ['jdaviz:panzoom', 'jdaviz:panzoom_x', 'jdaviz:panzoom_y'],
                    ['bqplot:xrange'],
                    ['jdaviz:sidebar_plot', 'jdaviz:sidebar_export']
                ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initialize_toolbar()

    def data(self, cls=None):
        return [layer_state.layer
                for layer_state in self.state.layers
                if hasattr(layer_state, 'layer') and
                isinstance(layer_state.layer, BaseData)]

    def set_plot_axes(self):
        # Get data to be used for axes labels
        data = self.data()[0]

        # Get the lookup table from the time axis in the gwcs obj:
        lookup_table = data.coords._pipeline[0].transform.lookup_table
        x_unit = lookup_table.unit
        reference_time = data.meta.get('reference_time', None)

        if reference_time is not None:
            xlabel = f'{str(x_unit.physical_type).title()} from {reference_time.iso} ({x_unit})'
        else:
            xlabel = f'{str(x_unit.physical_type).title()} ({x_unit})'

        self.figure.axes[0].label = xlabel

        y_unit = u.Unit(data.get_component('flux').units)
        y_unit_physical_type = str(y_unit.physical_type).title()

        common_count_rate_units = (u.electron / u.s, u.dn / u.s, u.ct / u.s)

        if y_unit_physical_type == 'Unknown':
            if y_unit.is_equivalent(common_count_rate_units):
                y_unit_physical_type = 'Flux'
        if y_unit_physical_type == 'Dimensionless':
            y_unit_physical_type = 'Relative Flux'

        ylabel = f'{y_unit_physical_type}'

        if not y_unit.is_equivalent(u.dimensionless_unscaled):
            ylabel += f' ({y_unit})'

        self.figure.axes[1].label = ylabel

        # Make it so y axis label is not covering tick numbers (sometimes)
        self.figure.axes[1].label_offset = "-50"

        # Set (X,Y)-axis to scientific notation if necessary:
        self.figure.axes[0].tick_format = 'g'
        self.figure.axes[1].tick_format = 'g'
