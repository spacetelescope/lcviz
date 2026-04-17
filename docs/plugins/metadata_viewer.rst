.. _lcviz-metadata-viewer:

***************
Metadata Viewer
***************

View any metadata associated with the selected data.

Overview
========

This plugin allows viewing of any metadata associated with the selected data.

User API
========

.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.metadata_viewer.metadata_viewer.MetadataViewer` user API documentation for more details.

    .. code-block:: python

      import jdaviz as jd
      from lightkurve import search_lightcurve
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download().flatten()
      jd.load(lc, format="Light Curve")
      jd.show()

      metadata = jd.plugins['Metadata']
      print(f"dataset choices: {metadata.dataset.choices}")
      metadata.dataset = metadata.dataset.choices[0]
      print(metadata.meta)

.. seealso::

    :ref:`Jdaviz Metadata Viewer <jdaviz:imviz-metadata-viewer>`
        Jdaviz documentation on the Metadata Viewer plugin.
