<template>
  <j-tray-plugin
    description='Choose which column to use as flux across lcviz.'
    :link="'https://lcviz.readthedocs.io/en/'+vdocs+'/plugins.html#flux-column'"
    :uses_active_status="uses_active_status"
    @plugin-ping="plugin_ping($event)"
    :keep_active.sync="keep_active"
    :popout_button="popout_button">

    <plugin-dataset-select
      :items="dataset_items"
      :selected.sync="dataset_selected"
      :show_if_single_entry="false"
      label="Data"
      hint="Select the light curve to modify."
    />

    <v-row>
      <v-select
        :menu-props="{ left: true }"
        attach
        :items="flux_column_items.map(i => i.label)"
        v-model="flux_column_selected"
        label="Flux Column"
        hint="Select the column to adopt as flux."
        persistent-hint
      ></v-select>
    </v-row>

  </j-tray-plugin>
</template>
