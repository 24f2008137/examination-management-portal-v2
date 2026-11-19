<template>
  <div class="card border-primary mt-3">
    <div class="card-header d-flex align-items-center">
      <strong>{{ exam.exam_name }}</strong>
      <button class="btn btn-sm btn-outline-secondary ms-auto" @click="$emit('close')">Close</button>
    </div>
    <div class="card-body">
      <AlertBox :error="error" />
      <p v-if="loading" class="text-muted">Loading...</p>

      <template v-if="detail">
        <div class="row g-3 mb-3">
          <div class="col-md-6">
            <h3 class="h6">Instructions</h3>
            <p class="mb-0" style="white-space: pre-line">{{ detail.exam_instructions || 'No special instructions.' }}</p>
          </div>
          <div class="col-md-6">
            <h3 class="h6">Evaluation criteria</h3>
            <ul class="mb-0 ps-3">
              <li v-for="r in rubrics" :key="r.id">{{ r.criterion_name }} ({{ r.max_marks }} marks)</li>
              <li v-if="!rubrics.length" class="text-muted list-unstyled">Not published yet.</li>
            </ul>
          </div>
        </div>

        <h3 class="h6">Select a slot</h3>
        <p v-if="exam.exam_status !== 'Booking Open'" class="text-muted small">Slots can be booked only while the exam is in the Booking Open stage.</p>
        <p v-else-if="!slots.length" class="text-muted">No slots have been published for this exam yet.</p>
        <template v-else>
          <!-- date strip -->
          <div class="date-strip mb-3">
            <button
              v-for="d in dates" :key="d.iso" type="button"
              class="date-chip" :class="{ active: d.iso === activeDate }"
              @click="pickDate(d.iso)"
            >
              <span class="small text-uppercase">{{ d.weekday }}</span>
              <span class="fs-4 fw-semibold lh-1">{{ d.day }}</span>
              <span class="small text-uppercase">{{ d.month }}</span>
            </button>
          </div>

          <!-- one row per examiner, time chips like show timings -->
          <div v-for="g in groups" :key="g.examiner_id" class="examiner-row">
            <div class="examiner-name">
              <strong>{{ g.name }}</strong>
              <div class="small text-muted">{{ exam.exam_duration }} min</div>
            </div>
            <div class="d-flex flex-wrap gap-2">
              <button
                v-for="s in g.slots" :key="s.id" type="button"
                class="time-chip" :class="chipClass(s)"
                :disabled="!isBookable(s) || booking"
                @click="selectedId = s.id"
              >
                <span class="fw-semibold">{{ s.start_time.slice(0, 5) }}</span>
                <span class="small">{{ chipNote(s) }}</span>
              </button>
            </div>
          </div>

          <div class="d-flex flex-wrap gap-3 small text-muted mt-3">
            <span><i class="dot dot-ok"></i> Available</span>
            <span><i class="dot dot-few"></i> Filling fast</span>
            <span><i class="dot dot-off"></i> Full / passed</span>
          </div>

          <!-- confirmation bar -->
          <div v-if="selectedSlot" class="confirm-bar mt-3">
            <div>
              <div class="fw-semibold">{{ prettyDate(selectedSlot.date) }}, {{ selectedSlot.start_time.slice(0, 5) }} - {{ selectedSlot.end_time.slice(0, 5) }}</div>
              <div class="small text-muted">with {{ selectedSlot.examiner_name }}</div>
            </div>
            <button class="btn btn-success ms-auto" :disabled="booking" @click="book(selectedSlot)">
              {{ booking ? 'Booking...' : 'Confirm booking' }}
            </button>
          </div>
        </template>
      </template>
    </div>
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import { studentApi } from '@/api/http'

export default {
  name: 'StudentExamDetail',
  components: { AlertBox },
  props: { exam: { type: Object, required: true } },
  emits: ['booked', 'close'],
  data() {
    return { detail: null, rubrics: [], slots: [], loading: true, booking: false, error: '', activeDate: '', selectedId: null }
  },
  async mounted() {
    try {
      const [detail, rubrics, slots] = await Promise.all([
        studentApi.get(`/api/exams/${this.exam.id}`),
        studentApi.get(`/api/exams/${this.exam.id}/rubrics`),
        studentApi.get(`/api/exams/${this.exam.id}/slots`)
      ])
      this.detail = detail
      this.rubrics = rubrics
      this.slots = slots
      this.activeDate = this.dates.length ? this.dates[0].iso : ''
    } catch (e) {
      this.error = e.message
    } finally {
      this.loading = false
    }
  },
  computed: {
    dates() {
      const seen = [...new Set(this.slots.map((s) => s.date))].sort()
      return seen.map((iso) => {
        const [y, m, d] = iso.split('-').map(Number)
        const dt = new Date(y, m - 1, d)
        return {
          iso,
          weekday: dt.toLocaleDateString(undefined, { weekday: 'short' }),
          day: d,
          month: dt.toLocaleDateString(undefined, { month: 'short' })
        }
      })
    },
    // slots of the chosen date, grouped by examiner, sorted by time
    groups() {
      const map = new Map()
      this.slots
        .filter((s) => s.date === this.activeDate)
        .sort((a, b) => a.start_time.localeCompare(b.start_time))
        .forEach((s) => {
          if (!map.has(s.examiner_id)) map.set(s.examiner_id, { examiner_id: s.examiner_id, name: s.examiner_name, slots: [] })
          map.get(s.examiner_id).slots.push(s)
        })
      return [...map.values()]
    },
    selectedSlot() {
      return this.slots.find((s) => s.id === this.selectedId) || null
    }
  },
  methods: {
    pickDate(iso) {
      this.activeDate = iso
      this.selectedId = null
    },
    prettyDate(iso) {
      const [y, m, d] = iso.split('-').map(Number)
      return new Date(y, m - 1, d).toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' })
    },
    hasPassed(slot) {
      const [y, m, d] = slot.date.split('-').map(Number)
      const [hh, mm] = slot.start_time.split(':').map(Number)
      return new Date(y, m - 1, d, hh, mm) <= new Date()
    },
    isBookable(slot) {
      return slot.status === 'Available' && slot.available_seats > 0 && !this.hasPassed(slot)
    },
    chipClass(slot) {
      if (!this.isBookable(slot)) return 'off'
      const few = slot.maximum_student_capacity > 1 && slot.available_seats / slot.maximum_student_capacity <= 0.25
      return [few ? 'few' : 'ok', { picked: slot.id === this.selectedId }]
    },
    chipNote(slot) {
      if (this.hasPassed(slot)) return 'Passed'
      if (slot.status !== 'Available' || slot.available_seats <= 0) return 'Full'
      return slot.maximum_student_capacity > 1 ? `${slot.available_seats} left` : ''
    },
    async book(slot) {
      this.error = ''
      this.booking = true
      try {
        await studentApi.post('/api/student/bookings', { slot_id: slot.id })
        this.$emit('booked')
      } catch (e) {
        this.error = e.message
        this.selectedId = null
        // refresh so a slot someone else just took shows as Full
        try { this.slots = await studentApi.get(`/api/exams/${this.exam.id}/slots`) } catch { /* ignore */ }
      } finally {
        this.booking = false
      }
    }
  }
}
</script>

<style scoped>
.date-strip { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 4px; }
.date-chip {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  min-width: 64px; padding: 8px 10px; border: 1px solid #dee2e6; border-radius: 8px;
  background: #fff; color: #212529; cursor: pointer;
}
.date-chip:hover { border-color: #0d6efd; }
.date-chip.active { background: #0d6efd; border-color: #0d6efd; color: #fff; }

.examiner-row {
  display: flex; flex-wrap: wrap; gap: 12px 24px; align-items: center;
  padding: 12px 0; border-bottom: 1px solid #eee;
}
.examiner-name { min-width: 160px; }

.time-chip {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-width: 84px; min-height: 48px; padding: 4px 12px; border-radius: 6px;
  background: #fff; border: 1px solid; line-height: 1.2; cursor: pointer;
}
.time-chip.ok { border-color: #198754; color: #198754; }
.time-chip.few { border-color: #f59f00; color: #b36b00; }
.time-chip.off { border-color: #ced4da; color: #adb5bd; background: #f8f9fa; cursor: not-allowed; }
.time-chip.ok:hover, .time-chip.few:hover { background: #f1f8f4; }
.time-chip.picked { background: #198754; border-color: #198754; color: #fff; }

.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 4px; }
.dot-ok { background: #198754; }
.dot-few { background: #f59f00; }
.dot-off { background: #ced4da; }

.confirm-bar {
  display: flex; align-items: center; gap: 16px; padding: 12px 16px;
  border: 1px solid #198754; border-radius: 8px; background: #f1f8f4;
}
</style>
