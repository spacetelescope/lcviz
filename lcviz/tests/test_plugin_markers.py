import pytest
import numpy as np
from numpy.testing import assert_allclose

from jdaviz.core.marks import MarkersMark


def _get_markers_from_viewer(viewer):
    return [m for m in viewer.figure.marks if isinstance(m, MarkersMark)][0]


def _assert_dict_allclose(dict1, dict2):
    assert dict1.keys() == dict2.keys()
    for k, v in dict1.items():
        if isinstance(v, float):
            assert_allclose(v, dict2.get(k))
        elif isinstance(v, (tuple, list)):
            assert_allclose(np.asarray(v), np.asarray(dict2.get(k)))
        else:
            assert v == dict2.get(k)


def test_docs_snippets(helper, light_curve_like_kepler_quarter):
    lcviz, lc = helper, light_curve_like_kepler_quarter

    lcviz.load_data(lc)
    # lcviz.show()

    markers = lcviz.plugins['Markers']
    markers.open_in_tray()
    # interactively mark by mousing over the viewer and pressing "M"
    table = markers.export_table()
    print(table)
    markers.clear_table()


def test_plugin_markers(helper, light_curve_like_kepler_quarter):
    helper.load_data(light_curve_like_kepler_quarter)
    tv = helper.default_time_viewer._obj

    mp = helper.plugins['Markers']
    label_mouseover = mp._obj.coords_info
    mp.open_in_tray()

    # test event in flux-vs-time viewer
    label_mouseover._viewer_mouse_event(tv,
                                        {'event': 'mousemove',
                                         'domain': {'x': 0, 'y': 0}})

    assert label_mouseover.as_text() == ('Cursor 0.00000e+00, 0.00000e+00',
                                         'Time 5.45833e+00 d',
                                         'Flux 9.67587e-01')

    object_name = helper.app.data_collection[-1].meta['OBJECT']
    _assert_dict_allclose(label_mouseover.as_dict(), {'data_label': f'{object_name} [Q10]',
                                                      'time': 5.4583335,
                                                      'time:unit': 'd',
                                                      'phase': np.nan,
                                                      'ephemeris': '',
                                                      'axes_x': 5.4583335,
                                                      'axes_x:unit': 'd',
                                                      'index': 262.0,
                                                      'axes_y': 0.96758735,
                                                      'axes_y:unit': '',
                                                      'value': 0.96758735,
                                                      'value:unit': ''})

    mp._obj._on_viewer_key_event(tv, {'event': 'keydown',
                                      'key': 'm'})
    assert len(mp.export_table()) == 1
    assert len(_get_markers_from_viewer(tv).x) == 1

    ephem = helper.plugins['Ephemeris']
    pv = ephem.create_phase_viewer()._obj

    # test event in flux-vs-phase viewer
    label_mouseover._viewer_mouse_event(pv,
                                        {'event': 'mousemove',
                                         'domain': {'x': 0.5, 'y': 0}})

    assert label_mouseover.as_text() == ('Cursor 5.00000e-01, 0.00000e+00',
                                         'Phase 0.45833',
                                         'Flux 9.67587e-01')

    _assert_dict_allclose(label_mouseover.as_dict(), {'data_label': f'{object_name} [Q10]',
                                                      'time': 5.458333374001086,
                                                      'time:unit': 'd',
                                                      'phase': 0.4583333730697632,
                                                      'ephemeris': 'default',
                                                      'axes_x': 0.4583333730697632,
                                                      'axes_x:unit': '',
                                                      'index': 262.0,
                                                      'axes_y': 0.9675873517990112,
                                                      'axes_y:unit': '',
                                                      'value': 0.9675873517990112,
                                                      'value:unit': ''})

    mp._obj._on_viewer_key_event(pv, {'event': 'keydown',
                                      'key': 'm'})
    assert len(mp.export_table()) == 2
    assert len(_get_markers_from_viewer(tv).x) == 1
    assert len(_get_markers_from_viewer(pv).x) == 1

    # test event in flux-vs-phase viewer (with cursor only)
    label_mouseover.dataset.selected = 'none'
    label_mouseover._viewer_mouse_event(pv,
                                        {'event': 'mousemove',
                                         'domain': {'x': 0.6, 'y': 0}})

    print(label_mouseover.as_text())
    assert label_mouseover.as_text() == ('Cursor 6.00000e-01, 0.00000e+00',
                                         '',
                                         '')

    _assert_dict_allclose(label_mouseover.as_dict(), {'axes_x': 0.6,
                                                      'axes_x:unit': '',
                                                      'axes_y': 0,
                                                      'axes_y:unit': '',
                                                      'data_label': '',
                                                      'time': np.nan,
                                                      'time:unit': '',
                                                      'phase': 0.6,
                                                      'value': 0,
                                                      'value:unit': '',
                                                      'ephemeris': ''})


@pytest.mark.remote_data
def test_tpf_markers(helper, light_curve_like_kepler_quarter):
    helper.load_data(light_curve_like_kepler_quarter)

    # TODO: replace with test fixture
    from lightkurve import search_targetpixelfile
    tpf = search_targetpixelfile("KIC 001429092",
                                 mission="Kepler",
                                 cadence="long",
                                 quarter=10).download()
    helper.load_data(tpf)

    mp = helper.plugins['Markers']
    label_mouseover = mp._obj.coords_info
    mp.open_in_tray()

    assert abs(helper.plugins['Time Selector'].value - 47.006888) < 1e-4

    # test event in image (TPF) viewer
    iv = helper.viewers['image']._obj
    label_mouseover._viewer_mouse_event(iv,
                                        {'event': 'mousemove',
                                         'domain': {'x': 0, 'y': 0}})

    assert label_mouseover.as_text() == ('Pixel x=00000.0 y=00000.0 Value +1.28035e+01 electron / s',  # noqa
                                         'Time 47.00689 d',
                                         '')

    print(label_mouseover.as_dict())
    _assert_dict_allclose(label_mouseover.as_dict(), {'data_label': 'KIC 1429092[TPF]',
                                                      'time': 47.00689,
                                                      'time:unit': 'd',
                                                      'pixel': (0.0, 0.0),
                                                      'axes_x': 0,
                                                      'axes_x:unit': 'pix',
                                                      'axes_y': 0,
                                                      'axes_y:unit': 'pix',
                                                      'value': 12.803529,
                                                      'value:unit': 'electron / s'})
