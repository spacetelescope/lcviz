import os
from astropy.io import fits
from jdaviz.core.registries import data_parser_registry
from lightkurve import LightCurve, KeplerLightCurve, TessLightCurve
from lightkurve.io.detect import detect_filetype

__all__ = ["light_curve_parser"]


@data_parser_registry("light_curve_parser")
def light_curve_parser(app, file_obj, data_label=None, show_in_viewer=True, **kwargs):
    time_viewer_reference_name = app._jdaviz_helper._default_time_viewer_reference_name

    if isinstance(file_obj, str) and os.path.exists(file_obj):
        if data_label is None:
            data_label = os.path.splitext(os.path.basename(file_obj))[0]

        # detect the type light curve in a FITS file:
        filetype = detect_filetype(fits.open(file_obj))
        # get the constructor for this type of light curve:
        filetype_to_cls = {
            'KeplerLightCurve': KeplerLightCurve,
            'TessLightCurve': TessLightCurve
        }
        cls = filetype_to_cls[filetype]
        # read the light curve:
        light_curve = cls.read(file_obj)

    elif isinstance(file_obj, LightCurve):
        light_curve = file_obj

    # make a data label:
    if data_label is not None:
        new_data_label = f'{data_label}'
    else:
        new_data_label = light_curve.meta.get('OBJECT', 'Light curve')
    flux_origin = light_curve.meta.get('FLUX_ORIGIN', None)  # i.e. PDCSAP or SAP
    if flux_origin is not None:
        new_data_label += f'[{flux_origin}]'

    app.add_data(light_curve, new_data_label)

    if show_in_viewer:
        app.add_data_to_viewer(time_viewer_reference_name, new_data_label)
