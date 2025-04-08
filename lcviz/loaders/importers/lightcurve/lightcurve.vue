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
      api_hint="ldr.extension ="
      :api_hints_enabled="api_hints_enabled"
      hint="Extension to use from the FITS HDUList."
    />
    <v-row>
      <plugin-auto-label
        :value.sync="data_label_value"
        :default="data_label_default"
        :auto.sync="data_label_auto"
        :invalid_msg="data_label_invalid_msg"
        :label="extension_multiselect ? 'Base Data Label' : 'Data Label'"
        api_hint="ldr.importer.data_label ="
        :api_hints_enabled="api_hints_enabled"
        :hint="extension_multiselect ? 'Base label to assign to new data entries (will include extension as suffix).' : 'Label to assign to the new data entry.'"
      ></plugin-auto-label>
    </v-row>
    <plugin-switch
      v-if="create_ephemeris_available"
      :value.sync="create_ephemeris"
      :label="extension_multiselect && extension_selected.length > 1 ? 'Create Ephemerides': 'Create Ephemeris'"
      api_hint="ldr.importer.create_ephemeris = "
      :api_hints_enabled="api_hints_enabled"
      :hint="extension_multiselect && extension_selected.length > 1 ? 'Create ephemerides entries and phase-viewers.': 'Create ephemeris entry and phase-viewer.'"
    />
  </v-contatiner>
</template>