.. _lcviz-time-selector:

*************
Time Selector
*************

Define the time indicated in all light curve viewers and image cubes.

Overview
========

The time selector plugin allows defining the time indicated in all light curve viewers
(time and phase viewers) as well as the time at which all image cubes are displayed.

UI Access
=========

.. wireframe-demo:: _static/jdaviz-wireframe.html
   :js: jdaviz-wireframe-actions.js
   :css: jdaviz-wireframe.css
   :repeat: false
   :steps-json: [{"action": "show-sidebar", "value": "plugins", "delay": 1500, "caption": "Open the plugin toolbar"}, {"action": "open-panel", "value": "Time Selector", "delay": 1000, "caption": "Open the Time Selector plugin"}]

User API
========

.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.time_selector.time_selector.TimeSelector` user API documentation for more details.

    .. code-block:: python

      import jdaviz as jd
      from lightkurve import search_lightcurve
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download().flatten()
      jd.load(lc, format="Light Curve")
      jd.show()

      ts = jd.plugins['Time Selector']
      ts.open_in_tray()

.. seealso::

    :ref:`Jdaviz Slice Plugin <jdaviz:slice>`
        Jdaviz documentation on the Slice plugin.
