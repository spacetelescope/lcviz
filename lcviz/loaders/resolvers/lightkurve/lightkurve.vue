<template>
  <j-loader
    title="Lightkurve"
    :popout_button="popout_button"
    :spinner="spinner"
    :parsed_input_is_query="parsed_input_is_query"
    v-model:treat_table_as_query="treat_table_as_query"
    :observation_table="observation_table"
    :observation_table_populated="observation_table_populated"
    :file_table="file_table"
    :file_table_populated="file_table_populated"
    :file_cache="file_cache"
    :file_timeout="file_timeout"
    :target_items="target_items"
    v-model:target_selected="target_selected"
    :format_items="format_items"
    v-model:format_selected="format_selected"
    :importer_widget="importer_widget"
    :api_hints_enabled="api_hints_enabled"
    :valid_import_formats="valid_import_formats"
    :server_is_remote="server_is_remote"
    :is_wcs_linked="is_wcs_linked"
    :footprint_select_icon="footprint_select_icon"
    :custom_toolbar_enabled="custom_toolbar_enabled"
    :image_data_loaded="image_data_loaded"
    @link-by-wcs="link_by_wcs"
    @toggle-custom-toolbar="toggle_custom_toolbar"
  >
    <v-form v-model="all_fields_filled">
      <j-plugin-section-header>Source Selection</j-plugin-section-header>

      <plugin-select
        :items="search_input_items.map(i => i.label)"
        v-model:selected="search_input_selected"
        label="Input"
        api_hint="ldr.search_input ="
        :api_hints_enabled="api_hints_enabled"
        hint="Select the source of cone-search coordinates."
      ></plugin-select>

      <div v-if="search_input_selected === 'Source'">
        <v-row>
          <v-text-field
            v-model="source"
            :label="api_hints_enabled ? 'ldr.source =' : 'Source/Coordinates'"
            :class="api_hints_enabled ? 'api-hint' : null"
            hint="Enter a source name or coordinate pair in degrees to center your query on."
            :rules="[() => !!source || 'This field is required']"
            persistent-hint>
          </v-text-field>
        </v-row>

        <plugin-select
          :items="coordframe_choices.map(i => i.label)"
          v-model:selected="coordframe_selected"
          label="Coordinate Frame"
          api_hint="ldr.coordframe ="
          :api_hints_enabled="api_hints_enabled"
          hint="Astronomical coordinate frame for the query coordinate"
        ></plugin-select>
      </div>

      <div v-if="search_input_selected === 'Viewer'">
        <plugin-viewer-select
          :items="viewer_items"
          v-model:selected="viewer_selected"
          :show_if_single_entry="false"
          label="Viewer"
          api_hint="ldr.viewer ="
          :api_hints_enabled="api_hints_enabled"
          hint="Select a viewer to retrieve center coordinates."
        />

        <v-row>
          <v-switch
            v-model="coord_follow_viewer_pan"
            label="Follow Viewer Center"
            hint="Automatically adjust coordinates as viewer pans and zooms"
            persistent-hint
          ></v-switch>
        </v-row>

        <v-row>
          <v-text-field
            v-model="source"
            label="Source/Coordinates"
            hint="Coordinates at the viewer center"
            disabled
            persistent-hint>
          </v-text-field>
        </v-row>

        <plugin-select
          :items="coordframe_choices.map(i => i.label)"
          v-model:selected="coordframe_selected"
          label="Coordinate Frame"
          api_hint="ldr.coordframe ="
          :api_hints_enabled="api_hints_enabled"
          hint="Astronomical coordinate frame for the query coordinate"
          :disabled="true"
        ></plugin-select>
      </div>

      <div v-if="search_input_selected === 'Catalog'">
        <plugin-dataset-select
          :items="catalog_items"
          v-model:selected="catalog_selected"
          label="Catalog"
          :show_if_single_entry="true"
          api_hint="ldr.catalog ="
          :api_hints_enabled="api_hints_enabled"
          hint="Select a loaded catalog. The archive is queried once per catalog row."
        />

        <plugin-select
          :items="catalog_subset_items.map(i => i.label)"
          v-model:selected="catalog_subset_selected"
          label="Subset"
          api_hint="ldr.catalog_subset ="
          :api_hints_enabled="api_hints_enabled"
          hint="Optionally restrict the query to a subset of catalog rows."
        ></plugin-select>

        <j-flex-row>
          <v-radio-group
            v-model="catalog_col_type"
            row
            label="Coordinates from"
            style="margin-top: 15px"
          >
            <v-radio
              label="RA/Dec Columns"
              value="sky_coords"
              style="margin-top: -8px"
            ></v-radio>
            <v-radio
              label="Source Names"
              value="source_name"
              :disabled="catalog_name_col_items.length === 0"
              style="margin-top: -8px"
            ></v-radio>
          </v-radio-group>
        </j-flex-row>
        <v-alert
          v-if="catalog_name_col_items.length === 0"
          type="info"
          dense
          style="margin-top: -20px; margin-bottom: 8px"
        >
          No source name columns found.
        </v-alert>

        <plugin-select
          v-if="catalog_col_type === 'source_name'"
          :items="catalog_name_col_items.map(i => i.label)"
          v-model:selected="catalog_name_col_selected"
          label="Source Name Column"
          api_hint="ldr.catalog_name_col ="
          :api_hints_enabled="api_hints_enabled"
          hint="Column of source names to resolve into coordinates."
        ></plugin-select>

        <j-flex-row v-if="catalog_col_type === 'source_name'">
          <v-alert type="warning" dense>
            Source-name resolution issues one request per catalog row (Sesame/CDS).
            Large catalogs may take significant time.
          </v-alert>
        </j-flex-row>

        <plugin-select
          :items="coordframe_choices.map(i => i.label)"
          v-model:selected="coordframe_selected"
          label="Coordinate Frame"
          api_hint="ldr.coordframe ="
          :api_hints_enabled="api_hints_enabled"
          hint="Astronomical Coordinate Frame of the catalog coordinates."
        ></plugin-select>
      </div>

      <j-flex-row justify="space-between">
        <div :style="{ width: '55%' }">
          <v-text-field
            variant="underlined"
            v-model.number="radius"
            type="number"
            :label="api_hints_enabled ? 'ldr.radius =' : 'Radius'"
            :class="api_hints_enabled ? 'api-hint' : null">
          </v-text-field>
        </div>
        <div :style="{ width: '40%' }">
          <plugin-select
            :items="radius_unit_items.map(i => i.label)"
            v-model:selected="radius_unit_selected"
            label="Unit"
            api_hint="ldr.radius_unit ="
            :api_hints_enabled="api_hints_enabled"
          ></plugin-select>
        </div>
      </j-flex-row>
      <j-flex-row>
        <span class="v-messages" style="width: 100%; padding: 0 12px; margin-top: -12px">
          Angular radius around source coordinates, within which to query for data.
        </span>
      </j-flex-row>

      <j-plugin-section-header>Mission</j-plugin-section-header>

      <plugin-select
        :show_if_single_entry="true"
        :items="mission_items.map(i => i.label)"
        v-model:selected="mission_selected"
        label="Mission"
        :search="true"
        api_hint="ldr.mission ="
        :api_hints_enabled="api_hints_enabled"
        hint="Select a mission to search for data"
      ></plugin-select>

      <plugin-select
        :show_if_single_entry="true"
        :items="data_type_items.map(i => i.label)"
        v-model:selected="data_type_selected"
        label="Data Type"
        :search="true"
        api_hint="ldr.data_type ="
        :api_hints_enabled="api_hints_enabled"
        hint="Select a data type to search for"
      ></plugin-select>

      <v-row justify="space-between" style="margin-top: 12px">
        <v-text-field
          v-model.number='max_results'
          type="number"
          style="padding: 0px"
          :label="api_hints_enabled ? 'ldr.max_results =' : 'Max Results'"
          :class="api_hints_enabled ? 'api-hint' : null"
          persistent-hint
          hint="Maximum total number of results to return across all queried sources"
        ></v-text-field>
      </v-row>
    </v-form>



    <v-row class="row-no-outside-padding" justify="end" style="margin-top: 32px">
      <span v-if="query_progress" style="align-self: center; margin-right: 8px; font-size: 0.85em; color: gray;">
        {{ query_progress }}
      </span>
      <plugin-action-button
        :spinner="results_loading"
        :disabled="!all_fields_filled"
        :results_isolated_to_plugin="true"
        :api_hints_enabled="api_hints_enabled"
        @click="query_archive">
          {{ api_hints_enabled ?
              'ldr.query_archive()'
              :
              'Query Archive'
          }}
      </plugin-action-button>
    </v-row>

    <j-loader-banner-messages :items="loader_message_items"></j-loader-banner-messages>

    <v-row v-if="returned_max_results">
      <v-alert type="warning">
        The number of results returned has reached the maximum limit set ({{ max_results }}). Consider increasing the maximum results to ensure all data is retrieved.
      </v-alert>
    </v-row>
  </j-loader>
</template>

<script>
export default {
  data() {
    return {
      all_fields_filled: false, // Reactive property for form validity
    };
  },
};
</script>
