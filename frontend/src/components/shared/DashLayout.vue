<template>
  <div>
    <nav class="navbar navbar-dark bg-dark">
      <div class="container-fluid">
        <span class="navbar-brand mb-0 h1">{{ title }}</span>
        <div class="d-flex align-items-center gap-2">
          <span v-if="subtitle" class="text-light small me-2">{{ subtitle }}</span>
          <RouterLink class="btn btn-sm btn-outline-light" to="/">Home</RouterLink>
          <button class="btn btn-sm btn-light" @click="$emit('logout')">Logout</button>
        </div>
      </div>
    </nav>
    <div class="container-fluid py-3">
      <ul class="nav nav-tabs mb-3">
        <li v-for="t in tabs" :key="t.key" class="nav-item">
          <button class="nav-link" :class="{ active: modelValue === t.key }" @click="$emit('update:modelValue', t.key)">
            {{ t.label }}
          </button>
        </li>
      </ul>
      <slot />
    </div>
  </div>
</template>

<script>
import { RouterLink } from 'vue-router'

export default {
  name: 'DashLayout',
  components: { RouterLink },
  props: {
    title: { type: String, required: true },
    subtitle: { type: String, default: '' },
    tabs: { type: Array, required: true },
    modelValue: { type: String, required: true }
  },
  emits: ['update:modelValue', 'logout']
}
</script>
