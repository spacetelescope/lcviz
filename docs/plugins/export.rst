.. _lcviz-export:

******
Export
******

Export plots and data from any viewer to various formats.

Overview
========

This plugin allows exporting the plot in a given viewer to various image formats.

User API
========

.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.export.export.Export` user API documentation for more details.

    .. code-block:: python

      import jdaviz as jd
      from lightkurve import search_lightcurve
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download().flatten()
      jd.load(lc, format="Light Curve")
      jd.show()

      export = jd.plugins['Export']
      export.export('test.png')

.. seealso::

    :ref:`Jdaviz Export Plot <jdaviz:imviz-export-plot>`
        Jdaviz documentation on the Export plugin.
