.. _lcviz-stitch:

******
Stitch
******

Combine multiple light curves into a single entry.

Overview
========

This plugin allows for combining multiple light curves into a single entry.  It is only
available if there are at least two light curves loaded into a light curve viewer.

User API
========

.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.stitch.stitch.Stitch` user API documentation for more details.

    .. code-block:: python

      import jdaviz as jd
      from lightkurve import search_lightcurve
      lc1 = search_lightcurve("HAT-P-11", mission="Kepler",
                              cadence="long", quarter=9).download()
      lc2 = search_lightcurve("HAT-P-11", mission="Kepler",
                              cadence="long", quarter=10).download()
      jd.load(lc1, format="Light Curve", data_label='lc1')
      jd.load(lc2, format="Light Curve", data_label='lc2')
      jd.show()

      stitch = jd.plugins['Stitch']
      stitch.open_in_tray()
      stitch.dataset.select_all()
      stitched_lc = stitch.stitch()
      print(stitched_lc)

.. seealso::

    This plugin uses the following ``lightkurve`` implementations:

    * :meth:`lightkurve.LightCurveCollection.stitch`
