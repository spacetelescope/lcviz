<template>
  <j-tray-plugin
    :config="config"
    plugin_key="Binning"
    v-model:api_hints_enabled="api_hints_enabled"
    :description="docs_description || 'Bin input light curve in time or phase-space.'"
    :link="'https://lcviz.readthedocs.io/en/'+vdocs+'/plugins.html#binning'"
    :uses_active_status="uses_active_status"
    @plugin-ping="plugin_ping($event)"
    v-model:keep_active="keep_active"
    :popout_button="popout_button">

    <v-row>
      <v-expansion-panels popout>
        <v-expansion-panel>
          <v-expansion-panel-title>
            <span style="padding: 6px">Settings</span>
          </v-expansion-panel-title>
          <v-expansion-panel-text class="plugin-expansion-panel-content">
            <v-row>
              <plugin-switch
                v-model:value="show_live_preview"
                label="Show live preview"
                api_hint="plg.show_live_preview ="
                :api_hints_enabled="api_hints_enabled"
                hint="Whether to show live preview of binning options."
                persistent-hint
              />
            </v-row>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-row>

    <plugin-dataset-select
      :items="dataset_items"
      v-model:selected="dataset_selected"
      :show_if_single_entry="false"
      label="Data"
      api_hint="plg.dataset ="
      :api_hints_enabled="api_hints_enabled"
      hint="Select the light curve as input."
    />

    <plugin-ephemeris-select
      :items="ephemeris_items"
      v-model:selected="ephemeris_selected"
      :show_if_single_entry="false"
      label="Ephemeris"
      api_hint="plg.ephemeris ="
      :api_hints_enabled="api_hints_enabled"
      hint="Select the phase-folding as input."
    />

    <v-row>
      <v-text-field
        :label="api_hints_enabled ? 'plg.n_bins =' : 'N Bins'"
        :class="api_hints_enabled ? 'api-hint' : null"
        type="number"
        v-model.number="n_bins"
        :step="10"
        :rules="[() => n_bins !== '' || 'This field is required',
                 () => n_bins > 0 || 'Number of bins must be positive']"
        hint="Number of bins."
        persistent-hint
      >
      </v-text-field>
    </v-row>

    <plugin-previews-temp-disabled
      v-model:previews_temp_disabled="previews_temp_disabled"
      :previews_last_time="previews_last_time"
      v-model:show_live_preview="show_live_preview"
    />

    <plugin-add-results
      v-model:label="results_label"
      :label_default="results_label_default"
      v-model:label_auto="results_label_auto"
      :label_invalid_msg="results_label_invalid_msg"
      :label_overwrite="results_label_overwrite"
      label_hint="Label for the binned data."
      :add_to_viewer_items="add_to_viewer_items"
      v-model:add_to_viewer_selected="add_to_viewer_selected"
      action_label="Bin"
      action_tooltip="Bin data"
      :action_disabled="!bin_enabled"
      :action_spinner="spinner"
      add_results_api_hint = 'plg.add_results'
      action_api_hint='plg.bin(add_data=True)'
      :api_hints_enabled="api_hints_enabled"
      @click:action="apply"
    ></plugin-add-results>

  </j-tray-plugin>
</template>
