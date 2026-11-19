<template>
  <div>
    <AlertBox :error="error" />
    <p v-if="loading" class="text-muted">Loading...</p>

    <template v-if="stats">
      <h2 class="h5 mb-3">Welcome, {{ stats.student_name }}</h2>
      <div class="row g-3 mb-4">
        <div v-for="c in cards" :key="c.key" class="col-6 col-md-4 col-lg-2">
          <div class="card shadow-sm h-100">
            <div class="card-body">
              <div class="fs-2 fw-semibold">{{ stats[c.key] }}</div>
              <div class="text-muted small">{{ c.label }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="row g-4">
        <div class="col-lg-7">
          <h2 class="h5">Upcoming examinations</h2>
          <div class="table-responsive">
            <table class="table table-sm table-hover align-middle">
              <thead class="table-light"><tr><th>Exam</th><th>Date</th><th>Start</th><th>Examiner</th></tr></thead>
              <tbody>
                <tr v-for="u in stats.upcoming_exams" :key="u.booking_id">
                  <td>{{ u.exam_name }}</td>
                  <td>{{ u.exam_date }}</td>
                  <td>{{ u.start_time.slice(0, 5) }}</td>
                  <td>{{ u.examiner_name }}</td>
                </tr>
                <tr v-if="!stats.upcoming_exams.length"><td colspan="4" class="text-muted">No upcoming examinations.</td></tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="col-lg-5">
          <StudentExport />
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import StudentExport from '@/components/student/StudentExport.vue'
import { studentApi } from '@/api/http'

export default {
  name: 'StudentOverview',
  components: { AlertBox, StudentExport },
  data() {
    return {
      stats: null,
      loading: true,
      error: '',
      cards: [
        { key: 'available_exams', label: 'Available exams' },
        { key: 'available_slots', label: 'Available slots' },
        { key: 'total_bookings', label: 'Total bookings' },
        { key: 'completed_exams', label: 'Completed exams' },
        { key: 'published_results', label: 'Published results' }
      ]
    }
  },
  async mounted() {
    try {
      this.stats = await studentApi.get('/api/student/dashboard')
    } catch (e) {
      this.error = e.message
    } finally {
      this.loading = false
    }
  }
}
</script>
