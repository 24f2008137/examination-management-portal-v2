<template>
  <div>
    <div class="mb-3">
      <input v-model="search" class="form-control" style="max-width: 320px" placeholder="Search by name, department or username" @input="debouncedLoad" />
    </div>

    <AlertBox :error="error" />

    <div class="table-responsive">
      <table class="table table-hover align-middle">
        <thead class="table-light">
          <tr><th>Name</th><th>Username</th><th>Department</th><th>Contact</th><th>Status</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="s in students" :key="s.id" :class="{ 'table-active': selected && selected.id === s.id }">
            <td>{{ s.name }}</td>
            <td>{{ s.username }}</td>
            <td>{{ s.department }}</td>
            <td>{{ s.contact_details }}</td>
            <td><StatusBadge :status="s.status" /></td>
            <td class="text-nowrap">
              <button class="btn btn-sm btn-outline-secondary me-1" @click="showHistory(s)">History</button>
              <button class="btn btn-sm btn-outline-secondary" @click="toggle(s)">
                {{ s.status === 'Active' ? 'Deactivate' : 'Activate' }}
              </button>
            </td>
          </tr>
          <tr v-if="!loading && !students.length"><td colspan="6" class="text-muted">No students found.</td></tr>
        </tbody>
      </table>
    </div>

    <div v-if="selected" class="card border-primary">
      <div class="card-header d-flex align-items-center">
        <strong>Exam history: {{ selected.name }}</strong>
        <button class="btn btn-sm btn-outline-secondary ms-auto" @click="selected = null">Close</button>
      </div>
      <div class="card-body">
        <AlertBox :error="historyError" />
        <div class="table-responsive">
          <table class="table table-sm align-middle mb-0">
            <thead class="table-light">
              <tr><th>Exam</th><th>Date</th><th>Examiner</th><th>Booking</th><th>Marks</th><th>Remarks</th></tr>
            </thead>
            <tbody>
              <tr v-for="h in history" :key="h.booking_id">
                <td>{{ h.exam_name }}</td>
                <td>{{ h.exam_date }}</td>
                <td>{{ h.examiner }}</td>
                <td><StatusBadge :status="h.booking_status" /></td>
                <td>{{ h.evaluation ? h.evaluation.marks : '-' }}</td>
                <td>{{ h.evaluation ? h.evaluation.remarks : '' }}</td>
              </tr>
              <tr v-if="!history.length"><td colspan="6" class="text-muted">No bookings yet.</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import { adminApi } from '@/api/http'

export default {
  name: 'AdminStudents',
  components: { AlertBox, StatusBadge },
  data() {
    return { students: [], search: '', loading: true, error: '', selected: null, history: [], historyError: '', timer: null }
  },
  mounted() {
    this.load()
  },
  beforeUnmount() {
    clearTimeout(this.timer)
  },
  methods: {
    debouncedLoad() {
      clearTimeout(this.timer)
      this.timer = setTimeout(this.load, 300)
    },
    async load() {
      this.error = ''
      try {
        this.students = await adminApi.get('/api/admin/students', { q: this.search })
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
    async toggle(s) {
      this.error = ''
      try {
        await adminApi.put(`/api/admin/students/${s.id}/status`, { status: s.status === 'Active' ? 'Inactive' : 'Active' })
        await this.load()
      } catch (e) {
        this.error = e.message
      }
    },
    async showHistory(s) {
      this.selected = s
      this.history = []
      this.historyError = ''
      try {
        this.history = await adminApi.get(`/api/admin/students/${s.id}/history`)
      } catch (e) {
        this.historyError = e.message
      }
    }
  }
}
</script>
