import numpy as np
from numpy.testing import assert_allclose

from lcviz.marks import LivePreviewTrend, LivePreviewFlattened


def _get_marks_from_viewer(viewer, cls=(LivePreviewTrend, LivePreviewFlattened)):
    return [m for m in viewer.figure.marks if isinstance(m, cls)]


def test_plugin_flatten(helper, light_curve_like_kepler_quarter):
    helper.load_data(light_curve_like_kepler_quarter)
    tv = helper.app.get_viewer(helper._default_time_viewer_reference_name)

    f = helper.plugins['Flatten']
    f.plugin_opened = True
    ephem = helper.plugins['Ephemeris']
    pv = ephem.create_phase_viewer()

    assert len(_get_marks_from_viewer(tv)) == 2
    assert len(_get_marks_from_viewer(pv)) == 1

    orig_label = f.dataset.selected
    assert f.dataset.selected_obj is not None
    assert f._obj.add_results.label_overwrite is True
    assert f._obj.add_results.label == orig_label
    f.flatten(add_data=True)


def test_no_overwrite(helper, light_curve_like_kepler_quarter):
    helper.load_data(light_curve_like_kepler_quarter)

    f = helper.plugins['Flatten']

    orig_label = f.dataset.selected
    assert f._obj.add_results.label_overwrite is True
    assert f._obj.add_results.label == orig_label
    f.default_to_overwrite = False
    assert f._obj.add_results.label_overwrite is False
    assert f._obj.add_results.label != orig_label
    f.flatten(add_data=True)


def test_unnormalize(helper, light_curve_like_kepler_quarter):
    helper.load_data(light_curve_like_kepler_quarter)

    f = helper.plugins['Flatten']

    assert f.unnormalize is False
    lc, trend = f.flatten(add_data=False)
    # should be roughly 1
    assert np.nanmedian(lc.flux.value) < 2

    f.unnormalize = True
    lc_unnorm, trend = f.flatten(add_data=False)
    assert_allclose(np.nanmedian(lc.flux.value), np.nanmedian(trend.flux.value), rtol=1e-4)
