.. _lcviz-ephemeris:

*********
Ephemeris
*********

Set, find, and refine ephemerides used for phase-folding.

Overview
========

The ephemeris plugin allows for setting, finding, and refining the ephemeris or ephemerides used
for phase-folding.

UI Access
=========

.. wireframe-demo:: _static/jdaviz-wireframe.html
   :js: jdaviz-wireframe-actions.js
   :css: jdaviz-wireframe.css
   :repeat: false
   :steps-json: [{"action":"show-sidebar","value":"plugins","delay":1500},{"action":"open-panel","value":"Ephemeris","delay":1000}]

User API
========

.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.ephemeris.ephemeris.Ephemeris` user API documentation for more details.

    .. code-block:: python

      import jdaviz as jd
      from lightkurve import search_lightcurve
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download().flatten()
      jd.load(lc, format="Light Curve")
      jd.show()

      ephem = jd.plugins['Ephemeris']
      ephem.period = 4.88780258
      ephem.t0 = 2.43
      ephem.rename_component('default', 'my component name')
