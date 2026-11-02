<template>
  <j-tray-plugin
    description='Extract light curve from TPF data.'
    :link="'https://lcviz.readthedocs.io/en/'+vdocs+'/plugins.html#photometric-extraction'"
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
              <v-switch
                v-model="show_live_preview"
                label="Show live preview"
                hint="Whether to show live preview of binning options."
                persistent-hint
              ></v-switch>
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
      hint="Select the TPF as input."
    />

    <plugin-add-results
      v-model:label="results_label"
      :label_default="results_label_default"
      v-model:label_auto="results_label_auto"
      :label_invalid_msg="results_label_invalid_msg"
      :label_overwrite="results_label_overwrite"
      label_hint="Label for the extracted light curve."
      :add_to_viewer_items="add_to_viewer_items"
      v-model:add_to_viewer_selected="add_to_viewer_selected"
      action_label="Extract"
      action_tooltip="Extract photometry"
      :action_disabled="!apply_enabled"
      :action_spinner="spinner"
      @click:action="apply"
    ></plugin-add-results>

  </j-tray-plugin>
</template>
