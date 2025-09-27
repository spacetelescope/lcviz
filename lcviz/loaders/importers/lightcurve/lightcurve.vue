<template>
  <v-container>
    <div style="position: absolute; width: 32px; right: 0px; margin-right: 12px; margin-top: -32px">
      <j-tooltip tooltipcontent='Toggle multiselect for extension.'>
        <v-btn
          icon
          style="opacity: 0.7"
          @click="extension_multiselect = !extension_multiselect"
        >
          <img :src="extension_multiselect ? icon_checktoradial : icon_radialtocheck" width="24" class="invert-if-dark"/>
      </v-btn>
      </j-tooltip>
    </div>
    <plugin-select
      v-if="input_hdulist"
      :items="extension_items.map(i => i.label)"
      :selected.sync="extension_selected"
      :multiselect="extension_multiselect"
      :show_if_single_entry="true"
      label="Extension"
      api_hint="ldr.importer.extension ="
      :api_hints_enabled="api_hints_enabled"
      hint="Extension to use from the FITS HDUList."
    />
    <plugin-auto-label
      :value.sync="data_label_value"
      :default="data_label_default"
      :auto.sync="data_label_auto"
      :invalid_msg="data_label_invalid_msg"
      :label="extension_multiselect ? 'Base Data Label' : 'Data Label'"
      api_hint="ldr.importer.data_label ="
      :api_hints_enabled="api_hints_enabled"
      :hint="input_hdulist && extension_multiselect ? 'Base label to assign to new data entries (will include extension as suffix).' : 'Label to assign to the new data entry.'"
    ></plugin-auto-label>

    <plugin-viewer-create-new
      :items="viewer_items"
      :selected.sync="viewer_selected"
      :create_new_items="viewer_create_new_items"
      :create_new_selected.sync="viewer_create_new_selected"
      :new_label_value.sync="viewer_label_value"
      :new_label_default="viewer_label_default"
      :new_label_auto.sync="viewer_label_auto"
      :new_label_invalid_msg="viewer_label_invalid_msg"
      :multiselect="viewer_multiselect"
      :show_multiselect_toggle="false"
      label="Viewer for Light Curve"
      api_hint='ldr.importer.viewer = '
      :api_hints_enabled="api_hints_enabled"
      :show_if_single_entry="true"
      hint="Select the viewer to use for the new 1D Light Curve data entry."
    ></plugin-viewer-create-new>

    <plugin-switch
      v-if="create_ephemeris_available"
      :value.sync="create_ephemeris"
      :label="extension_multiselect && extension_selected.length > 1 ? 'Create Ephemerides': 'Create Ephemeris'"
      api_hint="ldr.importer.create_ephemeris = "
      :api_hints_enabled="api_hints_enabled"
      :hint="extension_multiselect && extension_selected.length > 1 ? 'Create ephemerides entries and phase-viewers.': 'Create ephemeris entry and phase-viewer.'"
    />

    <v-row justify="end">
      <plugin-action-button
        :spinner="import_spinner"
        :disabled="import_disabled"
        :results_isolated_to_plugin="false"
        :api_hints_enabled="api_hints_enabled"
        @click="import_clicked">
        {{ api_hints_enabled ?
          'ldr.importer()'
          :
          'Import'
        }}
      </plugin-action-button>
    </v-row>
  </v-container>
</template>