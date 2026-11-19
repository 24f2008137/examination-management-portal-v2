<template>
  <div>
    <div class="d-flex gap-2 mb-3">
      <select v-model="filter" class="form-select" style="max-width: 220px" @change="load">
        <option value="pending">Pending evaluations</option>
        <option value="all">All booked students</option>
      </select>
    </div>

    <AlertBox :error="error" />

    <div class="table-responsive">
      <table class="table table-hover align-middle">
        <thead class="table-light">
          <tr><th>Student</th><th>Exam</th><th>Exam date</th><th>Booking</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="b in rows" :key="b.booking_id">
            <td>{{ b.student_name }}</td>
            <td>{{ b.exam_name }}</td>
            <td>{{ b.exam_date }}</td>
            <td><StatusBadge :status="b.booking_status" /></td>
            <td>
              <button v-if="b.booking_status === 'Booked'" class="btn btn-sm btn-primary" @click="open(b, false)">Evaluate</button>
              <button v-else-if="b.booking_status === 'Completed'" class="btn btn-sm btn-outline-secondary" @click="open(b, true)">View evaluation</button>
            </td>
          </tr>
          <tr v-if="!loading && !rows.length"><td colspan="5" class="text-muted">Nothing to show.</td></tr>
        </tbody>
      </table>
    </div>

    <EvaluationForm
      v-if="active"
      :key="active.booking.booking_id + String(active.viewOnly)"
      :booking-id="active.booking.booking_id"
      :exam-id="active.booking.exam_id"
      :student-name="active.booking.student_name"
      :view-only="active.viewOnly"
      @done="onDone"
      @close="active = null"
    />
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import EvaluationForm from '@/components/examiner/EvaluationForm.vue'
import { examinerApi } from '@/api/http'

export default {
  name: 'ExaminerEvaluations',
  components: { AlertBox, StatusBadge, EvaluationForm },
  data() {
    return { rows: [], filter: 'pending', loading: true, error: '', active: null }
  },
  mounted() {
    this.load()
  },
  methods: {
    async load() {
      this.error = ''
      try {
        this.rows = await examinerApi.get('/api/examiner/evaluations', { status: this.filter })
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
    open(booking, viewOnly) {
      this.error = ''
      this.active = { booking, viewOnly }
    },
    async onDone() {
      this.active = null
      await this.load()
    }
  }
}
</script>
