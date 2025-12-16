<template>
  <j-tray-plugin
    description='Extract light curve from TPF data.'
    :link="'https://lcviz.readthedocs.io/en/'+vdocs+'/plugins.html#photometric-extraction'"
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
              <v-switch
                v-model="show_live_preview"
                label="Show live preview"
                hint="Whether to show live preview of binning options."
                persistent-hint
              ></v-switch>
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
      hint="Select the TPF as input."
    />

    <plugin-add-results
      :label.sync="results_label"
      :label_default="results_label_default"
      :label_auto.sync="results_label_auto"
      :label_invalid_msg="results_label_invalid_msg"
      :label_overwrite="results_label_overwrite"
      label_hint="Label for the extracted light curve."
      :add_to_viewer_items="add_to_viewer_items"
      :add_to_viewer_selected.sync="add_to_viewer_selected"
      action_label="Extract"
      action_tooltip="Extract photometry"
      :action_disabled="!apply_enabled"
      :action_spinner="spinner"
      @click:action="apply"
    ></plugin-add-results>

  </j-tray-plugin>
</template>
