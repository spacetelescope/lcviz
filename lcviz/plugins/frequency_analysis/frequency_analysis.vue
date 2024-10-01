<template>
  <j-tray-plugin
    :config="config"
    plugin_key="Frequency Analysis"
    :api_hints_enabled.sync="api_hints_enabled"
    description='Frequency/period analysis.'
    :link="'https://lcviz.readthedocs.io/en/'+vdocs+'/plugins.html#frequency_analysis'"
    :popout_button="popout_button">

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
      <v-select
        :menu-props="{ left: true }"
        attach
        :items="method_items.map(i => i.label)"
        v-model="method_selected"
        :label="api_hints_enabled ? 'plg.method =' : 'Algorithm/Method'"
        :class="api_hints_enabled ? 'api-hint' : null"
        :hint="'Method to determine power at each '+xunit_selected+'.'"
        persistent-hint
      ></v-select>
    </v-row>

    <v-row>
      <v-select
        :menu-props="{ left: true }"
        attach
        :items="xunit_items.map(i => i.label)"
        v-model="xunit_selected"
        :label="api_hints_enabled ? 'plg.xunit =' : 'X Units'"
        :class="api_hints_enabled ? 'api-hint' : null"
        hint="Whether to plot in frequency or period-space."
        persistent-hint
      ></v-select>
    </v-row>

    <v-row>
      <plugin-switch
        :value.sync="auto_range"
        :label="'Auto '+xunit_selected+' range'"
        api_hint="plg.auto_range ="
        :api_hints_enabled="api_hints_enabled"
        :hint="'Whether to automatically or manually set the range on sampled '+xunit_selected+'s.'"
        persistent-hint
      />
    </v-row>

    <v-row>
      <v-text-field
        v-if="!auto_range"
        ref="min"
        type="number"
        :label="api_hints_enabled ? 'plg.minimum =' : 'Minimum '+xunit_selected"
        :class="api_hints_enabled ? 'api-hint' : null"
        v-model.number="minimum"
        :step="minimum_step"
        type="number"
        :hint="'Minimum '+xunit_selected+' to search.'"
        persistent-hint
        :rules="[() => minimum!=='' || 'This field is required']"
      ></v-text-field>
    </v-row>

    <v-row>
      <v-text-field
        v-if="!auto_range"
        ref="max"
        type="number"
        :label="api_hints_enabled ? 'plg.maximum =' : 'Maximum '+xunit_selected"
        :class="api_hints_enabled ? 'api-hint' : null"
        v-model.number="maximum"
        :step="maximum_step"
        type="number"
        :hint="'Maximum '+xunit_selected+' to search.'"
        persistent-hint
        :rules="[() => maximum!=='' || 'This field is required']"
      ></v-text-field>
    </v-row>

    <v-row v-if="api_hints_enabled">
        <span class="api-hint">
          plg.periodogram
        </span>
    </v-row>

    <div style="display: grid"> <!-- overlay container -->
      <div style="grid-area: 1/1">

        <v-row v-if="err.length > 0">
          <v-alert color="warning">{{ err }}</v-alert>
        </v-row>
        <v-row v-else>
          <jupyter-widget :widget="plot_widget"/> 
        </v-row>

      </div>
      <div v-if="spinner"
           class="text-center"
           style="grid-area: 1/1; 
                  z-index:2;
                  margin-left: -24px;
                  margin-right: -24px;
                  padding-top: 6px;
                  background-color: rgb(0 0 0 / 20%)">
        <v-progress-circular
          indeterminate
          color="spinner"
          size="50"
          width="6"
        ></v-progress-circular>
      </div>
    </div>

  </div>

  </j-tray-plugin>
</template>
