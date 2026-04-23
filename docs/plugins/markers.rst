.. _lcviz-markers:

*******
Markers
*******

Interactively create markers in any viewer and log information into a table.

Overview
========

This plugin allows for interactively creating markers in any viewer and logging information about
the location of that marker along with the applicable data and viewer labels into a table.

With the plugin open in the tray, mouse over any viewer and press the "m" key to log the information
displayed in the app toolbar into the table.  The markers remain at that fixed pixel-position in
the viewer they were created (regardless of changes to the underlying data or linking) and are only
visible when the plugin is opened.

UI Access
=========

.. wireframe-demo:: _static/jdaviz-wireframe.html
   :js: jdaviz-wireframe-actions.js
   :css: jdaviz-wireframe.css
   :repeat: false
   :steps-json: [{"action": "show-sidebar", "value": "info", "delay": 1500, "caption": "Open the info sidebar"}, {"action": "select-tab", "value": "Markers", "delay": 1000, "caption": "Select the Markers tab"}]

User API
========

.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.markers.markers.Markers` user API documentation for more details.

    .. code-block:: python

      import jdaviz as jd
      from lightkurve import search_lightcurve
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download().flatten()
      jd.load(lc, format="Light Curve")
      jd.show()

      markers = jd.plugins['Markers']
      markers.open_in_tray()
      # interactively mark by mousing over the viewer and pressing "M"
      table = markers.export_table()
      print(table)
      markers.clear_table()

.. seealso::

    :ref:`Jdaviz Markers <jdaviz:markers-plugin>`
        Jdaviz documentation on the Markers plugin.
