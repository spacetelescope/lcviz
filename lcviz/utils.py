from glue.config import data_translator
from glue.core import Data, Subset
from ipyvue import watch

import os
from glue.core.coordinates import Coordinates
import numpy as np
from astropy import units as u
from astropy.table import QTable
from astropy.time import Time

from lightkurve import (
    LightCurve, KeplerLightCurve, TessLightCurve
)

__all__ = ['TimeCoordinates', 'LightCurveHandler']


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
        self._values = delta_t

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
        return tuple(self._values.unit.to_string('vounit'))

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
        time_coord = TimeCoordinates(obj.time)
        delta_t = (obj.time - obj.time[0]).to(u.d)
        data = Data(coords=time_coord)

        if hasattr(obj, 'label'):
            data.label = obj.label

        data.meta.update(obj.meta)
        data.meta.update({"reference_time": obj.time[0]})

        data['dt'] = delta_t
        data.get_component('dt').units = str(delta_t.unit)

        # LightCurve is a subclass of astropy TimeSeries, so
        # collect all other columns in the TimeSeries:
        for component_label in obj.colnames:
            component_data = getattr(obj, component_label)
            data[component_label] = component_data
            if hasattr(component_data, 'unit'):
                data.get_component(component_label).units = str(component_data.unit)

        data.meta.update({'uncertainty_type': 'std'})

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
            component = data.get_component(component_id)

            values = component.data[glue_mask]

            if isinstance(values[0], Time):
                values = Time(values.base)
            elif hasattr(component, 'units') and component.units != "None":
                values = u.Quantity(values, component.units)

            columns.append(values)
            names.append(component_id.label)

        table = QTable(columns, names=names, masked=True, copy=False)
        return LightCurve(table, **kwargs)


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
