import pytest


@pytest.mark.parametrize('helper_name', ['helper', 'deconfigged_helper'])
def test_docs_snippets(helper_name, light_curve_like_kepler_quarter, request):
    jd = request.getfixturevalue(helper_name)
    lc = light_curve_like_kepler_quarter

    jd.load(lc, format='Light Curve')
    # jd.show()

    po = jd.plugins['Plot Options']
    print(f"viewer choices: {po.viewer.choices}")
    po.viewer = po.viewer.choices[0]
    print(f"layer choices: {po.layer.choices}")
    po.layer = po.layer.choices[0]

    po.marker_size = 4
    po.marker_color = 'blue'
