<template>
  <div>
    <div v-if="error" class="alert alert-danger py-2" role="alert">{{ error }}</div>
    <div v-if="notice" class="alert alert-success py-2" role="alert">{{ notice }}</div>
  </div>
</template>

<script>
export default {
  name: 'AlertBox',
  props: {
    error: { type: String, default: '' },
    notice: { type: String, default: '' }
  }
}
</script>
