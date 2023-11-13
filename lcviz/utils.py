from glue.config import data_translator
from glue.core import Data, Subset
from ipyvue import watch

import os
from glue.core.coordinates import Coordinates
from glue.core.component_id import ComponentID
import numpy as np
from scipy.interpolate import interp1d
from astropy import units as u
from astropy.table import QTable
from astropy.time import Time

from lightkurve import (
    LightCurve, KeplerLightCurve, TessLightCurve, FoldedLightCurve
)

__all__ = ['TimeCoordinates', 'LightCurveHandler', 'data_not_folded']


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


__all__ = ['LightCurveHandler', 'enable_hot_reloading']


@data_translator(LightCurve)
class LightCurveHandler:
    lc_component_ids = {}

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
        data['dt'] = (obj.time - time_coord.reference_time).to(time_coord.unit)
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

            if component_label not in self.lc_component_ids:
                self.lc_component_ids[component_label] = ComponentID(component_label)
            cid = self.lc_component_ids[component_label]

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
                values = u.Quantity(values, component.units)

            if component_id.label not in names:
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


# plugin component filters
def data_not_folded(data):
    return data.meta.get('_LCVIZ_EPHEMERIS', None) is None
