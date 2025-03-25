<template>
  <j-tray-plugin
    :config="config"
    plugin_key="Ephemeris"
    :api_hints_enabled.sync="api_hints_enabled"
    :description="docs_description || 'Find and refine ephemerides for phase-folding.'"
    :link="'https://lcviz.readthedocs.io/en/'+vdocs+'/plugins.html#ephemeris'"
    :popout_button="popout_button">

    <plugin-editable-select
      :mode.sync="component_mode"
      :edit_value.sync="component_edit_value"
      :items="component_items"
      :selected.sync="component_selected"
      label="Component"
      api_hint="plg.component ="
      api_hint_add="plg.add_component"
      api_hint_rename="plg.rename_component"
      api_hint_remove="plg.remove_component"
      :api_hints_enabled="api_hints_enabled"
      hint="Select an ephemeris component."
      >
    </plugin-editable-select>

    <v-row justify="end">
      <v-btn
        color="primary" 
        text
        :class="api_hints_enabled ? 'api-hint' : null"
        @click="create_phase_viewer"
        :disabled="phase_viewer_exists || component_selected.length == 0"
      >
        {{ api_hints_enabled ? 
          'plg.create_phase_viewer()'
          :
          'Show Phase Viewer'
        }}
      </v-btn>
    </v-row>

    <div v-if="component_items.length > 0">
      <j-plugin-section-header>Ephemeris</j-plugin-section-header>

      <v-row>
        <v-text-field
          ref="t0"
          type="number"
          :label="api_hints_enabled ? 'plg.t0 =' : 'Zeropoint (t0)'"
          :class="api_hints_enabled ? 'api-hint' : null"
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
          :label="api_hints_enabled ? 'plg.period =' : 'Period'"
          :class="api_hints_enabled ? 'api-hint' : null"
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
          :label="api_hints_enabled ? 'plg.dpdt =' : 'Period derivative'"
          :class="api_hints_enabled ? 'api-hint' : null"
          v-model.number="dpdt"
          :step="dpdt_step"
          hint="The first time-derivative of the period of the ephemeris."
          persistent-hint
          :rules="[() => dpdt!=='' || 'This field is required']"
        ></v-text-field>
      </v-row>

      <v-row>
        <v-text-field
          ref="wrap_at"
          type="number"
          :label="api_hints_enabled ? 'plg.wrap_at =' : 'Wrapping phase'"
          :class="api_hints_enabled ? 'api-hint' : null"
          v-model.number="wrap_at"
          :step="0.1"
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
        hint="Method to determine period."
      />

      <div style="display: grid"> <!-- overlay container -->
        <div style="grid-area: 1/1">

          <v-row v-if="method_err.length > 0">
            <v-alert color="warning">{{ method_err }}</v-alert>
          </v-row>
          <v-row v-else>
            <j-tooltip :tooltipcontent="'adopt period into '+component_selected+' ephemeris.'">
              <v-btn
                text
                color='primary'
                :class="api_hints_enabled ? 'api-hint' : null"
                @click='adopt_period_at_max_power'
                style="padding: 0px"
              >
                {{ api_hints_enabled ? 
                  'plg.adopt_period_at_max_power()'
                  :
                  'period: '+period_at_max_power
                }}
                
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

      <j-plugin-section-header>Query NASA Exoplanet Archive</j-plugin-section-header>
      <v-row>
        <span class="v-messages v-messages__message text--secondary">
          Query the
          <a href="https://exoplanetarchive.ipac.caltech.edu/docs/pscp_about.html" target="_blank">
          Planetary Systems Composite Data</a> table from
          <a href="https://exoplanetarchive.ipac.caltech.edu/" target="_blank">
          NASA Exoplanet Archive</a>. Queries first by name, then falls back on
          coordinates if the object name is not recognized.
        </span>
      </v-row>

      <v-row>
        <v-text-field
          ref="query_name"
          type="string"
          :label="api_hints_enabled ? 'plg.query_name =' : 'Object name'"
          :class="api_hints_enabled ? 'api-hint' : null"
          v-model.number="query_name"
          hint="Object name."
          persistent-hint
        ></v-text-field>
      </v-row>
      <v-row>
        <v-text-field
          ref="query_ra"
          type="number"
          :label="api_hints_enabled ? 'plg.query_ra =' : 'RA (degrees)'"
          :class="api_hints_enabled ? 'api-hint' : null"
          v-model.number="query_ra"
          :step="ra_dec_step"
          hint="Object right ascension."
          persistent-hint
        ></v-text-field>
      </v-row>
      <v-row>
        <v-text-field
          ref="query_dec"
          type="number"
          :label="api_hints_enabled ? 'plg.query_dec =' : 'Dec (degrees)'"
          :class="api_hints_enabled ? 'api-hint' : null"
          v-model.number="query_dec"
          :step="ra_dec_step"
          hint="Object declination."
          persistent-hint
        ></v-text-field>
      </v-row>
      <v-row>
        <v-text-field
          ref="query_radius"
          type="number"
          :label="api_hints_enabled ? 'plg.query_radius =' : 'Radius (arcseconds)'"
          :class="api_hints_enabled ? 'api-hint' : null"
          v-model.number="query_radius"
          :step="1"
          hint="Radius around the query coordinate."
          persistent-hint
        ></v-text-field>
      </v-row>

      <v-row justify="end">
        <j-tooltip tooltipcontent="Query for this object.">
          <plugin-action-button
            :spinner="query_spinner"
            :results_isolated_to_plugin="false"
            :api_hints_enabled="api_hints_enabled"
            @click="query_for_ephemeris">
              {{ api_hints_enabled ? 
                'plg.query_for_ephemeris()'
                :
                'Query'
              }} 
          </plugin-action-button>
        </j-tooltip>
      </v-row>
      <div v-if="query_result_items.length > 0">
        <v-row>
          <v-select
            :menu-props="{ left: true }"
            attach
            :items="query_result_items"
            :item-value="item => item.label"
            v-model="query_result_selected"
            :label="api_hints_enabled ? 'plg.query_result =' : 'Ephemerides available'"
            :class="api_hints_enabled ? 'api-hint' : null"
            :hint="'Ephemeris parameters from ' + query_result_items.length + ' available query result(s)'"
            persistent-hint
            dense
          >

          <template v-slot:selection="{ item }">
            <span v-if="api_hints_enabled" class="api-hint">
              '{{ item.label }}'
            </span>
            <span v-else>
              {{ item.label }}
            </span>
          </template>
          <template v-slot:item="{ item }">
            <span style="margin-top: 8px; margin-bottom: 0px">
              <span v-if="api_hints_enabled" class="api-hint">
                '{{ item.label }}'
              </span>
              <span v-else>
                {{ item.label }}
              </span>
              <v-row style="line-height: 1.0; margin: 0px; opacity: 0.85; font-size: 8pt">
                Period: {{ item.period }} d, Epoch: {{ item.epoch }} d
              </v-row>
            </span>
          </template>

          </v-select>
        </v-row>

        <v-row v-if="query_result_selected !== ''">
          <span class="v-messages v-messages__message text--secondary">
            Period: {{period_from_catalog}} d, Epoch: {{t0_from_catalog}} d
          </span>
          <j-tooltip :tooltipcontent="'Adopt period and epoch into '+component_selected+' ephemeris.'">
            <v-row justify="end">
            <v-col>
              <plugin-action-button
                @click="create_ephemeris_from_query"
                :class="api_hints_enabled ? 'api-hint' : null"
                :disabled="component_items.map(item => item.label).includes(query_result_selected.replace(/\s/g, ''))">
                  {{ api_hints_enabled ?
                    'plg.create_ephemeris_from_query()'
                    :
                    'Create new component'
                   }}  
              </plugin-action-button>
            </v-col>
            </v-row>
          </j-tooltip>
        </v-row>
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
