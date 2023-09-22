<template>
  <j-tray-plugin
    description='Find and refine ephemerides for phase-folding.'
    :link="'https://lcviz.readthedocs.io/en/'+vdocs+'/plugins.html#ephemeris'"
    :popout_button="popout_button">

    <plugin-editable-select
      :mode.sync="component_mode"
      :edit_value.sync="component_edit_value"
      :items="component_items"
      :selected.sync="component_selected"
      label="Component"
      hint="Select an ephemeris component."
      >
    </plugin-editable-select>

    <v-row justify="end">
      <v-btn color="primary" text @click="create_phase_viewer" :disabled="phase_viewer_exists || component_selected.length == 0">
        Show Phase Viewer
      </v-btn>
    </v-row>

    <div v-if="component_items.length > 0">
      <j-plugin-section-header>Ephemeris</j-plugin-section-header>

      <v-row>
        <v-text-field
          ref="t0"
          type="number"
          label="Zeropoint (t0)"
          v-model.number="t0"
          :step="t0_step"
          type="number"
          hint="Time at zero-phase of the ephemeris."
          persistent-hint
          :rules="[() => t0!=='' || 'This field is required']"
        ></v-text-field>
      </v-row>

      <v-row>
        <v-text-field
          ref="period"
          type="number"
          label="Period"
          v-model.number="period"
          :step="period_step"
          hint="The period of the ephemeris, defined at t0."
          persistent-hint
          :rules="[() => period!=='' || 'This field is required',
                   () => period > 0 || 'Period must be greater than zero']"
        >
          <template v-slot:append>
            <j-tooltip tooltipcontent="halve period">
              <v-icon style="cursor: pointer" @click="period_halve">mdi-division</v-icon>
            </j-tooltip>
            <j-tooltip tooltipcontent="double period">
              <v-icon style="cursor: pointer" @click="period_double">mdi-multiplication</v-icon>
            </j-tooltip>
          </template>
        </v-text-field>
      </v-row>

      <v-row>
        <v-text-field
          ref="dpdt"
          type="number"
          label="Period derivative"
          v-model.number="dpdt"
          :step="dpdt_step"
          type="number"
          hint="The first time-derivative of the period of the ephemeris."
          persistent-hint
          :rules="[() => dpdt!=='' || 'This field is required']"
        ></v-text-field>
      </v-row>

      <v-row>
        <v-text-field
          ref="wrap_at"
          type="number"
          label="Wrapping phase"
          v-model.number="wrap_at"
          :step="0.1"
          type="number"
          :hint="'Phased data will encompass the range '+wrap_at_range+'.'"
          persistent-hint
          :rules="[() => wrap_at!=='' || 'This field is required']"
        ></v-text-field>
      </v-row>

      <j-plugin-section-header>Period Finding/Refining</j-plugin-section-header>

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
          hint="Method to determine period."
          persistent-hint
        ></v-select>
      </v-row>



      <div style="display: grid"> <!-- overlay container -->
        <div style="grid-area: 1/1">

          <v-row v-if="method_err.length > 0">
            <v-alert color="warning">{{ method_err }}</v-alert>
          </v-row>
          <v-row v-else>
            <j-tooltip :tooltipcontent="'adopt period into '+component_selected+' ephemeris.'">
              <v-btn text color='primary '@click='adopt_period_at_max_power' style="padding: 0px">
                period: {{period_at_max_power}}
              </v-btn>
            </j-tooltip>
          </v-row>

        </div>
        <div v-if="method_spinner"
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

<script>
module.exports = {
  computed: {
    wrap_at_range() {
      const lower = this.wrap_at - 1
      return '('+lower.toFixed(2)+', '+this.wrap_at.toFixed(2)+')'
    },
  }
};
</script>
