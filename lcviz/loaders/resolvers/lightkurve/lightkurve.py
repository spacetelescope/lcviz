from astropy.coordinates import SkyCoord
from astropy import units as u

from lightkurve import search_lightcurve, search_targetpixelfile

from traitlets import Unicode, List

from jdaviz.core.registries import loader_resolver_registry
from jdaviz.core.template_mixin import (
    SelectPluginComponent,
    with_spinner,
)
from jdaviz.core.loaders.resolvers import BaseConeSearchResolver
from jdaviz.core.user_api import LoaderUserApi

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
        skycoord_center = SkyCoord.from_name(self.source, frame=self.coordframe.selected)
        radius = self.radius * u.Unit(self.radius_unit.selected)

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
        self.reached_max_results = len(output) >= self.max_results
        self._output = output

        self._resolver_input_updated()

    def vue_query_archive(self, _=None):
        self.query_archive()

    def parse_input(self):
        return self._output


