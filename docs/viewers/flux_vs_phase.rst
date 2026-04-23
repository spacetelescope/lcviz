.. _lcviz-viewer-phase:

**************
Flux vs Phase
**************

Display flux as a function of orbital phase for phase-folded light curves.

Overview
========

The Flux vs Phase viewer (registry name ``lcviz-phase-viewer``) displays flux against
orbital phase computed from the ephemeris defined in the
:ref:`Ephemeris plugin <lcviz-ephemeris>`. One phase viewer is created automatically
for each ephemeris component added.

The x-axis spans [-0.5, 0.5] in phase units by default, and the viewer stays
synchronized with the time viewer through the shared ephemeris.

UI Access
=========

.. wireframe-demo:: _static/jdaviz-wireframe.html
   :js: jdaviz-wireframe-actions.js
   :css: jdaviz-wireframe.css
   :repeat: false
   :steps-json: [{"action": "show-sidebar", "value": "loaders", "delay": 1500, "caption": "Open the data loader"}, {"action": "select-tab", "value": "Viewer", "delay": 1500, "caption": "Select the Viewer tab"}, {"action": "select-dropdown", "value": "Viewer Type:Flux vs Phase", "delay": 1500, "caption": "Set viewer type to Flux vs Phase"}]

API Access
==========

.. code-block:: python

    import jdaviz as jd
    from lightkurve import search_lightcurve

    lc = search_lightcurve("HAT-P-11", mission="Kepler",
                           cadence="long", quarter=10).download().flatten()
    jd.load(lc, format="Light Curve")
    jd.show()

    # Set ephemeris to create a phase viewer
    ephem = jd.plugins['Ephemeris']
    ephem.period = 4.88780258
    ephem.t0 = 2.43

    # Access the phase viewer
    pv = jd.viewers['flux-vs-phase:default[1]']

.. seealso::

    :class:`~lcviz.viewers.PhaseScatterView`
        API documentation for the Flux vs Phase viewer.

    :ref:`lcviz-ephemeris`
        The Ephemeris plugin for defining phase-folding parameters.
