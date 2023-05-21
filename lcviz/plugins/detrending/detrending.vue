<template>
  <j-tray-plugin
    description='Remove long-term trends.'
    :link="'https://lcviz.readthedocs.io/en/'+vdocs+'/plugins.html#detrending'"
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
                hint="Whether to show live preview of detrending options.  Note that the live-preview of the detrended light curve is not yet normalized."
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
      <v-select
        :menu-props="{ left: true }"
        attach
        :items="method_items.map(i => i.label)"
        v-model="method_selected"
        label="Algorithm/Method"
        hint="Detrending method."
        persistent-hint
      ></v-select>
    </v-row>

    <div v-if="method_selected === 'flatten'">
      <v-row>
        <v-text-field
          label="Window length"
          type="number"
          :step="1"
          v-model.number="flatten_window_length"
          :rules="[() => flatten_window_length !== '' || 'This field is required',
                   () => flatten_window_length > 0 || 'Must be a positive odd integer']"
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
          v-model.number="flatten_polyorder"
          :rules="[() => flatten_polyorder !== '' || 'This field is required',
                   () => flatten_polyorder >= 0 || 'Must be >= 0',
                   () => flatten_polyorder < flatten_window_length || 'Must be less than window length']"
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
          v-model.number="flatten_break_tolerance"
          :rules="[() => flatten_break_tolerance !== '' || 'This field is required',
                   () => flatten_break_tolerance > 0 || 'Must be a positive integer']"
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
          v-model.number="flatten_niters"
          :rules="[() => flatten_niters !== '' || 'This field is required',
                   () => flatten_niters > 0 || 'Must be a positive integer']"
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
          v-model.number="flatten_sigma"
          :rules="[() => flatten_sigma !== '' || 'This field is required',
                   () => flatten_sigma > 0 || 'Must be a positive value']"
          hint="Number of sigma above which to remove outliers from the flatten."
          persistent-hint
        >
        </v-text-field>
      </v-row>
    </div>

    <plugin-add-results
      :label.sync="results_label"
      :label_default="results_label_default"
      :label_auto.sync="results_label_auto"
      :label_invalid_msg="results_label_invalid_msg"
      :label_overwrite="results_label_overwrite"
      label_hint="Label for the detrended data."
      :add_to_viewer_items="add_to_viewer_items"
      :add_to_viewer_selected.sync="add_to_viewer_selected"
      action_label="Detrend"
      action_tooltip="Detrend data"
      :action_disabled="detrend_err.length > 0"
      @click:action="apply"
    ></plugin-add-results>

    <v-row v-if="detrend_err">
      <span class="v-messages v-messages__message text--secondary">
        <b style="color: red !important">ERROR from {{method_selected}}:</b> {{detrend_err}}
      </span>
    </v-row>

  </j-tray-plugin>
</template>
