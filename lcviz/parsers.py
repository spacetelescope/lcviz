import os
from astropy.io import fits
from glue.core.link_helpers import LinkSame
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

    app.add_data(light_curve, new_data_label)
    dc = app.data_collection
    if len(dc) > 1:
        # then we need to link this light curve back to the first
        dc0_comps = {str(comp): comp for comp in dc[0].components}
        new_links = [LinkSame(dc0_comps.get(str(new_comp)), new_comp) for new_comp in dc[-1].components]
        dc.set_links(new_links)

    if show_in_viewer:
        app.add_data_to_viewer(time_viewer_reference_name, new_data_label)
