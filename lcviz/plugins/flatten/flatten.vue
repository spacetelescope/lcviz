<template>
  <j-tray-plugin
    description='Remove long-term trends.'
    :link="'https://lcviz.readthedocs.io/en/'+vdocs+'/plugins.html#flatten'"
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
                label="Show flattened preview"
                hint="Whether to show live-preview of the unnormalized flattened light curve."
                persistent-hint
              ></v-switch>
            </v-row>
            <v-row v-if="show_live_preview && !unnormalize">
              <v-alert type="warning">Live preview is unnormalized, but flattening will normalize.</v-alert>
            </v-row>
            <v-row>
              <v-switch
                v-model="show_trend_preview"
                label="Show trend preview"
                hint="Whether to show live-preview of the trend used for flattening."
                persistent-hint
              ></v-switch>
            </v-row>
            <v-row>
              <v-switch
                v-model="default_to_overwrite"
                label="Overwrite by default"
                hint="Whether the output label should default to overwriting the input data."
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
      hint="Select the light curve as input."
    />

    <v-row>
      <v-text-field
        label="Window length"
        type="number"
        :step="1"
        v-model.number="window_length"
        :rules="[() => window_length !== '' || 'This field is required',
                 () => window_length > 0 || 'Must be a positive odd integer']"
        hint="The length of the filter window."
        persistent-hint
      >
      </v-text-field>
    </v-row>

    <v-row>
      <v-text-field
        label="Order"
        type="number"
        :step="1"
        v-model.number="polyorder"
        :rules="[() => polyorder !== '' || 'This field is required',
                 () => polyorder >= 0 || 'Must be >= 0',
                 () => polyorder < window_length || 'Must be less than window length']"
        hint="The order of the polynomial used to fit the samples."
        persistent-hint
      >
      </v-text-field>
    </v-row>

    <v-row>
      <v-text-field
        label="Break tolerance"
        type="number"
        :step="1"
        v-model.number="break_tolerance"
        :rules="[() => break_tolerance !== '' || 'This field is required',
                 () => break_tolerance > 0 || 'Must be a positive integer']"
        hint="If there are large gaps in time, flatten will split the flux into several sub-lightcurves and apply savgol_filter to each individually. A gap is defined as a period in time larger than break_tolerance times the median gap."
        persistent-hint
      >
      </v-text-field>
    </v-row>

    <v-row>
      <v-text-field
        label="Iterations"
        type="number"
        :step="1"
        v-model.number="niters"
        :rules="[() => niters !== '' || 'This field is required',
                 () => niters > 0 || 'Must be a positive integer']"
        hint="Number of iterations to iteratively sigma clip and flatten."
        persistent-hint
      >
      </v-text-field>
    </v-row>

    <v-row>
      <v-text-field
        label="Sigma"
        type="number"
        :step="0.5"
        v-model.number="sigma"
        :rules="[() => sigma !== '' || 'This field is required',
                 () => sigma > 0 || 'Must be a positive value']"
        hint="Number of sigma above which to remove outliers from the flatten."
        persistent-hint
      >
      </v-text-field>
    </v-row>

    <v-row>
      <v-switch
        v-model="unnormalize"
        label="Un-normalize"
        hint="Whether to multiply the flattened light curve by the median of the trend."
        persistent-hint
      ></v-switch>
    </v-row>

    <v-row v-if="show_live_preview && !unnormalize">
      <v-alert type="warning">Live preview is unnormalized, but flattening will normalize.</v-alert>
    </v-row>

    <v-alert v-if="previews_temp_disable && (show_live_preview || show_trend_preview)" type='warning' style="margin-left: -12px; margin-right: -12px">
      Live-updating is temporarily disabled (last update took {{last_live_time}}s)
      <v-row justify='center'>
        <j-tooltip tooltipcontent='hide live trend and flattened previews (can be re-enabled from the settings section in the plugin).' span_style="width: 100%">
          <v-btn style='width: 100%' @click="() => {show_live_preview = false; show_trend_preview = false}">
            disable previews
          </v-btn>
        </j-tooltip>
      </v-row>
      <v-row justify='center'>
        <j-tooltip tooltipcontent='manually update live-previews based on current plugin inputs.' span_style="width: 100%">
          <v-btn style='width: 100%' @click="previews_temp_disable = false">
            update preview
          </v-btn>
        </j-tooltip>
      </v-row>
    </v-alert>

    <plugin-add-results
      :label.sync="results_label"
      :label_default="results_label_default"
      :label_auto.sync="results_label_auto"
      :label_invalid_msg="results_label_invalid_msg"
      :label_overwrite="results_label_overwrite"
      label_hint="Label for the flattened data."
      :add_to_viewer_items="add_to_viewer_items"
      :add_to_viewer_selected.sync="add_to_viewer_selected"
      action_label="Flatten"
      action_tooltip="Flatten data"
      :action_disabled="flatten_err.length > 0 || spinner"
      @click:action="apply"
    ></plugin-add-results>

    <v-row v-if="flatten_err">
      <span class="v-messages v-messages__message text--secondary">
        <b style="color: red !important">ERROR:</b> {{flatten_err}}
      </span>
    </v-row>

  </j-tray-plugin>
</template>
