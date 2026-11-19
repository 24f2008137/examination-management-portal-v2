<template>
  <div class="card border-primary mt-3">
    <div class="card-header d-flex align-items-center">
      <strong>Students booked: {{ slotInfo.exam_name }} · {{ slotInfo.date }} {{ slotInfo.start_time.slice(0, 5) }}</strong>
      <button class="btn btn-sm btn-outline-secondary ms-auto" @click="$emit('close')">Close</button>
    </div>
    <div class="card-body">
      <AlertBox :error="error" />
      <div class="table-responsive">
        <table class="table table-sm align-middle">
          <thead class="table-light">
            <tr><th>Student</th><th>Department</th><th>Contact</th><th>Booking</th><th>Marks</th><th></th></tr>
          </thead>
          <tbody>
            <tr v-for="b in bookings" :key="b.booking_id">
              <td>{{ b.student_name }}</td>
              <td>{{ b.department }}</td>
              <td>{{ b.contact_details }}</td>
              <td><StatusBadge :status="b.booking_status" /></td>
              <td>{{ b.marks === null ? '-' : b.marks }}</td>
              <td class="text-nowrap">
                <button v-if="b.booking_status === 'Booked' && !b.evaluated" class="btn btn-sm btn-primary" @click="open(b, false)">Evaluate</button>
                <button v-else-if="b.evaluated" class="btn btn-sm btn-outline-secondary" @click="open(b, true)">View evaluation</button>
              </td>
            </tr>
            <tr v-if="!bookings.length"><td colspan="6" class="text-muted">No students have booked this slot.</td></tr>
          </tbody>
        </table>
      </div>

      <EvaluationForm
        v-if="active"
        :key="active.booking.booking_id + String(active.viewOnly)"
        :booking-id="active.booking.booking_id"
        :exam-id="slotInfo.exam_id"
        :student-name="active.booking.student_name"
        :view-only="active.viewOnly"
        @done="onDone"
        @close="active = null"
      />
    </div>
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import EvaluationForm from '@/components/examiner/EvaluationForm.vue'
import { examinerApi } from '@/api/http'

export default {
  name: 'ExaminerSlotBookings',
  components: { AlertBox, StatusBadge, EvaluationForm },
  props: { slotInfo: { type: Object, required: true } },
  emits: ['changed', 'close'],
  data() {
    return { bookings: [], error: '', active: null }
  },
  mounted() {
    this.load()
  },
  methods: {
    async load() {
      try {
        this.bookings = await examinerApi.get(`/api/examiner/slots/${this.slotInfo.id}/bookings`)
      } catch (e) {
        this.error = e.message
      }
    },
    open(booking, viewOnly) {
      this.active = { booking, viewOnly }
    },
    async onDone() {
      this.active = null
      await this.load()
      this.$emit('changed')
    }
  }
}
</script>
