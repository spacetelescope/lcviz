<template>
  <v-container>
    <plugin-select
      v-if="input_hdulist"
      :items="extension_items.map(i => i.label)"
      :selected.sync="extension_selected"
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
        label="Data Label"
        api_hint="ldr.importer.data_label ="
        :api_hints_enabled="api_hints_enabled"
        hint="Label to assign to the new data entry."
      ></plugin-auto-label>
    </v-row>
    <plugin-switch
      v-if="create_ephemeris_available"
      :value.sync="create_ephemeris"
      label="Create Ephemeris"
      api_hint="plg.create_ephemeris = "
      :api_hints_enabled="api_hints_enabled"
      hint="Create ephemeris entry and phase-viewer."
    />
  </v-contatiner>
</template>