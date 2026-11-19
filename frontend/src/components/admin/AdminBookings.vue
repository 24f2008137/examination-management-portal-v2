<template>
  <div>
    <div class="d-flex flex-wrap gap-2 mb-3">
      <input v-model="filters.q" class="form-control" style="max-width: 280px" placeholder="Search student, username or exam" @input="debouncedLoad" />
      <select v-model="filters.status" class="form-select" style="max-width: 180px" @change="load">
        <option value="">All statuses</option>
        <option v-for="s in statuses" :key="s">{{ s }}</option>
      </select>
      <select v-model="filters.exam_id" class="form-select" style="max-width: 240px" @change="load">
        <option value="">All exams</option>
        <option v-for="e in exams" :key="e.id" :value="e.id">{{ e.exam_name }}</option>
      </select>
    </div>

    <AlertBox :error="error" :notice="notice" />

    <div class="table-responsive">
      <table class="table table-hover align-middle">
        <thead class="table-light">
          <tr><th>Student</th><th>Exam</th><th>Examiner</th><th>Date</th><th>Booked on</th><th>Status</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="b in bookings" :key="b.booking_id" :class="{ 'table-active': selected && selected.booking_id === b.booking_id }">
            <td>{{ b.student_name }}</td>
            <td>{{ b.exam_name }}</td>
            <td>{{ b.examiner_name }}</td>
            <td>{{ b.exam_date }}</td>
            <td class="small">{{ b.booking_date.slice(0, 16) }}</td>
            <td><StatusBadge :status="b.booking_status" /></td>
            <td>
              <button v-if="b.booking_status === 'Booked'" class="btn btn-sm btn-outline-primary" @click="select(b)">Reschedule</button>
            </td>
          </tr>
          <tr v-if="!loading && !bookings.length"><td colspan="7" class="text-muted">No bookings found.</td></tr>
        </tbody>
      </table>
    </div>

    <div v-if="selected" class="card border-primary">
      <div class="card-header d-flex align-items-center">
        <strong>Move {{ selected.student_name }} to another slot ({{ selected.exam_name }})</strong>
        <button class="btn btn-sm btn-outline-secondary ms-auto" @click="selected = null">Close</button>
      </div>
      <div class="card-body">
        <AlertBox :error="panelError" />
        <p v-if="!options.length" class="text-muted mb-0">No other available slots for this exam.</p>
        <form v-else class="row g-2 align-items-end" @submit.prevent="move">
          <div class="col-md-8">
            <select v-model="newSlot" class="form-select" required>
              <option disabled value="">Select a new slot</option>
              <option v-for="s in options" :key="s.id" :value="s.id">
                {{ s.date }} {{ s.start_time.slice(0, 5) }}-{{ s.end_time.slice(0, 5) }} · {{ s.examiner_name }} · {{ s.available_seats }} seat(s) left
              </option>
            </select>
          </div>
          <div class="col-md-2"><button class="btn btn-primary w-100" type="submit">Move</button></div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import { adminApi } from '@/api/http'

export default {
  name: 'AdminBookings',
  components: { AlertBox, StatusBadge },
  data() {
    return {
      bookings: [], exams: [], allSlots: [],
      statuses: ['Booked', 'Completed', 'Cancelled'],
      filters: { q: '', status: '', exam_id: '' },
      loading: true, error: '', notice: '',
      selected: null, newSlot: '', panelError: '', timer: null
    }
  },
  computed: {
    
    options() {
      if (!this.selected) return []
      const current = this.allSlots.find((s) => s.id === this.selected.slot_id)
      if (!current) return []
      return this.allSlots.filter(
        (s) => s.exam_id === current.exam_id && s.id !== current.id && s.status === 'Available' && s.available_seats > 0
      )
    }
  },
  async mounted() {
    adminApi.get('/api/exams').then((e) => (this.exams = e)).catch(() => {})
    await this.load()
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
        this.bookings = await adminApi.get('/api/admin/bookings', this.filters)
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
    async select(booking) {
      this.selected = booking
      this.newSlot = ''
      this.panelError = ''
      try {
        this.allSlots = await adminApi.get('/api/admin/slots')
      } catch (e) {
        this.panelError = e.message
      }
    },
    async move() {
      this.panelError = ''
      try {
        await adminApi.put(`/api/admin/bookings/${this.selected.booking_id}/reschedule`, { slot_id: this.newSlot })
        this.notice = 'Booking rescheduled.'
        this.selected = null
        await this.load()
      } catch (e) {
        this.panelError = e.message
      }
    }
  }
}
</script>
