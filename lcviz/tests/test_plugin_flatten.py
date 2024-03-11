import numpy as np
from numpy.testing import assert_allclose

from lcviz.marks import LivePreviewTrend, LivePreviewFlattened


def _get_marks_from_viewer(viewer, cls=(LivePreviewTrend, LivePreviewFlattened),
                           include_not_visible=False):
    return [m for m in viewer.figure.marks if isinstance(m, cls)
            if include_not_visible or m.visible]


def test_docs_snippets(helper, light_curve_like_kepler_quarter):
    lcviz, lc = helper, light_curve_like_kepler_quarter

    lcviz.load_data(lc)
    # lcviz.show()

    flatten = lcviz.plugins['Flatten']
    flatten.open_in_tray()
    flatten.polyorder = 4
    flattened_lc = flatten.flatten(add_data=True)
    print(flattened_lc)


def test_plugin_flatten(helper, light_curve_like_kepler_quarter):
    helper.load_data(light_curve_like_kepler_quarter)
    tv = helper.default_time_viewer._obj

    ephem = helper.plugins['Ephemeris']
    pv = ephem.create_phase_viewer()._obj
    f = helper.plugins['Flatten']

    # no marks until plugin opened/active
    assert len(_get_marks_from_viewer(tv)) == 0
    assert len(_get_marks_from_viewer(pv)) == 0

    with f.as_active():
        assert len(_get_marks_from_viewer(tv)) == 2
        assert len(_get_marks_from_viewer(pv)) == 1

        # update period which should update phasing in phase-viewer
        ephem.period = 1.2

        before_polyorder = f.polyorder
        before_update = _get_marks_from_viewer(tv)[0].y

        # test error handling in live-preview
        f.polyorder = -1
        assert f._obj.flatten_err != ''
        assert len(_get_marks_from_viewer(tv)) == 0
        assert len(_get_marks_from_viewer(pv)) == 0

        # update polyorder (live-preview should re-appear and have changed from before)
        f.polyorder = before_polyorder + 1
        assert f._obj.flatten_err == ''
        marks = _get_marks_from_viewer(tv)
        assert len(marks) == 2
        after_update = marks[0].y
        assert not np.allclose(before_update, after_update)

        orig_flux_column = f._obj.flux_column.selected
        assert f.dataset.selected_obj is not None
        assert f._obj.flux_label_overwrite is False
        assert f._obj.flux_label.value == f'{orig_flux_column}_flattened'
        f._obj.vue_apply(add_data=True)
        assert f._obj.flux_column.selected == f'{orig_flux_column}_flattened'
        assert f._obj.flatten_err == ''

    # marks are hidden
    assert len(_get_marks_from_viewer(tv)) == 0
    assert len(_get_marks_from_viewer(pv)) == 0


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
