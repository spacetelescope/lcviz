import pytest


@pytest.mark.parametrize('helper_name', ['helper', 'deconfigged_helper'])
def test_docs_snippets(helper_name, light_curve_like_kepler_quarter, request):
    helper = request.getfixturevalue(helper_name)
    lcviz, lc = helper, light_curve_like_kepler_quarter

    lcviz.load(lc)
    # lcviz.show()

    metadata = lcviz.plugins['Metadata']
    print(f"dataset choices: {metadata.dataset.choices}")
    metadata.dataset = metadata.dataset.choices[0]
    print(metadata.meta)
