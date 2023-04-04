from jdaviz.core.registries import data_parser_registry
from specutils import Spectrum1D

__all__ = ["lcviz_dummy_parser", "lcviz_manual_data_parser"]

@data_parser_registry("lcviz_dummy_parser")
def lcviz_dummy_parser(app, data, data_label=None):
    """
    A dummy parser to verify registering an external parser.

    Takes a Spectrum1D and multiplies the spectral_axis by 1000

    Parameters
    ----------
    data : str, `~specutils.Spectrum1D`
        A Spectrum1D
    data_label : str
        The Glue data label found in the ``DataCollection``.
    """

    spectrum_viewer_reference_name = app._jdaviz_helper._default_spectrum_viewer_reference_name

    if not isinstance(data, Spectrum1D):
        raise ValueError("Only Spectrum1Ds are accepted")

    parsed_data = Spectrum1D(flux=data.flux, spectral_axis=data.spectral_axis*1000)

    app.add_data(parsed_data, data_label)
    app.add_data_to_viewer(spectrum_viewer_reference_name, data_label)


@data_parser_registry("lcviz_manual_data_parser")
def lcviz_manual_data_parser(app, data, data_label=None, show_in_viewer=True):
    time_viewer_reference_name = app._jdaviz_helper._default_time_viewer_reference_name

    data._preferred_translation = True  # Triggers custom viewer.set_plot_axes()

    app.add_data(data, data_label)
    app.add_data_to_viewer(time_viewer_reference_name, data_label)
