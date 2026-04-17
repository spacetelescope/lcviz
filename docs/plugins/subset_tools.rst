.. _lcviz-subset-tools:

************
Subset Tools
************

View and modify defined subsets.

Overview
========

This plugin allows viewing and modifying defined subsets.

User API
========

.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.subset_tools.subset_tools.SubsetTools` user API documentation for more details.

    .. code-block:: python

      import jdaviz as jd
      from lightkurve import search_lightcurve
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download().flatten()
      jd.load(lc, format="Light Curve")
      jd.show()

      subset_tools = jd.plugins['Subset Tools']
      subset_tools.open_in_tray()

.. seealso::

    :ref:`Jdaviz Subset Tools <jdaviz:imviz-subset-plugin>`
        Jdaviz documentation on the Subset Tools plugin.
