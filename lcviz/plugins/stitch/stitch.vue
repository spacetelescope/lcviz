<template>
  <j-tray-plugin
    description='Stitch light curves together.'
    :link="'https://lcviz.readthedocs.io/en/'+vdocs+'/plugins.html#stitch'"
    :popout_button="popout_button">

    <plugin-dataset-select
      :items="dataset_items"
      :selected.sync="dataset_selected"
      :show_if_single_entry="true"
      :multiselect="true"
      label="Data"
      hint="Select the light curves as input."
    />

    <v-row v-if="dataset_selected.length < 2">
      <span class="v-messages v-messages__message text--secondary">
        <b style="color: red !important">Must select at least two input light curves to stitch.</b>
      </span>
    </v-row>

    <plugin-add-results v-else
      :label.sync="results_label"
      :label_default="results_label_default"
      :label_auto.sync="results_label_auto"
      :label_invalid_msg="results_label_invalid_msg"
      :label_overwrite="results_label_overwrite"
      label_hint="Label for the binned data."
      :add_to_viewer_items="add_to_viewer_items"
      :add_to_viewer_selected.sync="add_to_viewer_selected"
      action_label="Stitch"
      action_tooltip="Stitch data"
      :action_disabled="dataset_selected.length < 2"
      :action_spinner="spinner"
      @click:action="apply"
    >
      <v-row>
        <v-switch
          v-model="remove_input_datasets"
          label="Remove input datasets"
          hint='Delete input datasets from the app'
          persistent-hint
        >
        </v-switch>
      </v-row>
    </plugin-add-results>

    <v-row v-if="stitch_err">
      <span class="v-messages v-messages__message text--secondary">
        <b style="color: red !important">ERROR:</b> {{stitch_err}}
      </span>
    </v-row>

  </j-tray-plugin>
</template>
