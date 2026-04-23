.. _lcviz-binning:

*******
Binning
*******

Bin a light curve in time or phase-space.

Overview
========

This plugin supports binning a light curve in time or phase-space.

UI Access
=========

.. wireframe-demo:: _static/jdaviz-wireframe.html
   :js: jdaviz-wireframe-actions.js
   :css: jdaviz-wireframe.css
   :repeat: false
   :steps-json: [{"action": "show-sidebar", "value": "plugins", "delay": 1500, "caption": "Open the plugin toolbar"}, {"action": "open-panel", "value": "Binning", "delay": 1000, "caption": "Open the Binning plugin"}]

User API
========

.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.binning.binning.Binning` user API documentation for more details.

    .. code-block:: python

      import jdaviz as jd
      from lightkurve import search_lightcurve
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download().flatten()
      jd.load(lc, format="Light Curve")
      jd.show()

      binning = jd.plugins['Binning']
      binning.n_bins = 150
      binned_lc = binning.bin(add_data=True)
      print(binned_lc)

.. seealso::

    This plugin uses the following ``lightkurve`` implementations:

    * :meth:`lightkurve.LightCurve.bin`
