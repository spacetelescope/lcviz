from glue.config import data_translator
from glue.core import Data, Subset

from lightkurve import LightCurve
from ndcube.extra_coords import TimeTableCoordinate
from astropy import units as u
from astropy.utils.masked import Masked


@data_translator(LightCurve)
class LightCurveHandler:

    def to_data(self, obj):
        time = obj.time
        ttc = TimeTableCoordinate(time)
        gwcs = ttc.wcs

        data = Data(coords=gwcs)

        data.meta.update(obj.meta)
        data.meta.update({"reference_time": ttc.reference_time})

        data['flux'] = obj.flux
        data.get_component('flux').units = str(obj.flux.unit)

        data['uncertainty'] = obj.flux_err
        data.get_component('uncertainty').units = str(obj.flux_err.unit)
        data.meta.update({'uncertainty_type': 'std'})

        if hasattr(obj.flux, 'mask'):
            data['mask'] = obj.flux.mask
        return data

    def to_object(self, data_or_subset, attribute=None):
        """
        Convert a glue Data object to a lightkurve.LightCurve object.

        Parameters
        ----------
        data_or_subset : `glue.core.data.Data` or `glue.core.subset.Subset`
            The data to convert to a Spectrum1D object
        attribute : `glue.core.component_id.ComponentID`
            The attribute to use for the Spectrum1D data
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
        gwcs = data.coords
        reference_time = data.meta['reference_time']
        input_times = gwcs._pipeline[0].transform.lookup_table
        kwargs['time'] = input_times + reference_time

        if isinstance(attribute, str):
            attribute = data.id[attribute]
        elif len(data.main_components) == 0:
            raise ValueError('Data object has no attributes.')
        elif attribute is None:
            if len(data.main_components) == 1:
                attribute = data.main_components[0]
            # If no specific attribute is defined, attempt to retrieve
            # the flux and uncertainty, if available
            elif any([x.label in ('time', 'flux', 'uncertainty') for x in data.components]):
                attribute = [data.find_component_id(x)
                             for x in ('time', 'flux', 'uncertainty')
                             if data.find_component_id(x) is not None]
            else:
                raise ValueError("Data object has more than one attribute, so "
                                 "you will need to specify which one to use as "
                                 "the flux for the spectrum using the "
                                 "attribute= keyword argument.")

        def parse_attributes(attributes):
            data_kwargs = {}
            lc_init_keys = {'time': 'time', 'flux': 'flux', 'uncertainty': 'flux_err'}
            for attribute in attributes:
                component = data.get_component(attribute)

                # Collapse values and mask to profile
                values = data.get_data(attribute)
                attribute_label = attribute.label

                if attribute in ('flux', 'uncertainty'):
                    values = u.Quantity(values, unit=component.units)
                    if 'mask' in data.main_components:
                        mask = data['mask'].astype(bool)
                        values = Masked(values, mask)

                if subset_state is not None and attribute != 'mask':
                    glue_mask = data.get_mask(subset_state=subset_state)
                    values = Masked(values, ~glue_mask)

                init_kwarg = lc_init_keys[attribute_label]
                data_kwargs[init_kwarg] = values

            return data_kwargs

        data_kwargs = parse_attributes(
            [attribute] if not hasattr(attribute, '__len__') else attribute)
        return LightCurve(**data_kwargs, **kwargs)
