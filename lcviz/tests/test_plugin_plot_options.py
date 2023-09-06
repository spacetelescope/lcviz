def test_docs_snippets(helper, light_curve_like_kepler_quarter):
    lcviz, lc = helper, light_curve_like_kepler_quarter

    lcviz.load_data(lc)
    # lcviz.show()

    po = lcviz.plugins['Plot Options']
    print(f"viewer choices: {po.viewer.choices}")
    po.viewer = po.viewer.choices[0]
    print(f"layer choices: {po.layer.choices}")
    po.layer = po.layer.choices[0]

    po.marker_size = 4
    po.marker_color = 'blue'
