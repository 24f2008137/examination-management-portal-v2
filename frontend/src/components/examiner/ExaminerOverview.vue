<template>
  <div>
    <AlertBox :error="error" />
    <p v-if="loading" class="text-muted">Loading...</p>
    <template v-if="stats">
      <h2 class="h5 mb-3">Welcome, {{ stats.examiner_name }}</h2>
      <div class="row g-3">
        <div v-for="c in cards" :key="c.key" class="col-6 col-md-4 col-lg-2">
          <div class="card shadow-sm h-100">
            <div class="card-body">
              <div class="fs-2 fw-semibold">{{ stats[c.key] }}</div>
              <div class="text-muted small">{{ c.label }}</div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import { examinerApi } from '@/api/http'

export default {
  name: 'ExaminerOverview',
  components: { AlertBox },
  data() {
    return {
      stats: null,
      loading: true,
      error: '',
      cards: [
        { key: 'total_assigned_exams', label: 'Assigned exams' },
        { key: 'total_slots', label: 'Slots created' },
        { key: 'total_bookings', label: 'Booked students' },
        { key: 'pending_evaluations', label: 'Pending evaluations' },
        { key: 'completed_evaluations', label: 'Completed evaluations' }
      ]
    }
  },
  async mounted() {
    try {
      this.stats = await examinerApi.get('/api/examiner/dashboard')
    } catch (e) {
      this.error = e.message
    } finally {
      this.loading = false
    }
  }
}
</script>
