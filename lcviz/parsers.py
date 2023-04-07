from jdaviz.core.registries import data_parser_registry
from specutils import Spectrum1D

__all__ = ["lcviz_manual_data_parser"]


@data_parser_registry("lcviz_manual_data_parser")
def lcviz_manual_data_parser(app, data, data_label=None, show_in_viewer=True):
    time_viewer_reference_name = app._jdaviz_helper._default_time_viewer_reference_name

    data._preferred_translation = True  # Triggers custom viewer.set_plot_axes()

    app.add_data(data, data_label)
    app.add_data_to_viewer(time_viewer_reference_name, data_label)
