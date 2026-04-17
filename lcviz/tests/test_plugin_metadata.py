import pytest


@pytest.mark.parametrize('helper_name', ['helper', 'deconfigged_helper'])
def test_docs_snippets(helper_name, light_curve_like_kepler_quarter, request):
    jd = request.getfixturevalue(helper_name)
    lc = light_curve_like_kepler_quarter

    jd.load(lc, format='Light Curve')
    # jd.show()

    metadata = jd.plugins['Metadata']
    print(f"dataset choices: {metadata.dataset.choices}")
    metadata.dataset = metadata.dataset.choices[0]
    print(metadata.meta)
