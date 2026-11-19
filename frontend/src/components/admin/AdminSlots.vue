<template>
  <div>
    <div class="d-flex flex-wrap gap-2 mb-3">
      <select v-model="filters.exam_id" class="form-select" style="max-width: 240px" @change="load">
        <option value="">All exams</option>
        <option v-for="e in exams" :key="e.id" :value="e.id">{{ e.exam_name }}</option>
      </select>
      <select v-model="filters.examiner_id" class="form-select" style="max-width: 220px" @change="load">
        <option value="">All examiners</option>
        <option v-for="x in examiners" :key="x.id" :value="x.id">{{ x.name }}</option>
      </select>
      <select v-model="filters.status" class="form-select" style="max-width: 180px" @change="load">
        <option value="">All statuses</option>
        <option v-for="s in statuses" :key="s">{{ s }}</option>
      </select>
    </div>

    <AlertBox :error="error" :notice="notice" />

    <div class="table-responsive">
      <table class="table table-hover align-middle">
        <thead class="table-light">
          <tr><th>Exam</th><th>Examiner</th><th>Date</th><th>Time</th><th>Seats</th><th>Status</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="s in slots" :key="s.id" :class="{ 'table-active': selected && selected.id === s.id }">
            <td>{{ s.exam_name }}</td>
            <td>{{ s.examiner_name }}</td>
            <td>{{ s.date }}</td>
            <td>{{ s.start_time.slice(0, 5) }} - {{ s.end_time.slice(0, 5) }}</td>
            <td>{{ s.available_seats }} / {{ s.maximum_student_capacity }}</td>
            <td><StatusBadge :status="s.status" /></td>
            <td><button class="btn btn-sm btn-outline-primary" @click="select(s)">Reschedule / reassign</button></td>
          </tr>
          <tr v-if="!loading && !slots.length"><td colspan="7" class="text-muted">No slots found.</td></tr>
        </tbody>
      </table>
    </div>

    <div v-if="selected" class="card border-primary">
      <div class="card-header d-flex align-items-center">
        <strong>{{ selected.exam_name }} · {{ selected.date }}</strong>
        <button class="btn btn-sm btn-outline-secondary ms-auto" @click="selected = null">Close</button>
      </div>
      <div class="card-body">
        <AlertBox :error="panelError" :notice="panelNotice" />
        <div class="row g-4">
          <form class="col-lg-7" @submit.prevent="reschedule">
            <h3 class="h6">Reschedule slot</h3>
            <div class="row g-2 align-items-end">
              <div class="col-md-4">
                <label class="form-label small mb-0">Date</label>
                <input v-model="resched.date" type="date" class="form-control form-control-sm" required />
              </div>
              <div class="col-md-3">
                <label class="form-label small mb-0">Start</label>
                <input v-model="resched.start_time" type="time" class="form-control form-control-sm" required />
              </div>
              <div class="col-md-3">
                <label class="form-label small mb-0">End</label>
                <input v-model="resched.end_time" type="time" class="form-control form-control-sm" required />
              </div>
              <div class="col-md-2"><button class="btn btn-sm btn-primary w-100" type="submit">Save</button></div>
            </div>
          </form>
          <form class="col-lg-5" @submit.prevent="reassign">
            <h3 class="h6">Change examiner</h3>
            <div class="row g-2 align-items-end">
              <div class="col-8">
                <select v-model="newExaminer" class="form-select form-select-sm" required>
                  <option disabled value="">Select an examiner</option>
                  <option v-for="x in assigned" :key="x.id" :value="x.id">{{ x.name }}</option>
                </select>
              </div>
              <div class="col-4"><button class="btn btn-sm btn-primary w-100" type="submit">Reassign</button></div>
            </div>
            <div class="form-text">Only examiners assigned to this exam can be chosen.</div>
          </form>
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
  name: 'AdminSlots',
  components: { AlertBox, StatusBadge },
  data() {
    return {
      slots: [], exams: [], examiners: [], assigned: [],
      statuses: ['Available', 'Full', 'Cancelled', 'Completed'],
      filters: { exam_id: '', examiner_id: '', status: '' },
      loading: true, error: '', notice: '',
      selected: null, resched: { date: '', start_time: '', end_time: '' }, newExaminer: '',
      panelError: '', panelNotice: ''
    }
  },
  async mounted() {
    adminApi.get('/api/exams').then((e) => (this.exams = e)).catch(() => {})
    adminApi.get('/api/admin/examiners').then((x) => (this.examiners = x)).catch(() => {})
    await this.load()
  },
  methods: {
    async load() {
      this.error = ''
      try {
        this.slots = await adminApi.get('/api/admin/slots', this.filters)
        if (this.selected) this.selected = this.slots.find((s) => s.id === this.selected.id) || null
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
    async select(slot) {
      this.selected = slot
      this.panelError = ''
      this.panelNotice = ''
      this.newExaminer = ''
      this.resched = { date: slot.date, start_time: slot.start_time.slice(0, 5), end_time: slot.end_time.slice(0, 5) }
      try {
        this.assigned = await adminApi.get(`/api/admin/exams/${slot.exam_id}/examiners`)
      } catch (e) {
        this.panelError = e.message
      }
    },
    async reschedule() {
      this.panelError = ''
      this.panelNotice = ''
      try {
        await adminApi.put(`/api/admin/slots/${this.selected.id}/reschedule`, this.resched)
        this.panelNotice = 'Slot rescheduled.'
        await this.load()
      } catch (e) {
        this.panelError = e.message
      }
    },
    async reassign() {
      this.panelError = ''
      this.panelNotice = ''
      try {
        await adminApi.put(`/api/admin/slots/${this.selected.id}/examiner`, { examiner_id: this.newExaminer })
        this.panelNotice = 'Examiner reassigned.'
        await this.load()
      } catch (e) {
        this.panelError = e.message
      }
    }
  }
}
</script>
