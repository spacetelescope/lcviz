<template>
  <div>
  <v-row v-if="items.length > 1 || show_if_single_entry || api_hints_enabled">
    <v-select
      :menu-props="{ left: true }"
      attach
      :items="items"
      v-model="selected"
      @change="$emit('update:selected', $event)"
      :label="api_hints_enabled && api_hint ? api_hint : (label ? label : 'Ephemeris')"
      :class="api_hints_enabled ? 'api-hint' : null"
      :hint="hint ? hint : 'Select ephemeris.'"
      :rules="rules ? rules : []"
      item-text="label"
      item-value="label"
      persistent-hint
    >
    <template slot="selection" slot-scope="data">
      <div class="single-line">
        <span v-if="api_hints_enabled" class="api-hint">
          '{{selected}}'
        </span>
        <span v-else>
          {{ data.item.label }}
        </span>
      </div>
    </template>
    <template slot="item" slot-scope="data">
      <div class="single-line">
        <span>
          {{ data.item.label }}
        </span>
      </div>
    </template>
   </v-select>
  </v-row>
 </div>
</template>
<script>
module.exports = {
  props: ['items', 'selected', 'label', 'hint', 'rules', 'show_if_single_entry',
          'api_hint', 'api_hints_enabled']
};
</script>

<style>
  .v-select__selections {
    flex-wrap: nowrap !important;
  }
  .single-line {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
  }
</style>
