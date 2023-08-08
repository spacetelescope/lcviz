import os
from astropy.io import fits
from glue.config import data_translator
from jdaviz.core.registries import data_parser_registry
from lightkurve import LightCurve, KeplerLightCurve, TessLightCurve
from lightkurve.io.detect import detect_filetype

__all__ = ["light_curve_parser"]


@data_parser_registry("light_curve_parser")
def light_curve_parser(app, file_obj, data_label=None, show_in_viewer=True, **kwargs):
    time_viewer_reference_name = app._jdaviz_helper._default_time_viewer_reference_name

    # load local FITS file from disk by its path:
    if isinstance(file_obj, str) and os.path.exists(file_obj):
        if data_label is None:
            data_label = os.path.splitext(os.path.basename(file_obj))[0]

        # detect the type light curve in a FITS file:
        with fits.open(file_obj) as hdulist:
            filetype = detect_filetype(hdulist)

        # get the constructor for this type of light curve:
        filetype_to_cls = {
            'KeplerLightCurve': KeplerLightCurve,
            'TessLightCurve': TessLightCurve
        }
        cls = filetype_to_cls[filetype]
        # read the light curve:
        light_curve = cls.read(file_obj)

    # load a LightCurve object:
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

    data = _data_with_reftime(app, light_curve)
    app.add_data(data, new_data_label)

    if show_in_viewer:
        app.add_data_to_viewer(time_viewer_reference_name, new_data_label)

        # add to any known phase viewers
        ephem_plugin = app._jdaviz_helper.plugins.get('Ephemeris', None)
        if ephem_plugin is not None:
            for viewer_id in ephem_plugin._obj.phase_viewer_ids:
                app.add_data_to_viewer(viewer_id, new_data_label)


def _data_with_reftime(app, light_curve):
    # grab the first-found reference time in the data collection:
    ff_reference_time = None
    for existing_data in app.data_collection:
        if hasattr(existing_data, 'meta') and 'reference_time' in existing_data.meta:
            ff_reference_time = existing_data.meta.get('reference_time', None)
            if ff_reference_time is not None:
                break

    # convert to glue Data manually, so we may edit the `dt` component if necessary:
    handler, _ = data_translator.get_handler_for(light_curve)
    return handler.to_data(light_curve, reference_time=ff_reference_time)
