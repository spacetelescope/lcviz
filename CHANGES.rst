0.4.0 - unreleased
------------------

0.3.0 - (04-05-2024)
--------------------

* Ability to create additional viewers. [#94]
* Updates to use jdaviz 3.9. [#68]

0.2.0 (02-26-2024)
------------------

* Clone viewer tool. [#74, #91]

* Flux column plugin to choose which column is treated as the flux column for each dataset. [#77]

* Flatten plugin no longer creates new data entries, but instead appends a new column to the input
  light curve and selects as the flux column (origin). [#77]

* Ephemeris plugin now supports passing floats to ``times_to_phases``. [#87]

* Ephemeris plugin's ``create_phase_viewer`` now returns the public user API instance of the viewer
  instead of the underlying object. [#87]

0.1.0 (12-14-2023)
------------------

* Initial release of lcviz with support to import time-series light curves via lightkurve and
  process them through binning, flattening, frequency analysis, and ephemeris plugins.
