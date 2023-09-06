def test_docs_snippets(helper, light_curve_like_kepler_quarter):
    lcviz, lc = helper, light_curve_like_kepler_quarter

    lcviz.load_data(lc)
    # lcviz.show()

    metadata = lcviz.plugins['Metadata']
    print(f"dataset choices: {metadata.dataset.choices}")
    metadata.dataset = metadata.dataset.choices[0]
    print(metadata.metadata)
