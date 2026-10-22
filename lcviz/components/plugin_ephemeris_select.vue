<template>
  <div>
  <v-row v-if="items.length > 1 || show_if_single_entry || api_hints_enabled">
    <v-select
      :menu-props="{ location: 'bottom start' }"
      attach
      :items="items"
      :model-value="selected"
      @update:modelValue="$emit('update:selected', $event)"
      :label="api_hints_enabled && api_hint ? api_hint : (label ? label : 'Ephemeris')"
      :class="api_hints_enabled ? 'api-hint' : null"
      :hint="hint ? hint : 'Select ephemeris.'"
      :rules="rules ? rules : []"
      item-title="label"
      item-value="label"
      persistent-hint
    >
    <template #selection="{ item }">
      <div class="single-line">
        <span v-if="api_hints_enabled" class="api-hint">
          '{{selected}}'
        </span>
        <span v-else>
          {{ item.raw.label }}
        </span>
      </div>
    </template>
    <template #item="{ props, item }">
      <v-list-item v-bind="props" :title="undefined" class="single-line">
        <span>
          {{ item.raw.label }}
        </span>
      </v-list-item>
    </template>
   </v-select>
  </v-row>
 </div>
</template>
<script>
export default {
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
