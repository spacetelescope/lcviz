<template>
  <j-tray-plugin
    :config="config"
    plugin_key="Flatten"
    :api_hints_enabled.sync="api_hints_enabled"
    :description="docs_description || 'Flatten input light curve to remove long-term trends.'"
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
              <plugin-switch
                :value.sync="show_live_preview"
                api_hint="plg.show_live_preview ="
                :api_hints_enabled="api_hints_enabled"
                label="Show flattened preview"
                hint="Whether to show live-preview of the unnormalized flattened light curve."
                persistent-hint
              />
            </v-row>
            <v-row v-if="show_live_preview && !unnormalize">
              <v-alert type="warning">Live preview is unnormalized, but flattening will normalize.</v-alert>
            </v-row>
            <v-row>
              <plugin-switch
                :value.sync="show_trend_preview"
                api_hint="plg.show_trend_preview ="
                :api_hints_enabled="api_hints_enabled"
                label="Show trend preview"
                hint="Whether to show live-preview of the trend used for flattening."
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

    <v-row>
      <v-text-field
        :label="api_hints_enabled ? 'plg.window_length =' : 'Window length'"
        :class="api_hints_enabled ? 'api-hint' : null"
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
        :label="api_hints_enabled ? 'plg.polyorder =' : 'Order'"
        :class="api_hints_enabled ? 'api-hint' : null"
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
        :label="api_hints_enabled ? 'plg.break_tolerance =' : 'Break tolerance'"
        :class="api_hints_enabled ? 'api-hint' : null"
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
        :label="api_hints_enabled ? 'plg.niters =' : 'Iterations'"
        :class="api_hints_enabled ? 'api-hint' : null"
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
        :label="api_hints_enabled ? 'plg.sigma =' : 'Sigma'"
        :class="api_hints_enabled ? 'api-hint' : null"
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
      <plugin-switch
        :value.sync="unnormalize"
        label="Un-normalize"
        api_hint="plg.unnormalize ="
        :api_hints_enabled="api_hints_enabled"
        hint="Whether to multiply the flattened light curve by the median of the trend."
        persistent-hint
      />
    </v-row>

    <v-row v-if="show_live_preview && !unnormalize">
      <v-alert type="warning">Live preview is unnormalized, but flattening will normalize.</v-alert>
    </v-row>

    <plugin-auto-label
      :value.sync="flux_label_label"
      :default="flux_label_default"
      :auto.sync="flux_label_auto"
      :invalid_msg="flux_label_invalid_msg"
      hint="Label for flux column."
      api_hint="plg.flux_label ="
      :api_hints_enabled="api_hints_enabled"
    ></plugin-auto-label>

    <plugin-previews-temp-disabled
      :previews_temp_disabled.sync="previews_temp_disabled"
      :previews_last_time="previews_last_time"
      :show_live_preview="show_live_preview || show_trend_preview"
      @disable_previews="() => {show_live_preview=false; show_trend_preview=false}"
    />

    <v-row justify="end">
      <j-tooltip tooltipcontent="Flatten and select the new column as the adopted flux column">
        <plugin-action-button 
          :spinner="spinner"
          :disabled="flux_label_invalid_msg.length > 0"
          :results_isolated_to_plugin="false"
          :class="api_hints_enabled ? 'api-hint' : null"
          @click="apply">
            {{ api_hints_enabled ?
              'plg.flatten(add_data=True)'
              :
              'Flatten'+(flux_label_overwrite ? ' (Overwrite)' : '') 
             }}
        </plugin-action-button>
      </j-tooltip>
    </v-row>

    <v-row v-if="flatten_err">
      <span class="v-messages v-messages__message text--secondary">
        <b style="color: red !important">ERROR:</b> {{flatten_err}}
      </span>
    </v-row>

  </j-tray-plugin>
</template>
