from glue.core import DataCollection
import numpy as np


def test_translator(light_curve_like_kepler_quarter):
    light_curve = light_curve_like_kepler_quarter
    dc = DataCollection()
    dc['dummy-lc'] = light_curve
    translated_lc = dc['dummy-lc'].get_object()

    # check for equality within these attrs:
    attrs = ['time', 'flux', 'flux_err']

    for attr in attrs:
        expected = getattr(light_curve, attr)
        translated = getattr(translated_lc, attr)

        if attr == 'time':
            args = (
                expected.tdb.jd,
                translated.tdb.jd
            )
        else:
            args = (
                expected.value,
                translated.to_value(expected.unit)
            )

        # check that attribute's values match expectations:
        np.testing.assert_allclose(*args)

        if hasattr(expected, 'mask'):
            # check that mask is preserved
            assert np.all(expected.mask == translated.mask)
