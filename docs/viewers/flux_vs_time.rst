.. _lcviz-viewer-time:

************
Flux vs Time
************

Display flux as a function of time for one or more light curves.

Overview
========

The Flux vs Time viewer (registry name ``lcviz-time-viewer``) is lcviz's primary viewer for
exploring light curve data. It displays flux (or any chosen flux column) on the y-axis against
time on the x-axis, with full support for zooming, panning, subset selection, and
slice indicators for linked TPF cube views.

Multiple light curves can be overlaid in the same viewer.  Additional Flux vs Time viewers
can be created via the Viewer Creator controls in jdaviz.

UI Access
=========

.. wireframe-demo:: _static/jdaviz-wireframe.html
   :js: jdaviz-wireframe-actions.js
   :css: jdaviz-wireframe.css
   :repeat: false
   :steps-json: [{"action": "show-sidebar", "value": "loaders", "delay": 1500, "caption": "Open the data loader"}, {"action": "select-tab", "value": "Viewer", "delay": 1500, "caption": "Select the Viewer tab"}, {"action": "select-dropdown", "value": "Viewer Type:Flux vs Time", "delay": 1500, "caption": "Set viewer type to Flux vs Time"}]

API Access
==========

.. code-block:: python

    import jdaviz as jd
    from lightkurve import search_lightcurve

    lc = search_lightcurve("HAT-P-11", mission="Kepler",
                           cadence="long", quarter=10).download()
    jd.load(lc, format="Light Curve")
    jd.show()

    # Access the time viewer
    tv = jd.viewers['flux-vs-time[1]']
    tv.state.x_min  # current x axis minimum

.. seealso::

    :class:`~lcviz.viewers.TimeScatterView`
        API documentation for the Flux vs Time viewer.
