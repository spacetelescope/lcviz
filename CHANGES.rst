0.2.0 - unreleased
------------------

* Clone viewer tool. [#74]

* Flux column plugin to choose which column is treated as the flux column for each dataset. [#77]

* Flatten plugin no longer creates new data entries, but instead appends a new column to the input
  light curve and selects as the flux column (origin). [#77]

0.1.0 (12-14-2023)
------------------

* Initial release of lcviz with support to import time-series light curves via lightkurve and
  process them through binning, flattening, frequency analysis, and ephemeris plugins.
