.. _lcviz-flux-column:

***********
Flux Column
***********

Choose which column in the underlying data is used as the flux column throughout the app.

Overview
========

This plugin allows choosing which column in the underlying data should be used as the flux column
(origin) throughout the app (when plotting and in any data analysis plugins).

UI Access
=========

.. wireframe-demo:: _static/jdaviz-wireframe.html
   :js: jdaviz-wireframe-actions.js
   :css: jdaviz-wireframe.css
   :repeat: false
   :steps-json: [{"action":"show-sidebar","value":"plugins","delay":1500},{"action":"open-panel","value":"Flux Column","delay":1000}]

User API
========

.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.flux_column.flux_column.FluxColumn` user API documentation for more details.

    .. code-block:: python

      import jdaviz as jd
      from lightkurve import search_lightcurve
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download().flatten()
      jd.load(lc, format="Light Curve")
      jd.show()

      flux_col = jd.plugins['Flux Column']
      print(flux_col.flux_column.choices)
      flux_col.flux_column = 'sap_flux'

.. seealso::

    This plugin reproduces the behavior also available in ``lightkurve`` as:

    * :meth:`lightkurve.LightCurve.select_flux`
