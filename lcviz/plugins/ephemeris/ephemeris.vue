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

    <j-plugin-section-header>Ephemeris</j-plugin-section-header>

    <v-row>
      <v-text-field
        ref="period"
        type="number"
        label="Period"
        v-model.number="period"
        type="number"
        hint="The period of the ephemeris."
        persistent-hint
        :rules="[() => !!period || 'This field is required',
                 () => period > 0 || 'Period must be greater than zero']"
      ></v-text-field>
    </v-row>

    <v-row>
      <v-text-field
        ref="t0"
        type="number"
        label="Zeropoint (t0)"
        v-model.number="t0"
        type="number"
        hint="The zero-point of the ephemeris."
        persistent-hint
        :rules="[() => !!t0 || 'This field is required']"
      ></v-text-field>
    </v-row>

  </j-tray-plugin>
</template>
