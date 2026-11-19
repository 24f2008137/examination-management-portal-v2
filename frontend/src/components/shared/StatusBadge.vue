<template>
  <span class="badge" :class="'text-bg-' + color">{{ status }}</span>
</template>

<script>
const COLORS = {
  Active: 'success', Available: 'success', Booked: 'primary', Evaluated: 'success',
  Completed: 'success', 'Booking Open': 'success', Processing: 'info', 'Slot Creation': 'info',
  Draft: 'secondary', Pending: 'secondary', Closed: 'warning', Full: 'warning',
  Inactive: 'danger', Cancelled: 'danger', Failed: 'danger'
}

export default {
  name: 'StatusBadge',
  props: { status: { type: String, default: '' } },
  computed: {
    color() {
      return COLORS[this.status] || 'secondary'
    }
  }
}
</script>
