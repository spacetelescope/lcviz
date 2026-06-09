from jdaviz.configs.specviz.plugins.unit_conversion.unit_conversion import (UnitConversion,
                                                                            _valid_glue_display_unit,  # noqa
                                                                            _flux_to_sb_unit)
from jdaviz.core.events import GlobalDisplayUnitChanged
from jdaviz.core.registries import tray_registry

from lcviz.viewers import (CubeView, TimeScatterView)

__all__ = ['UnitConversion']


@tray_registry('lcviz-unit-conversion', label="Unit Conversion")
class UnitConversion(UnitConversion):
    """
    See the :ref:`Unit Conversion Plugin Documentation <unit-conversion>` for more details.

    For a full list of exposed attributes, call ``dir(plugin)``.  Note that some attributes are
    applicable depending on the selection of ``viewer`` and/or ``layer``.  Below are
    a list of some common attributes and methods are available through the
    :ref:`public plugin API <plugin-apis>`:

    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.show`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.open_in_tray`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.close_in_tray`
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.docs_link = f"https://lcviz.readthedocs.io/en/{self.vdocs}/plugins.html#unit-conversion"
        self.docs_description = "Choose units for the time and flux axes."
        self.disabled_msg = ""  # otherwise disabled upstream - remove once upstream no longer has a config check

        self.has_time = True
        self.has_flux = True

    @property
    def spectrum_viewer(self):
        if hasattr(self, '_default_time_viewer_reference_name'):
            viewer_reference = self._default_time_viewer_reference_name
        else:
            viewer_reference = self.app._get_first_viewer_reference_name(
            )

        return self.app.get_viewer(viewer_reference)

    def _on_add_data_to_viewer(self, msg):
        viewer = msg.viewer

        if (not len(self.time_unit_selected) or not len(self.flux_unit_selected)):
            # TODO: default based on the native units of the data (LC or TPF)
            self.time_unit.choices = ['d', 'hr', 'min', 's']
            self.time_unit_selected = 'd'
            self.flux_unit.choices = ['erg / (Angstrom cm2 s)']
            self.flux_unit_selected = 'erg / (Angstrom cm2 s)'
            # setting default values will trigger the observes to set the units
            # in _on_unit_selected, so return here to avoid setting twice
            return

        # TODO: when enabling unit-conversion in rampviz, this may need to be more specific
        # or handle other cases for ramp profile viewers
        if isinstance(viewer, TimeScatterView):
            if (viewer.state.x_display_unit == self.time_unit_selected
                    and viewer.state.y_display_unit == self.flux_unit_selected):
                # data already existed in this viewer and display units were already set
                return

            # this spectral viewer was empty (did not have display units set yet),˜
            # but global selections are available in the plugin,
            # so we'll set them to the viewer here
            viewer.state.x_display_unit = self.time_unit_selected
            viewer.state.y_display_unit = self.flux_unit_selected

        elif isinstance(viewer, CubeView):
            # set the attribute display unit (contour and stretch units) for the new layer
            # NOTE: this assumes that all image data is coerced to surface brightness units
            layers = [lyr for lyr in msg.viewer.layers if lyr.layer.data.label == msg.data.label]
            self._handle_attribute_display_unit(self.flux_unit_selected, layers=layers)
            self._clear_cache('image_layers')

    def _on_unit_selected(self, msg):
        """
        When any user selection is made, update the relevant viewer(s) with the new unit,
        and then emit a GlobalDisplayUnitChanged message to notify other plugins of the change.
        """
        print("*** _on_unit_selected", msg.get('name'), msg.get('new'))
        if not len(msg.get('new', '')):
            # empty string, nothing to set yet
            return

        axis = msg.get('name').split('_')[0]

        if axis == 'time':
            xunit = _valid_glue_display_unit(self.time_unit.selected, self.spectrum_viewer, 'x')
            # TODO: iterate over all TimeScatterViewers
            self.spectrum_viewer.state.x_display_unit = xunit
            self.spectrum_viewer.set_plot_axes()

        elif axis == 'flux':
            yunit = _valid_glue_display_unit(self.flux_unit.selected, self.spectrum_viewer, 'y')
            # TODO: iterate over all Time and Phase Scatter Viewers
            self.spectrum_viewer.state.y_display_unit = yunit
            self.spectrum_viewer.set_plot_axes()

            # TODO: handle setting surface brightness units for CubeView

        # axis (first) argument will be one of: time, flux
        self.hub.broadcast(GlobalDisplayUnitChanged(axis,
                           msg.new, sender=self))
