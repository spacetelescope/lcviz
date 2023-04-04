from astropy import units as u

from glue.core import BaseData

from glue_jupyter.bqplot.profile import BqplotProfileView

from jdaviz.core.registries import viewer_registry
from jdaviz.configs.default.plugins.viewers import JdavizViewerMixin

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

        #TBF: Temp comps until actual glue-astronomy translators are developed
        x_component = 'x'
        y_component = 'flux'

        x_unit = u.Unit(data.get_component(x_component).units)
        self.figure.axes[0].label = f'{str(x_unit.physical_type).title()} ({x_unit})'

        y_unit = u.Unit(data.get_component(y_component).units)
        self.figure.axes[1].label = f'{str(y_unit.physical_type).title()} ({y_unit})'
        
        # Make it so y axis label is not covering tick numbers.
        self.figure.axes[1].label_offset = "-50"

        # Set Y-axis to scientific notation
        self.figure.axes[1].tick_format = '0.1e'
