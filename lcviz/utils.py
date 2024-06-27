from glue.config import data_translator
from glue.core import Data, Subset
from ipyvue import watch
import warnings

import os
from glue.core.coordinates import Coordinates
from glue.core.component_id import ComponentID
import numpy as np
from scipy.interpolate import interp1d

from lightkurve import (
    LightCurve, KeplerLightCurve, TessLightCurve, FoldedLightCurve
)
from lightkurve.targetpixelfile import (
    KeplerTargetPixelFile, TessTargetPixelFile, TargetPixelFileFactory
)
from lightkurve.utils import KeplerQualityFlags, TessQualityFlags

from astropy import units as u
from astropy.table import QTable
from astropy.time import Time
from astropy.wcs.wcsapi.wrappers.base import BaseWCSWrapper
from astropy.wcs.wcsapi import HighLevelWCSMixin

__all__ = ['TimeCoordinates', 'LightCurveHandler',
           'data_not_folded', 'is_tpf', 'is_not_tpf',
           'enable_hot_reloading']


component_ids = {'dt': ComponentID('dt')}


class TimeCoordinates(Coordinates):
    """
    This is a sub-class of Coordinates that is intended for a time axis
    given by a :class:`~astropy.time.Time` array.
    """

    def __init__(self, times, reference_time=None, unit=u.d):
        if not isinstance(times, Time):  # pragma: no cover
            raise TypeError('values should be a Time instance')
        self._index = np.arange(len(times))
        self._times = times
        self.unit = unit

        # convert to relative time units
        self.reference_time = reference_time
        if self.reference_time is None:
            self.reference_time = times[0]
        self._values = (times - self.reference_time).to(unit)

        super().__init__(n_dim=1)

    @property
    def time_axis(self):
        return self._times

    def world_to_pixel_values(self, *world):
        if len(world) > 1:  # pragma: no cover
            raise ValueError('TimeCoordinates is a 1-d coordinate class '
                             'and only accepts a single scalar or array to convert')
        return interp1d(
            self._values.value, self._index, fill_value='extrapolate'
        )(world[0])

    def pixel_to_world_values(self, *pixel):
        if len(pixel) > 1:  # pragma: no cover
            raise ValueError('SpectralCoordinates is a 1-d coordinate class '
                             'and only accepts a single scalar or array to convert')
        return interp1d(
            self._index, self._values.value, fill_value='extrapolate'
        )(pixel[0])


class PaddedTimeWCS(BaseWCSWrapper, HighLevelWCSMixin):

    # Spectrum1D can use a 1D spectral WCS even for n-dimensional
    # datasets while glue always needs the dimensionality to match,
    # so this class pads the WCS so that it is n-dimensional.

    # NOTE: This class could be updated to use CompoundLowLevelWCS from NDCube.

    def __init__(self, wcs, times, ndim=3, reference_time=None, unit=u.d):
        self.temporal_wcs = TimeCoordinates(
            times, reference_time=reference_time, unit=unit
        )
        self.spatial_wcs = wcs
        self.flux_ndim = ndim
        self.spatial_keys = [f"spatial{i}" for i in range(0, self.flux_ndim-1)]

    @property
    def time_axis(self):
        return self.temporal_wcs.time_axis

    @property
    def pixel_n_dim(self):
        return self.flux_ndim

    @property
    def world_n_dim(self):
        return self.flux_ndim

    @property
    def world_axis_physical_types(self):
        return [self.temporal_wcs.world_axis_physical_types[0], *[None]*(self.flux_ndim-1)]

    @property
    def world_axis_units(self):
        return (self.temporal_wcs.world_axis_units[0], *[None]*(self.flux_ndim-1))

    def pixel_to_world_values(self, *pixel_arrays):
        # The ravel and reshape are needed because of
        # https://github.com/astropy/astropy/issues/12154
        px = np.array(pixel_arrays[0])
        world_arrays = [self.temporal_wcs.pixel_to_world_values(px.ravel()).reshape(px.shape),
                        *pixel_arrays[1:]]
        return tuple(world_arrays)

    def world_to_pixel_values(self, *world_arrays):
        # The ravel and reshape are needed because of
        # https://github.com/astropy/astropy/issues/12154
        wx = np.array(world_arrays[0])
        pixel_arrays = [self.temporal_wcs.world_to_pixel_values(wx.ravel()).reshape(wx.shape),
                        *world_arrays[1:]]
        return tuple(pixel_arrays)

    @property
    def world_axis_object_components(self):
        return [self.temporal_wcs.world_axis_object_components[0],
                *[(key, 'value', 'value') for key in self.spatial_keys]]

    @property
    def world_axis_object_classes(self):
        spectral_key = self.temporal_wcs.world_axis_object_components[0][0]
        obj_classes = {spectral_key: self.temporal_wcs.world_axis_object_classes[spectral_key]}
        for key in self.spatial_keys:
            obj_classes[key] = (u.Quantity, (), {'unit': u.pixel})

        return obj_classes

    @property
    def pixel_shape(self):
        return None

    @property
    def pixel_bounds(self):
        return None

    @property
    def pixel_axis_names(self):
        return tuple([self.temporal_wcs.pixel_axis_names[0], *self.spatial_keys])

    @property
    def world_axis_names(self):
        if self.flux_ndim == 2:
            names = ['Offset']
        else:
            names = [f"Offset{i}" for i in range(0, self.flux_ndim-1)]

        return ({}.get(self.temporal_wcs.world_axis_physical_types[0], ''),
                *names)

    @property
    def axis_correlation_matrix(self):
        return np.identity(self.flux_ndim).astype('bool')

    @property
    def serialized_classes(self):
        return False


@data_translator(LightCurve)
class LightCurveHandler:

    def to_data(self, obj, reference_time=None):
        is_folded = isinstance(obj, FoldedLightCurve)
        time = obj.time_original if is_folded and hasattr(obj, 'time_original') else obj.time
        time_coord = TimeCoordinates(time, reference_time=reference_time)
        data = Data(coords=time_coord)

        if hasattr(obj, 'label'):
            data.label = obj.label

        data.meta.update(obj.meta)
        data.meta.update(
            {"reference_time": time_coord.reference_time}
        )
        data[component_ids['dt']] = (obj.time - time_coord.reference_time).to(time_coord.unit)
        data.get_component('dt').units = str(time_coord.unit)

        # LightCurve is a subclass of astropy TimeSeries, so
        # collect all other columns in the TimeSeries:
        for component_label in obj.colnames:

            component_data = getattr(obj, component_label)
            if is_folded and component_label == 'time':
                ephem_comp = obj.meta.get('_LCVIZ_EPHEMERIS', {}).get('ephemeris')
                if ephem_comp is None:
                    continue
                component_label = f'phase:{ephem_comp}'

            if component_label not in component_ids:
                component_ids[component_label] = ComponentID(component_label)
            cid = component_ids[component_label]

            data[cid] = component_data
            if hasattr(component_data, 'unit'):
                try:
                    data.get_component(cid).units = str(component_data.unit)
                except KeyError:  # pragma: no cover
                    continue

        data.meta.update({'uncertainty_type': 'std'})

        # if the anticipated x and y axes are the first two components in the
        # Data object, the viewer will load those components correctly before
        # you hit the call to `viewer.set_plot_axes`:
        reordered_components = {comp.label: comp for comp in data.components}
        dt_comp = reordered_components.pop('dt')
        flux_comp = reordered_components.pop('flux')
        data.reorder_components(
            [dt_comp, flux_comp] +
            list(reordered_components.values())
        )

        return data

    def to_object(self, data_or_subset):
        """
        Convert a glue Data object to a lightkurve.LightCurve object.

        Parameters
        ----------
        data_or_subset : `glue.core.data.Data` or `glue.core.subset.Subset`
            The data to convert to a LightCurve object
        attribute : `glue.core.component_id.ComponentID`
            The attribute to use for the LightCurve data
        """

        if isinstance(data_or_subset, Subset):
            data = data_or_subset.data
            subset_state = data_or_subset.subset_state
        else:
            data = data_or_subset
            subset_state = None

        # Copy over metadata
        kwargs = {'meta': data.meta.copy()}

        # extract a Time object out of the TimeCoordinates object:
        time = data.coords.time_axis

        if subset_state is None:
            # pass through mask of all True's if no glue subset is chosen
            glue_mask = np.ones(len(time)).astype(bool)
        else:
            # get the subset mask from glue:
            glue_mask = data.get_mask(subset_state=subset_state)
            # apply the subset mask to the time array:
            time = time[glue_mask]

        columns = [time]
        names = ['time']

        component_ids = data.main_components

        # we already handled time separately above, and `dt` is only used internally
        # in LCviz, so let's skip those IDs below:
        skip_components = [id for id in component_ids if id.label in ['time', 'dt']]
        for skip_comp in skip_components:
            component_ids.remove(skip_comp)

        for component_id in component_ids:
            if component_id.label in names:
                # avoid duplicate column
                continue
            component = data.get_component(component_id)

            values = component.data[glue_mask]

            if len(values) and isinstance(values[0], Time):
                values = Time(values.base)
            elif hasattr(component, 'units') and component.units != "None":
                try:
                    values = u.Quantity(values, component.units)
                except TypeError:
                    if component.units != "":
                        raise
                    # values could have been an array of strings with units ""
                    values = values

            if component_id.label not in names:
                columns.append(values)
                names.append(component_id.label)

        table = QTable(columns, names=names, masked=True, copy=False)
        return LightCurve(table, **kwargs)


class TPFHandler:
    quality_flag_cls = None
    tpf_attrs = ['flux', 'flux_bkg', 'flux_bkg_err', 'flux_err']
    meta_attrs = [
        'cadenceno',
        'campaign',
        'channel',
        'column',
        'dec',
        'hdu',
        'mission',
        'module',
        'nan_time_mask',
        'obsmode',
        'output',
        'pipeline_mask',
        'pos_corr1',
        'pos_corr2',
        'quality',
        'quarter',
        'ra',
        'row',
        'shape',
        'wcs'
    ]

    def to_data(self, obj, reference_time=None, unit=u.d):
        coords = PaddedTimeWCS(obj.wcs, obj.time, reference_time=reference_time, unit=unit)
        data = Data(coords=coords)

        flux_shape = obj.flux.shape

        if hasattr(obj, 'label'):
            data.label = obj.label

        data.meta.update(obj.meta)
        data.meta.update(
            {"reference_time": coords.temporal_wcs.reference_time}
        )

        data[component_ids['dt']] = np.broadcast_to(
            (
                obj.time - coords.temporal_wcs.reference_time
            ).to(coords.temporal_wcs.unit)[:, None, None], flux_shape
        )
        data.get_component('dt').units = str(coords.temporal_wcs.unit)

        # LightCurve is a subclass of astropy TimeSeries, so
        # collect all other columns in the TimeSeries:
        for component_label in self.tpf_attrs:

            component_data = getattr(obj, component_label)
            if component_label not in component_ids:
                component_ids[component_label] = ComponentID(component_label)
            cid = component_ids[component_label]

            data[cid] = component_data
            if hasattr(component_data, 'unit'):
                try:
                    data.get_component(cid).units = str(component_data.unit)
                except KeyError:  # pragma: no cover
                    continue

        data.meta.update({'uncertainty_type': 'std'})

        for attr in self.meta_attrs:
            value = getattr(obj, attr, None)
            data.meta.update({attr: value})

        # if the anticipated x and y axes are the first two components in the
        # Data object, the viewer will load those components correctly before
        # you hit the call to `viewer.set_plot_axes`:
        reordered_components = {comp.label: comp for comp in data.components}
        dt_comp = reordered_components.pop('dt')
        flux_comp = reordered_components.pop('flux')
        data.reorder_components(
            [dt_comp, flux_comp] +
            list(reordered_components.values())
        )

        return data

    def to_object(self, data_or_subset):
        """
        Convert a glue Data object to a lightkurve.KeplerTargetPixelFile object.

        Parameters
        ----------
        data_or_subset : `glue.core.data.Data` or `glue.core.subset.Subset`
            The data to convert to a KeplerTargetPixelFile object
        attribute : `glue.core.component_id.ComponentID`
            The attribute to use for the KeplerTargetPixelFile data
        """

        if isinstance(data_or_subset, Subset):
            data = data_or_subset.data
            subset_state = data_or_subset.subset_state
        else:
            data = data_or_subset
            subset_state = None

        # Copy over metadata

        meta = data.meta.copy()
        for attr in self.meta_attrs:
            # these attrs don't belong in the lightkurve object's meta:
            meta.pop(attr)

        # extract a Time object out of the TimeCoordinates object:
        time = data.coords.time_axis

        if subset_state is None:
            # pass through mask of all True's if no glue subset is chosen
            glue_mask = None
        else:
            # get the subset mask from glue:
            glue_mask = data.get_mask(subset_state=subset_state)
            # apply the subset mask to the time array:
            time = time[glue_mask]

        attrs_to_save = {'meta': meta, 'time': time}

        component_ids = data.main_components

        # we already handled time separately above, and `dt` is only used internally
        # in LCviz, so let's skip those IDs below:
        skip_components = [id for id in component_ids if id.label in ['time', 'dt']]
        for skip_comp in skip_components:
            component_ids.remove(skip_comp)

        for component_id in component_ids:
            if component_id.label in attrs_to_save:
                # avoid duplicate column
                continue
            component = data.get_component(component_id)
            values = component.data
            if glue_mask is not None:
                values = values[glue_mask]

            if component_id.label not in attrs_to_save:
                attrs_to_save[component_id.label] = values

        tpf_factory = TargetPixelFileFactory(*data.shape)

        for attr, values in attrs_to_save.items():
            if attr == 'time':
                values = values.value
            setattr(tpf_factory, attr, values)

        with warnings.catch_warnings():
            warnings.filterwarnings('ignore',
                                    message='Could not detect filetype as TESSTargetPixelFile or KeplerTargetPixelFile, returning generic TargetPixelFile instead.')  # noqa
            tpf = tpf_factory.get_tpf()

        for attr in self.meta_attrs:
            # if this attribute exists and can be set:
            if hasattr(tpf, attr) and getattr(getattr(tpf, attr), 'fset', None) is not None:
                setattr(tpf, attr, data.meta[attr])

        tpf.quality_mask = self.quality_flag_cls.create_quality_mask(
            quality_array=tpf.hdu[1].data["QUALITY"], bitmask=tpf.quality_bitmask
        )

        return tpf


def enable_hot_reloading(watch_jdaviz=True):
    """
    Use ``watchdog`` to perform hot reloading.

    Parameters
    ----------
    watch_jdaviz : bool
        Whether to also watch changes to jdaviz upstream.
    """
    try:
        watch(os.path.dirname(__file__))
        if watch_jdaviz:
            import jdaviz
            watch(os.path.dirname(jdaviz.__file__))
    except ModuleNotFoundError:
        print((
            'Watchdog module, needed for hot reloading, not found.'
            ' Please install with `pip install watchdog`'))


@data_translator(KeplerLightCurve)
class KeplerLightCurveHandler(LightCurveHandler):
    # Works the same as LightCurve
    pass


@data_translator(TessLightCurve)
class TessLightCurveHandler(LightCurveHandler):
    # Works the same as LightCurve
    pass


@data_translator(KeplerTargetPixelFile)
class KeplerTPFHandler(TPFHandler):
    quality_flag_cls = KeplerQualityFlags


@data_translator(TessTargetPixelFile)
class TessTPFHandler(TPFHandler):
    quality_flag_cls = TessQualityFlags


# plugin component filters
def data_not_folded(data):
    return data.meta.get('_LCVIZ_EPHEMERIS', None) is None


def is_tpf(data):
    return len(data.shape) == 3


def is_not_tpf(data):
    return not is_tpf(data)
