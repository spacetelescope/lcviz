from importlib import import_module
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table
from glue.core.subset import RangeSubsetState


lightkurve_resolver = import_module('lcviz.loaders.resolvers.lightkurve.lightkurve')


@pytest.fixture
def catalog_lightkurve_resolver(deconfigged_helper):
    catalog = Table({
        'ra': [10.5, 11.5, 12.5] * u.deg,
        'dec': [-20.25, -21.25, -22.25] * u.deg,
        'source_id': ['first', 'second', 'third'],
    })
    deconfigged_helper.load(catalog, format='Source Catalog', col_other=['source_id'])
    resolver = deconfigged_helper.loaders['lightkurve']
    resolver.search_input = 'Catalog'
    resolver.catalog = deconfigged_helper._app.data_collection[0].label
    return resolver


def _search_result(*targets):
    return SimpleNamespace(table=Table({'target_name': list(targets)}))


def test_lightkurve_source_input_without_viewers(deconfigged_helper):
    resolver = deconfigged_helper.loaders['lightkurve']._obj

    assert resolver.viewer.labels == []
    assert resolver.search_input.labels == ['Source']
    assert resolver.search_input.selected == 'Source'

    queried_coords = []
    resolver.source = '10.5 -20.25'
    resolver._query_single_coord = (
        lambda coord: queried_coords.append(coord) or Table({'result': [1]})
    )

    resolver.query_archive()

    assert len(queried_coords) == 1
    assert queried_coords[0].ra.deg == 10.5
    assert queried_coords[0].dec.deg == -20.25
    assert len(resolver._output) == 1


@pytest.mark.parametrize(('data_type', 'search_function'), [
    ('Light Curve', 'search_lightcurve'),
    ('Target Pixel File', 'search_targetpixelfile'),
])
@pytest.mark.parametrize('input_mode', ['sky_coords', 'subset', 'source_name'])
def test_lightkurve_catalog_input(catalog_lightkurve_resolver, monkeypatch,
                                 data_type, search_function, input_mode):
    resolver = catalog_lightkurve_resolver
    resolver.data_type = data_type
    resolver.mission = 'TESS'
    expected_ra = [10.5, 11.5, 12.5]
    if input_mode == 'subset':
        data = resolver._obj.catalog.selected_dc_item
        data_collection = resolver._obj._app.data_collection
        data_collection.new_subset_group(
            label='selected sources',
            subset_state=RangeSubsetState(11, 13, data.id['ra'])
        )
        resolver.catalog_subset = 'selected sources'
        expected_ra = expected_ra[1:]
    elif input_mode == 'source_name':
        resolver.catalog_col_type = 'source_name'
        resolver.catalog_name_col = 'source_id'
        from_name = Mock(side_effect=[
            SkyCoord(ra, dec, unit='deg')
            for ra, dec in zip(expected_ra, [-20.25, -21.25, -22.25])
        ])
        monkeypatch.setattr(SkyCoord, 'from_name', from_name)

    search = Mock(side_effect=[
        _search_result(f'{ra}-a', f'{ra}-b') for ra in expected_ra
    ])
    monkeypatch.setattr(lightkurve_resolver, search_function, search)
    resolver.query_archive()

    assert search.call_count == len(expected_ra)
    for call, ra in zip(search.call_args_list, expected_ra):
        assert call.kwargs['target'].isscalar
        assert call.kwargs['target'].ra.deg == ra
        assert call.kwargs['radius'] == 10 * u.arcsec
        assert call.kwargs['mission'] == 'TESS'
        assert call.kwargs['limit'] == 100
    if input_mode == 'source_name':
        assert [call.args[0] for call in from_name.call_args_list] == [
            'first', 'second', 'third'
        ]
    output = resolver._obj._output
    assert list(output['target_name']) == [
        f'{ra}-{suffix}' for ra in expected_ra for suffix in ('a', 'b')
    ]
    assert list(output['source_index']) == [
        i for i in range(len(expected_ra)) for _ in range(2)
    ]
    assert resolver.query_progress == ''
    assert not resolver._obj.returned_no_results
    assert not resolver._obj.returned_max_results


def test_lightkurve_catalog_max_results(catalog_lightkurve_resolver, monkeypatch):
    resolver = catalog_lightkurve_resolver
    resolver.max_results = 3
    search = Mock(side_effect=[_search_result('a', 'b'), _search_result('c', 'd')])
    monkeypatch.setattr(lightkurve_resolver, 'search_lightcurve', search)

    resolver.query_archive()

    assert search.call_count == 2
    assert list(resolver._obj._output['target_name']) == ['a', 'b', 'c']
    assert list(resolver._obj._output['source_index']) == [0, 0, 1]
    assert resolver._obj.returned_max_results
    assert resolver.query_progress == ''


def test_lightkurve_catalog_partial_results(catalog_lightkurve_resolver, monkeypatch):
    resolver = catalog_lightkurve_resolver
    search = Mock(side_effect=[
        RuntimeError('Archive unavailable'), _search_result(), _search_result('third')
    ])
    monkeypatch.setattr(lightkurve_resolver, 'search_lightcurve', search)

    resolver.query_archive()

    assert search.call_count == 3
    assert list(resolver._obj._output['target_name']) == ['third']
    assert list(resolver._obj._output['source_index']) == [2]
    assert any(msg['color'] == 'error' and 'Failed to query' in msg['text']
               for msg in resolver._obj.loader_message_items)
    assert resolver.query_progress == ''

    search.side_effect = None
    search.return_value = _search_result()
    resolver.query_archive()

    assert resolver._obj._output is None
    assert resolver._obj.returned_no_results
    assert resolver.query_progress == ''
