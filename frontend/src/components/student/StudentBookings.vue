<template>
  <div>
    <AlertBox :error="error" :notice="notice" />
    <div class="table-responsive">
      <table class="table table-hover align-middle">
        <thead class="table-light">
          <tr><th>Exam</th><th>Date</th><th>Time</th><th>Examiner</th><th>Booked on</th><th>Status</th><th>Meeting</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="b in bookings" :key="b.booking_id">
            <td>{{ b.exam_name }}</td>
            <td>{{ b.exam_date }}</td>
            <td>{{ b.start_time.slice(0, 5) }} - {{ b.end_time.slice(0, 5) }}</td>
            <td>{{ b.examiner_name }}</td>
            <td class="small">{{ b.booking_date.slice(0, 16) }}</td>
            <td><StatusBadge :status="b.booking_status" /></td>
            <td>
              <a v-if="b.meeting_link" :href="b.meeting_link" target="_blank" rel="noopener">Join</a>
            </td>
            <td>
              <button v-if="b.can_cancel" class="btn btn-sm btn-outline-danger" @click="cancel(b)">Cancel</button>
            </td>
          </tr>
          <tr v-if="!loading && !bookings.length"><td colspan="8" class="text-muted">You have no bookings yet.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import { studentApi } from '@/api/http'

export default {
  name: 'StudentBookings',
  components: { AlertBox, StatusBadge },
  data() {
    return { bookings: [], loading: true, error: '', notice: '' }
  },
  mounted() {
    this.load()
  },
  methods: {
    async load() {
      try {
        this.bookings = await studentApi.get('/api/student/bookings')
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
    async cancel(b) {
      if (!confirm(`Cancel your booking for ${b.exam_name}?`)) return
      this.error = ''
      this.notice = ''
      try {
        const data = await studentApi.del(`/api/student/bookings/${b.booking_id}`)
        this.notice = data.message
        await this.load()
      } catch (e) {
        this.error = e.message
      }
    }
  }
}
</script>
