<template>
  <j-tray-plugin
    :config="config"
    plugin_key="Flux Column"
    :api_hints_enabled.sync="api_hints_enabled"
    :description="docs_description || 'Choose which column to use as flux across lcviz.'"
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
      api_hint='plg.dataset ='
      :api_hints_enabled="api_hints_enabled"
      hint="Select the light curve to modify."
    />

    <plugin-select
      :items="flux_column_items.map(i => i.label)"
      :selected.sync="flux_column_selected"
      label="Flux Column"
      api_hint="plg.flux_column ="
      :api_hints_enabled="api_hints_enabled"
      hint="Select the column to adopt as flux."
    />

  </j-tray-plugin>
</template>
