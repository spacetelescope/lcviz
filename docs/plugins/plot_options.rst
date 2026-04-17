.. _lcviz-plot-options:

************
Plot Options
************

Access per-viewer and per-layer plotting options.

Overview
========

This plugin gives access to per-viewer and per-layer plotting options.

User API
========

.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.plot_options.plot_options.PlotOptions` user API documentation for more details.

    .. code-block:: python

      import jdaviz as jd
      from lightkurve import search_lightcurve
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download().flatten()
      jd.load(lc, format="Light Curve")
      jd.show()

      po = jd.plugins['Plot Options']
      print(f"viewer choices: {po.viewer.choices}")
      po.viewer = po.viewer.choices[0]
      print(f"layer choices: {po.layer.choices}")
      po.layer = po.layer.choices[0]

      po.marker_size = 4
      po.marker_color = 'blue'

.. seealso::

    :ref:`Jdaviz Plot Options <jdaviz:imviz-plot-options>`
        Jdaviz documentation on the Plot Options plugin.
