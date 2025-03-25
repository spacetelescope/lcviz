<template>
  <j-tray-plugin
    :config="config"
    plugin_key="Binning"
    :api_hints_enabled.sync="api_hints_enabled"
    :description="docs_description || 'Bin input light curve in time or phase-space.'"
    :link="'https://lcviz.readthedocs.io/en/'+vdocs+'/plugins.html#binning'"
    :uses_active_status="uses_active_status"
    @plugin-ping="plugin_ping($event)"
    :keep_active.sync="keep_active"
    :popout_button="popout_button">

    <v-row>
      <v-expansion-panels popout>
        <v-expansion-panel>
          <v-expansion-panel-header v-slot="{ open }">
            <span style="padding: 6px">Settings</span>
          </v-expansion-panel-header>
          <v-expansion-panel-content>
            <v-row>
              <plugin-switch
                :value.sync="show_live_preview"
                label="Show live preview"
                api_hint="plg.show_live_preview ="
                :api_hints_enabled="api_hints_enabled"
                hint="Whether to show live preview of binning options."
                persistent-hint
              />
            </v-row>
          </v-expansion-panel-content>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-row>

    <plugin-dataset-select
      :items="dataset_items"
      :selected.sync="dataset_selected"
      :show_if_single_entry="false"
      label="Data"
      api_hint="plg.dataset ="
      :api_hints_enabled="api_hints_enabled"
      hint="Select the light curve as input."
    />

    <plugin-ephemeris-select
      :items="ephemeris_items"
      :selected.sync="ephemeris_selected"
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
      :previews_temp_disabled.sync="previews_temp_disabled"
      :previews_last_time="previews_last_time"
      :show_live_preview.sync="show_live_preview"
    />

    <plugin-add-results
      :label.sync="results_label"
      :label_default="results_label_default"
      :label_auto.sync="results_label_auto"
      :label_invalid_msg="results_label_invalid_msg"
      :label_overwrite="results_label_overwrite"
      label_hint="Label for the binned data."
      :add_to_viewer_items="add_to_viewer_items"
      :add_to_viewer_selected.sync="add_to_viewer_selected"
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
