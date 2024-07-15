import os
from glue.config import data_translator
from jdaviz.core.registries import data_parser_registry
import lightkurve

from lcviz.viewers import PhaseScatterView, TimeScatterView
from lcviz.plugins.plot_options import PlotOptions

__all__ = ["light_curve_parser"]

mission_sub_intervals = {
    'kepler': {'prefix': 'Q', 'card': 'QUARTER'},
    'k2': {'prefix': 'C', 'card': 'CAMPAIGN'},
    'tess': {'prefix': 'S', 'card': 'SECTOR'},
}


@data_parser_registry("light_curve_parser")
def light_curve_parser(app, file_obj, data_label=None, show_in_viewer=True, **kwargs):
    # load a LightCurve or TargetPixelFile object:
    cls_with_translator = (
        lightkurve.LightCurve,
        lightkurve.targetpixelfile.KeplerTargetPixelFile,
        lightkurve.targetpixelfile.TessTargetPixelFile
    )

    # load local FITS file from disk by its path:
    if isinstance(file_obj, str) and os.path.exists(file_obj):
        if data_label is None:
            data_label = os.path.splitext(os.path.basename(file_obj))[0]

        # read the light curve:
        light_curve = lightkurve.read(file_obj)

    elif isinstance(file_obj, cls_with_translator):
        light_curve = file_obj
    else:
        raise NotImplementedError(f"could not parse light_curve with type {type(file_obj)}")

    # handle flux_origin default
    mission = light_curve.meta.get('MISSION', '').lower()
    flux_origin = light_curve.meta.get('FLUX_ORIGIN', None)  # i.e. PDCSAP or SAP

    # make a data label:
    if data_label is None:
        data_label = light_curve.meta.get('OBJECT', 'Light curve')

        if isinstance(light_curve, lightkurve.targetpixelfile.TargetPixelFile):
            data_label += '[TPF]'
        elif mission in mission_sub_intervals:
            # the sub-interval label is something like "Q9" for Kepler or
            # "S9" for TESS. If it's already in the proposed data label, skip;
            # otherwise, append it.
            sub_interval_label = (
                f' [{mission_sub_intervals[mission]["prefix"]}'
                f'{light_curve.meta.get(mission_sub_intervals[mission]["card"])}]'
            )
            data_label += sub_interval_label

    if flux_origin == 'flux' or (flux_origin is None and 'flux' in getattr(light_curve, 'columns', [])):  # noqa
        # then make a copy of this column so it won't be lost when changing with the flux_column
        # plugin
        light_curve['flux:orig'] = light_curve['flux']
        if 'flux_err' in light_curve.columns:
            light_curve['flux:orig_err'] = light_curve['flux_err']
        light_curve.meta['FLUX_ORIGIN'] = 'flux:orig'

    if 'FILENAME' in light_curve.meta:
        light_curve.meta['FILENAME'] = os.path.basename(light_curve.meta['FILENAME'])

    data = _data_with_reftime(app, light_curve)
    app.add_data(data, data_label)

    if isinstance(light_curve, lightkurve.targetpixelfile.TargetPixelFile):
        # ensure an image/cube/TPF viewer exists
        # TODO: move this to an event listener on add_data so that we can also remove when empty?
        from jdaviz.core.events import NewViewerMessage
        from lcviz.viewers import CubeView
        if show_in_viewer:
            found_viewer = False
            for viewer_id, viewer in app._viewer_store.items():
                if isinstance(viewer, CubeView):
                    app.add_data_to_viewer(viewer_id, data_label)
                    found_viewer = True
            if not found_viewer:
                app._on_new_viewer(NewViewerMessage(CubeView, data=None, sender=app),
                                   vid='image', name='image')
                app.add_data_to_viewer('image', data_label)

        # set TPF viewer's stretch to custom defaults:
        plot_options_plugin = PlotOptions(app=app)
        if plot_options_plugin is not None:
            plot_options_plugin._default_tpf_stretch()

    else:
        if show_in_viewer:
            for viewer_id, viewer in app._viewer_store.items():
                if isinstance(viewer, (TimeScatterView, PhaseScatterView)):
                    app.add_data_to_viewer(viewer_id, data_label)

            # add to any known phase viewers
            ephem_plugin = app._jdaviz_helper.plugins.get('Ephemeris', None)
            if ephem_plugin is not None:
                for viewer in ephem_plugin._obj._get_phase_viewers():
                    app.add_data_to_viewer(viewer.reference, data_label)


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
