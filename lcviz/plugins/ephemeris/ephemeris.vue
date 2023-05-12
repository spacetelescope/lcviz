<template>
  <j-tray-plugin
    description='Find and refine ephemerides for phase-folding.'
    :link="'https://lcviz.readthedocs.io/en/'+vdocs+'/plugins.html#ephemeris'"
    :popout_button="popout_button">

    <v-row>
      <v-select
        attach
        :menu-props="{ left: true }"
        :items="component_items.map(i => i.label)"
        v-model="component_selected"
        label="Component"
        hint="Select an ephemeris component."
        persistent-hint
      ></v-select>
    </v-row>

    <v-row justify="end">
      <v-btn color="primary" text @click="create_phase_viewer" :disabled="phase_viewer_exists">
        Show Phase Viewer
      </v-btn>
    </v-row>

    <j-plugin-section-header>Ephemeris</j-plugin-section-header>

    <v-row>
      <v-text-field
        ref="t0"
        type="number"
        label="Zeropoint (t0)"
        v-model.number="t0"
        :step="t0_step"
        type="number"
        hint="The zero-point of the ephemeris."
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
        ref="t0"
        type="number"
        label="Period derivative (dpdt)"
        v-model.number="dpdt"
        :step="dpdt_step"
        type="number"
        hint="The first time derivative of the period of the ephemeris."
        persistent-hint
        :rules="[() => dpdt!=='' || 'This field is required']"
      ></v-text-field>
    </v-row>

  </j-tray-plugin>
</template>
