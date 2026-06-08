import numpy as np

from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.table import Table as AstropyTable

from lightkurve import search_lightcurve, search_targetpixelfile

from traitlets import Unicode, List

from jdaviz.core.registries import loader_resolver_registry
from jdaviz.core.template_mixin import (
    SelectPluginComponent,
    with_spinner,
)
from jdaviz.core.loaders.resolvers import BaseConeSearchResolver
from jdaviz.core.user_api import LoaderUserApi
from jdaviz.core.events import SnackbarMessage

__all__ = ["LightkurveResolver"]


@loader_resolver_registry("lightkurve")
class LightkurveResolver(BaseConeSearchResolver):
    template_file = __file__, "lightkurve.vue"

    mission_items = List([]).tag(sync=True)
    mission_selected = Unicode().tag(sync=True)

    data_type_items = List([]).tag(sync=True)
    data_type_selected = Unicode().tag(sync=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mission = SelectPluginComponent(
            self, items="mission_items", selected="mission_selected",
            manual_options=['Kepler', 'K2', 'TESS']
        )
        self.max_results = 100
        self.radius = 10
        self.radius_unit.selected = "arcsec"

        self.data_type = SelectPluginComponent(
            self, items='data_type_items', selected='data_type_selected',
            manual_options=['Light Curve', 'Target Pixel File']
        )

    @property
    def user_api(self):
        return LoaderUserApi(
            self,
            expose=[
                "viewer", "coordframe", "radius", "radius_unit",
                "source",
                "mission", "data_type",
                "max_results",
                "query_archive"
            ],
        )

    @with_spinner(spinner_traitlet="results_loading")
    def query_archive(self):
        try:
            skycoord_center = SkyCoord.from_name(self.source, frame=self.coordframe.selected)
        except Exception as e:
            self.hub.broadcast(SnackbarMessage(
                f"Unable to resolve source coordinates: {self.source}",
                sender=self, color="error", traceback=e
            ))
            return

        radius = self.radius * u.Unit(self.radius_unit.selected)

        try:
            if self.data_type.selected == 'Light Curve':
                output = search_lightcurve(
                    target=skycoord_center,
                    radius=radius,
                    mission=self.mission.selected,
                    limit=self.max_results,
                )
            elif self.data_type.selected == 'Target Pixel File':
                output = search_targetpixelfile(
                    target=skycoord_center,
                    radius=radius,
                    mission=self.mission.selected,
                    limit=self.max_results,
                )
            else:
                raise NotImplementedError("Data type not recognized.")
        except Exception as e:
            self.hub.broadcast(SnackbarMessage(
                f"Lightkurve archive query failed: {e}",
                sender=self, color="error", traceback=e
            ))
            return

        if len(output) == 0:
            self.returned_no_results = True
            self.hub.broadcast(SnackbarMessage(
                f"No results found for {self.source}.",
                sender=self, color="warning"
            ))
            return

        self.returned_no_results = False
        self.returned_max_results = len(output) >= self.max_results
        self._output = self._search_result_to_table(output)

        self._resolver_input_updated()

    @staticmethod
    def _search_result_to_table(search_result):
        """Convert a lightkurve SearchResult to a clean astropy Table.

        The SearchResult's internal table contains many columns with masked or
        mixed types that cause type-inference failures when added row-by-row to
        jdaviz's QTable. This method selects only the display-relevant columns
        and converts every value to a plain Python scalar so astropy can infer
        consistent dtypes.
        """
        t = search_result.table
        keep = ['#', 'target_name', 'obs_collection', 'author',
                'year', 'description', 'exptime', 'dataURI']
        cols = [c for c in keep if c in t.colnames]

        rows = []
        for row in t:
            clean = {}
            for c in cols:
                val = row[c]
                # Convert masked scalars and numpy scalars to plain Python types
                if val is np.ma.masked:
                    clean[c] = ''
                elif hasattr(val, 'item'):  # numpy scalar
                    try:
                        clean[c] = val.item()
                    except Exception:
                        clean[c] = str(val)
                else:
                    clean[c] = val
            rows.append(clean)

        return AstropyTable(rows=rows) if rows else AstropyTable(names=cols)

    def vue_query_archive(self, _=None):
        self.query_archive()

    def parse_input(self):
        return self._output
