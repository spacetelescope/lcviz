.. _lcviz-flatten:

*******
Flatten
*******

Remove trends from a light curve by flattening.

Overview
========

This plugin allows for flattening the light curve by removing trends.  By default, the resulting
flattened light curve is "unnormalized" by multiplying the flattened light curve by the median of
the trend, but this can be disabled through the plugin settings.

User API
========

.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.flatten.flatten.Flatten` user API documentation for more details.

    .. code-block:: python

      import jdaviz as jd
      from lightkurve import search_lightcurve
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download()
      jd.load(lc, format="Light Curve")
      jd.show()

      flatten = jd.plugins['Flatten']
      flatten.open_in_tray()
      flatten.polyorder = 4
      flattened_lc = flatten.flatten(add_data=True)
      print(flattened_lc)

.. seealso::

    This plugin uses the following ``lightkurve`` implementations:

    * :meth:`lightkurve.LightCurve.flatten`
