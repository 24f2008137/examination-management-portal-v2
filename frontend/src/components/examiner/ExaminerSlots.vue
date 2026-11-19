<template>
  <div>
    <div class="d-flex mb-3">
      <button class="btn btn-primary ms-auto" @click="openForm()">+ New slots</button>
    </div>

    <form v-if="showForm" class="card card-body bg-light mb-3" @submit.prevent="save">
      <h2 class="h5">{{ form.id ? 'Edit slot' : 'New slot' }}</h2>
      <div class="row g-3">
        <div class="col-md-4">
          <label class="form-label">Exam</label>
          <select v-model="form.exam_id" class="form-select" :disabled="!!form.id" required>
            <option disabled value="">Select an exam</option>
            <option v-for="e in openExams" :key="e.id" :value="e.id">{{ e.exam_name }}</option>
          </select>
          <div v-if="!openExams.length && !form.id" class="form-text text-danger">
            No assigned exam is currently in the Slot Creation stage.
          </div>
          <div v-else-if="chosenExam" class="form-text">
            Slots can be created between {{ chosenExam.slot_creation_start_date }} and {{ chosenExam.slot_creation_end_date }}.
          </div>
        </div>
        <div class="col-md-2">
          <label class="form-label">Date</label>
          <input v-model="form.date" type="date" class="form-control" required />
        </div>
        <div class="col-md-2">
          <label class="form-label">{{ isVivaBulk ? 'Window start' : 'Start' }}</label>
          <input v-model="form.start_time" type="time" class="form-control" required />
        </div>
        <div class="col-md-2">
          <label class="form-label">{{ isVivaBulk ? 'Window end' : 'End' }}</label>
          <input v-model="form.end_time" type="time" class="form-control" required />
        </div>
        <div v-if="!isViva" class="col-md-2">
          <label class="form-label">Capacity</label>
          <input v-model.number="form.maximum_student_capacity" type="number" min="1" class="form-control" required />
        </div>
        <template v-if="isVivaBulk">
          <div class="col-md-2">
            <label class="form-label">Break start <span class="text-muted">(optional)</span></label>
            <input v-model="form.break_start" type="time" class="form-control" />
          </div>
          <div class="col-md-2">
            <label class="form-label">Break end</label>
            <input v-model="form.break_end" type="time" class="form-control" :required="!!form.break_start" />
          </div>
          <div class="col-12">
            <div class="form-text mb-1">
              Viva: slots are generated automatically, {{ chosenExam.exam_duration }} min each, 1 student per slot.
            </div>
            <div v-if="preview.length" class="d-flex flex-wrap gap-2">
              <span v-for="p in preview" :key="p" class="badge text-bg-success fw-normal">{{ p }}</span>
              <span class="small text-muted align-self-center">{{ preview.length }} slot{{ preview.length === 1 ? '' : 's' }}</span>
            </div>
            <div v-else-if="form.start_time && form.end_time" class="form-text text-danger">
              This window is too short for one {{ chosenExam.exam_duration }}-minute viva.
            </div>
          </div>
        </template>
        <div v-else-if="isViva" class="col-12 form-text">
          A viva slot is always {{ chosenExam.exam_duration }} minutes with 1 seat.
        </div>
        <div class="col-12">
          <label class="form-label">Meeting link (optional)</label>
          <input v-model="form.meeting_link" class="form-control" placeholder="https://..." />
        </div>
      </div>
      <AlertBox :error="formError" class="mt-3" />
      <div class="d-flex gap-2 mt-3">
        <button class="btn btn-primary" type="submit" :disabled="saving">Save</button>
        <button class="btn btn-outline-secondary" type="button" @click="showForm = false">Cancel</button>
      </div>
    </form>

    <AlertBox :error="error" :notice="notice" />

    <div class="table-responsive">
      <table class="table table-hover align-middle">
        <thead class="table-light">
          <tr><th>Exam</th><th>Date</th><th>Time</th><th>Seats</th><th>Status</th><th>Link</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="s in slots" :key="s.id" :class="{ 'table-active': viewing && viewing.id === s.id }">
            <td>{{ s.exam_name }}</td>
            <td>{{ s.date }}</td>
            <td>{{ s.start_time.slice(0, 5) }} - {{ s.end_time.slice(0, 5) }}</td>
            <td>{{ s.available_seats }} / {{ s.maximum_student_capacity }}</td>
            <td><StatusBadge :status="s.status" /></td>
            <td class="small text-truncate" style="max-width: 160px">{{ s.meeting_link }}</td>
            <td class="text-nowrap">
              <button class="btn btn-sm btn-primary me-1" @click="viewing = s">Students</button>
              <template v-if="s.editable">
                <button class="btn btn-sm btn-outline-secondary me-1" @click="openForm(s)">Edit</button>
                <button class="btn btn-sm btn-outline-danger" @click="remove(s)">Delete</button>
              </template>
            </td>
          </tr>
          <tr v-if="!loading && !slots.length"><td colspan="7" class="text-muted">You have not created any slots yet.</td></tr>
        </tbody>
      </table>
    </div>

    <ExaminerSlotBookings v-if="viewing" :key="viewing.id" :slot-info="viewing" @changed="load" @close="viewing = null" />
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import ExaminerSlotBookings from '@/components/examiner/ExaminerSlotBookings.vue'
import { examinerApi } from '@/api/http'

const blank = () => ({ id: null, exam_id: '', date: '', start_time: '', end_time: '', break_start: '', break_end: '', maximum_student_capacity: 1, meeting_link: '' })

const toMin = (t) => (t ? Number(t.slice(0, 2)) * 60 + Number(t.slice(3, 5)) : null)
const fmt = (m) => String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0')

export default {
  name: 'ExaminerSlots',
  components: { AlertBox, StatusBadge, ExaminerSlotBookings },
  data() {
    return { slots: [], exams: [], loading: true, error: '', notice: '', showForm: false, form: blank(), formError: '', saving: false, viewing: null }
  },
  computed: {
    openExams() {
      return this.exams.filter((e) => e.exam_status === 'Slot Creation')
    },
    chosenExam() {
      return this.exams.find((e) => e.id === this.form.exam_id)
    },
    isViva() {
      return !!this.chosenExam && this.chosenExam.exam_type === 'Viva'
    },
    // creating (not editing) a Viva -> one window is cut into many slots
    isVivaBulk() {
      return this.isViva && !this.form.id
    },
    // same cutting rule as the server, shown live as a preview
    preview() {
      if (!this.isVivaBulk) return []
      const start = toMin(this.form.start_time)
      const end = toMin(this.form.end_time)
      if (start === null || end === null) return []
      const dur = this.chosenExam.exam_duration
      const bs = toMin(this.form.break_start)
      const be = toMin(this.form.break_end)
      const out = []
      let t = start
      while (t + dur <= end) {
        if (bs !== null && be !== null && t < be && t + dur > bs) {
          t = be
          continue
        }
        out.push(`${fmt(t)} - ${fmt(t + dur)}`)
        t += dur
      }
      return out
    }
  },
  async mounted() {
    examinerApi.get('/api/examiner/exams').then((e) => (this.exams = e)).catch(() => {})
    await this.load()
  },
  methods: {
    async load() {
      try {
        this.slots = await examinerApi.get('/api/examiner/slots')
        if (this.viewing) this.viewing = this.slots.find((s) => s.id === this.viewing.id) || null
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
    openForm(slot) {
      this.form = slot
        ? {
            id: slot.id, exam_id: slot.exam_id, date: slot.date,
            start_time: slot.start_time.slice(0, 5), end_time: slot.end_time.slice(0, 5),
            maximum_student_capacity: slot.maximum_student_capacity, meeting_link: slot.meeting_link || ''
          }
        : blank()
      this.formError = ''
      this.notice = ''
      this.showForm = true
    },
    async save() {
      this.saving = true
      this.formError = ''
      const f = this.form
      const body = {
        date: f.date, start_time: f.start_time, end_time: f.end_time,
        maximum_student_capacity: f.maximum_student_capacity, meeting_link: f.meeting_link
      }
      if (this.isVivaBulk && f.break_start && f.break_end) {
        body.break_start = f.break_start
        body.break_end = f.break_end
      }
      try {
        if (f.id) {
          await examinerApi.put(`/api/examiner/slots/${f.id}`, body)
          this.notice = 'Slot updated.'
        } else {
          const res = await examinerApi.post('/api/examiner/slots', { ...body, exam_id: f.exam_id })
          this.notice = res && res.message ? res.message : 'Slot created.'
        }
        this.showForm = false
        await this.load()
      } catch (e) {
        this.formError = e.message
      } finally {
        this.saving = false
      }
    },
    async remove(slot) {
      if (!confirm('Delete this slot?')) return
      this.error = ''
      this.notice = ''
      try {
        await examinerApi.del(`/api/examiner/slots/${slot.id}`)
        if (this.viewing && this.viewing.id === slot.id) this.viewing = null
        this.notice = 'Slot deleted.'
        await this.load()
      } catch (e) {
        this.error = e.message
      }
    }
  }
}
</script>
