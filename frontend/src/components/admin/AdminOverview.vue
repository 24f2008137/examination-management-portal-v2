<template>
  <div>
    <AlertBox :error="error" :notice="notice" />
    <p v-if="loading" class="text-muted">Loading...</p>

    <div v-if="stats" class="row g-3 mb-4">
      <div v-for="c in cards" :key="c.key" class="col-6 col-md-3">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <div class="fs-2 fw-semibold">{{ stats[c.key] }}</div>
            <div class="text-muted small">{{ c.label }}</div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="report" class="row g-4">
      <div class="col-lg-7">
        <h2 class="h5">Reports per exam</h2>
        <p class="small text-muted">
          Bookings: {{ report.booked }} booked · {{ report.completed }} completed · {{ report.cancelled }} cancelled
        </p>
        <div class="table-responsive">
          <table class="table table-sm table-hover align-middle">
            <thead class="table-light">
              <tr><th>Exam</th><th>Bookings</th><th>Completed</th><th>Cancelled</th><th>Evaluations</th></tr>
            </thead>
            <tbody>
              <tr v-for="e in report.exam_reports" :key="e.exam_id">
                <td>{{ e.exam_name }}</td>
                <td>{{ e.total_bookings }}</td>
                <td>{{ e.completed_bookings }}</td>
                <td>{{ e.cancelled_bookings }}</td>
                <td>{{ e.evaluations }}</td>
              </tr>
              <tr v-if="!report.exam_reports.length"><td colspan="5" class="text-muted">No exams yet.</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="col-lg-5">
        <h2 class="h5">Background jobs</h2>
        <div class="card shadow-sm">
          <div class="card-body">
            <p class="small text-muted">Run the scheduled jobs on demand (useful for demos).</p>
            <button class="btn btn-outline-primary btn-sm mb-3" :disabled="jobBusy" @click="runDaily">
              Send daily reminders now
            </button>
            <div class="row g-2 align-items-end">
              <div class="col-5">
                <label class="form-label small mb-0">Year</label>
                <input v-model="reportYear" type="number" class="form-control form-control-sm" placeholder="e.g. 2026" />
              </div>
              <div class="col-3">
                <label class="form-label small mb-0">Month</label>
                <input v-model="reportMonth" type="number" min="1" max="12" class="form-control form-control-sm" />
              </div>
              <div class="col-4">
                <button class="btn btn-outline-primary btn-sm w-100" :disabled="jobBusy" @click="runMonthly">
                  Monthly report
                </button>
              </div>
            </div>
            <div class="form-text">Leave year and month empty to use the default period.</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import { adminApi } from '@/api/http'

export default {
  name: 'AdminOverview',
  components: { AlertBox },
  data() {
    return {
      stats: null,
      report: null,
      loading: true,
      error: '',
      notice: '',
      jobBusy: false,
      reportYear: '',
      reportMonth: '',
      cards: [
        { key: 'total_courses', label: 'Courses' },
        { key: 'total_exams', label: 'Examinations' },
        { key: 'total_students', label: 'Students' },
        { key: 'total_examiners', label: 'Examiners' },
        { key: 'total_slots', label: 'Exam slots' },
        { key: 'total_bookings', label: 'Bookings' },
        { key: 'pending_evaluations', label: 'Pending evaluations' },
        { key: 'completed_evaluations', label: 'Completed evaluations' }
      ]
    }
  },
  async mounted() {
    try {
      const [dash, rep] = await Promise.all([adminApi.get('/api/admin/dashboard'), adminApi.get('/api/admin/reports')])
      this.stats = dash
      this.report = rep
    } catch (e) {
      this.error = e.message
    } finally {
      this.loading = false
    }
  },
  methods: {
    async runJob(path, body) {
      this.error = ''
      this.notice = ''
      this.jobBusy = true
      try {
        const data = await adminApi.post(path, body)
        this.notice = data.message
      } catch (e) {
        this.error = e.message
      } finally {
        this.jobBusy = false
      }
    },
    runDaily() {
      return this.runJob('/api/admin/jobs/daily-reminders')
    },
    runMonthly() {
      const body = this.reportYear || this.reportMonth ? { year: this.reportYear, month: this.reportMonth } : {}
      return this.runJob('/api/admin/jobs/monthly-report', body)
    }
  }
}
</script>
