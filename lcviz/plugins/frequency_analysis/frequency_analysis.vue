<template>
  <j-tray-plugin
    :config="config"
    plugin_key="Frequency Analysis"
    :api_hints_enabled.sync="api_hints_enabled"
    :description="docs_description"
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

    <plugin-select
      :items="method_items.map(i => i.label)"
      :selected.sync="method_selected"
      label="Algorithm/Method"
      api_hint="plg.method ="
      :api_hints_enabled="api_hints_enabled"
      :hint="'Method to determine power at each '+xunit_selected+'.'"
    />

    <plugin-select
      :items="xunit_items.map(i => i.label)"
      :selected.sync="xunit_selected"
      label="X Units"
      api_hint="plg.xunit ="
      :api_hints_enabled="api_hints_enabled"
      hint="Whether to plot in frequency or period-space."
    />

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

  </j-tray-plugin>
</template>
