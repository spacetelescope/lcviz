<template>
    <j-viewer-creator
      :title="viewer_type"
      :popout_button="popout_button"
      :dataset_items="dataset_items"
      v-model:dataset_selected="dataset_selected"
      :dataset_multiselect="true"
      v-model:viewer_label_value="viewer_label_value"
      :viewer_label_default="viewer_label_default"
      v-model:viewer_label_auto="viewer_label_auto"
      :viewer_label_invalid_msg="viewer_label_invalid_msg"
      :api_hints_enabled="api_hints_enabled"
      @create-clicked="create_clicked"
    >
      <plugin-ephemeris-select
        :items="ephemeris_items"
        v-model:selected="ephemeris_selected"
        :show_if_single_entry="true"
        label="Ephemeris"
        api_hint="vc.ephemeris ="
        :api_hints_enabled="api_hints_enabled"
        hint="Select the ephemeris."
      />
    </j-viewer-creator>
  </template>