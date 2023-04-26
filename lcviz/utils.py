import datetime
from glue.config import data_translator
from glue.core import Data, Subset
from ipyvue import watch

import os
from lightkurve import LightCurve
from ndcube.extra_coords import TimeTableCoordinate
from glue.core.coordinates import Coordinates
import numpy as np
from gwcs.wcs import WCS

from astropy import units as u
from astropy.time import Time
from astropy.utils.masked import Masked
from lightkurve import LightCurve

__all__ = ['TimeCoordinates']


class TimeCoordinates(Coordinates):
    """
    This is a sub-class of Coordinates that is intended for a time axis
    given by a :class:`~astropy.time.Time` array.
    """

    def __init__(self, times, reference_time=None, unit=u.d):
        if not isinstance(times, Time):
            raise TypeError('values should be a Time instance')
        self._index = np.arange(len(times))
        self._times = times

        # convert to relative time units
        if reference_time is None:
            self.reference_time = times[0]

        delta_t = (times - self.reference_time).to(unit)
        self._values = delta_t # times.datetime64

        # self._values = (
        #     times.datetime64.astype(datetime.datetime).astype(int) / 1e9 * u.day
        # )

        super().__init__(n_dim=1)

    @property
    def time_axis(self):
        """
        Returns
        -------
        """
        return self._times

    @property
    def world_axis_units(self):
        return (self._values.unit.to_string('vounit'),)

    def world_to_pixel_values(self, *world):
        """
        Parameters
        ----------
        world
        Returns
        -------
        """
        if len(world) > 1:
            raise ValueError('TimeCoordinates is a 1-d coordinate class '
                             'and only accepts a single scalar or array to convert')
        return np.interp(world[0], self._values.value, self._index,
                         left=np.nan, right=np.nan)

    def pixel_to_world_values(self, *pixel):
        """
        Parameters
        ----------
        pixel
        Returns
        -------
        """
        if len(pixel) > 1:
            raise ValueError('SpectralCoordinates is a 1-d coordinate class '
                             'and only accepts a single scalar or array to convert')
        return np.interp(pixel[0], self._index, self._values.value,
                         left=np.nan, right=np.nan)


__all__ = ['LightCurveHandler', 'enable_hot_reloading']


@data_translator(LightCurve)
class LightCurveHandler:

    def to_data(self, obj):
        time = obj.time
        # ttc = TimeTableCoordinate(time)
        # gwcs = ttc.wcs
        time_coord = TimeCoordinates(obj.time)
        # delta_t = (obj.time - obj.time[0]).to(u.d)
        data = Data(coords=time_coord)

        data.meta.update(obj.meta)
        data.meta.update({"reference_time": obj.time[0]})

        flux = obj.flux
        flux_err = obj.flux_err

        if hasattr(flux, 'unmasked'):
            flux = flux.unmasked
            flux_err = obj.flux_err.unmasked

        data['flux'] = flux
        data.get_component('flux').units = str(flux.unit)

        data['uncertainty'] = flux_err
        data.get_component('uncertainty').units = str(flux_err.unit)
        data.meta.update({'uncertainty_type': 'std'})

        return data

    def to_object(self, data_or_subset, attribute=None):
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

        # convert gwcs coordinates to Time object.

        # ``gwcs`` will store the transformation from pixel coordinates, which are
        # integer indices in the input time object, to astropy.time.Time objects.
        # Here we extract the time coordinates directly from the lookup table:
        reference_time = data.meta['reference_time']

        if isinstance(data.coords, WCS):
            gwcs = data.coords
            input_times = gwcs._pipeline[0].transform.lookup_table
            kwargs['time'] = input_times + reference_time
        else:
            kwargs['time'] = data.coords.time_axis

        if isinstance(attribute, str):
            attribute = data.id[attribute]
        elif len(data.main_components) == 0:
            raise ValueError('Data object has no attributes.')
        elif attribute is None:
            if len(data.main_components) == 1:
                attribute = data.main_components[0]
            # If no specific attribute is defined, attempt to retrieve
            # the flux and uncertainty, if available
            elif any([x.label in ('flux', 'uncertainty') for x in data.components]):
                attribute = [data.find_component_id(x)
                             for x in ('flux', 'uncertainty')
                             if data.find_component_id(x) is not None]
            else:
                raise ValueError("Data object has more than one attribute, so "
                                 "you will need to specify which one to use as "
                                 "the flux for the spectrum using the "
                                 "attribute= keyword argument.")
        print('attributes', attribute)
        def parse_attributes(attributes):
            data_kwargs = {}
            lc_init_keys = {'flux': 'flux', 'uncertainty': 'flux_err'}
            for attribute in attributes:
                component = data.get_component(attribute)

                # Get mask if there is one defined, or if this is a subset
                if subset_state is None:
                    mask = None
                else:
                    mask = data.get_mask(subset_state=subset_state)
                    # mask = ~mask
                print('mask', mask, np.any(mask))
                # Collapse values and mask to profile
                values = data.get_data(attribute)
                attribute_label = attribute.label

                if attribute in ('flux', 'uncertainty'):
                    values = u.Quantity(values, unit=component.units)

                init_kwarg = lc_init_keys[attribute_label]
                data_kwargs.update({init_kwarg: values})

            return data_kwargs

        data_kwargs = parse_attributes(
            [attribute] if not hasattr(attribute, '__len__') else attribute)
        return LightCurve(**data_kwargs, **kwargs)


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
