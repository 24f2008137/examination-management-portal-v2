<template>
  <div>
    <div class="d-flex flex-wrap gap-2 mb-3">
      <input v-model="search" class="form-control" style="max-width: 280px" placeholder="Search exams by name" @input="debouncedLoad" />
      <select v-model="statusFilter" class="form-select" style="max-width: 200px" @change="load">
        <option value="">All statuses</option>
        <option v-for="s in statuses" :key="s">{{ s }}</option>
      </select>
      <button class="btn btn-outline-secondary" title="Reload the list (e.g. after an examiner completes an exam)" @click="load">Refresh</button>
      <button class="btn btn-primary ms-auto" @click="openForm()">+ New exam</button>
    </div>

    <form v-if="showForm" class="card card-body bg-light mb-3" @submit.prevent="save">
      <h2 class="h5">{{ form.id ? 'Edit exam' : 'New exam' }}</h2>
      <div class="row g-3">
        <div class="col-md-4">
          <label class="form-label">Course</label>
          <select v-model="form.course_id" class="form-select" required>
            <option disabled value="">Select a course</option>
            <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.course_code }} - {{ c.course_name }}</option>
          </select>
        </div>
        <div class="col-md-4">
          <label class="form-label">Exam name</label>
          <input v-model="form.exam_name" class="form-control" required />
        </div>
        <div class="col-md-4">
          <label class="form-label">Exam type</label>
          <select v-model="form.exam_type" class="form-select" required>
            <option disabled value="">Select a type</option>
            <option v-for="t in typeOptions" :key="t">{{ t }}</option>
          </select>
        </div>
        <div class="col-md-3">
          <label class="form-label">Duration (minutes)</label>
          <input v-model.number="form.exam_duration" type="number" min="1" class="form-control" required />
        </div>
        <div class="col-md-3">
          <label class="form-label">Maximum marks</label>
          <input v-model.number="form.maximum_marks" type="number" min="1" class="form-control" required />
        </div>
        <div class="col-md-3">
          <label class="form-label">Slot creation starts</label>
          <input v-model="form.slot_creation_start_date" type="date" class="form-control" required />
        </div>
        <div class="col-md-3">
          <label class="form-label">Slot creation ends</label>
          <input v-model="form.slot_creation_end_date" type="date" class="form-control" required />
        </div>
        <div class="col-md-3">
          <label class="form-label">Booking starts</label>
          <input v-model="form.slot_booking_start_date" type="date" class="form-control" required />
        </div>
        <div class="col-md-3">
          <label class="form-label">Booking ends</label>
          <input v-model="form.slot_booking_end_date" type="date" class="form-control" required />
        </div>
        <div class="col-12">
          <label class="form-label">Instructions</label>
          <textarea v-model="form.exam_instructions" rows="2" class="form-control"></textarea>
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
          <tr>
            <th>Exam</th><th>Course</th><th>Type</th><th>Marks / Duration</th>
            <th>Slot creation</th><th>Booking</th><th>Status</th><th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in exams" :key="e.id" :class="{ 'table-active': managing && managing.id === e.id }">
            <td>{{ e.exam_name }}</td>
            <td>{{ e.course_name }}</td>
            <td>{{ e.exam_type }}</td>
            <td>{{ e.maximum_marks }} / {{ e.exam_duration }} min</td>
            <td class="small">{{ e.slot_creation_start_date }}<br />to {{ e.slot_creation_end_date }}</td>
            <td class="small">{{ e.slot_booking_start_date }}<br />to {{ e.slot_booking_end_date }}</td>
            <td>
              <StatusBadge :status="e.exam_status" />
              <span v-if="e.results_published" class="badge text-bg-success ms-1">Results published</span>
            </td>
            <td class="text-nowrap">
              <button class="btn btn-sm btn-primary me-1" @click="manage(e)">Manage</button>
              <button class="btn btn-sm btn-outline-secondary me-1" @click="openForm(e)">Edit</button>
              <button class="btn btn-sm btn-outline-danger" @click="remove(e)">Delete</button>
            </td>
          </tr>
          <tr v-if="!loading && !exams.length"><td colspan="8" class="text-muted">No exams found.</td></tr>
        </tbody>
      </table>
    </div>

    <div v-if="managing" class="card border-primary mt-3">
      <div class="card-header d-flex flex-wrap align-items-center gap-2">
        <strong>{{ managing.exam_name }}</strong>
        <StatusBadge :status="managing.exam_status" />
        <div class="ms-auto d-flex flex-wrap gap-2">
          <button
            v-for="t in transitions[managing.exam_status]"
            :key="t.to"
            class="btn btn-sm btn-outline-primary"
            @click="changeStatus(t.to)"
          >
            {{ t.label }}
          </button>
          <button
            class="btn btn-sm btn-success"
            :disabled="managing.exam_status !== 'Completed' || managing.results_published"
            @click="publish"
          >
            {{ managing.results_published ? 'Results published' : 'Publish results' }}
          </button>
          <button class="btn btn-sm btn-outline-secondary" @click="managing = null">Close</button>
        </div>
      </div>
      <div class="card-body">
        <AlertBox :error="panelError" />
        <AdminExamExaminers :exam-id="managing.id" />
        <hr />
        <AdminExamRubrics :exam="managing" />
      </div>
    </div>
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import AdminExamRubrics from '@/components/admin/AdminExamRubrics.vue'
import AdminExamExaminers from '@/components/admin/AdminExamExaminers.vue'
import { adminApi } from '@/api/http'

const blank = () => ({
  id: null, course_id: '', exam_name: '', exam_type: '', exam_duration: 30, maximum_marks: 100,
  slot_creation_start_date: '', slot_creation_end_date: '', slot_booking_start_date: '', slot_booking_end_date: '',
  exam_instructions: ''
})

export default {
  name: 'AdminExams',
  components: { AlertBox, StatusBadge, AdminExamRubrics, AdminExamExaminers },
  data() {
    return {
      exams: [],
      courses: [],
      statuses: ['Draft', 'Slot Creation', 'Booking Open', 'Closed', 'Completed'],
      examTypes: ['Viva', 'Assessment'],
      // quick actions per status: open/close slot creation and student booking
      transitions: {
        Draft: [{ to: 'Slot Creation', label: 'Open slot creation' }],
        'Slot Creation': [
          { to: 'Booking Open', label: 'Close slot creation & open booking' },
          { to: 'Draft', label: 'Back to Draft' }
        ],
        'Booking Open': [{ to: 'Closed', label: 'Close booking' }],
        Closed: [
          { to: 'Booking Open', label: 'Reopen booking' },
          { to: 'Completed', label: 'Mark completed' }
        ],
        Completed: []
      },
      search: '',
      statusFilter: '',
      loading: true,
      error: '',
      notice: '',
      showForm: false,
      form: blank(),
      formError: '',
      saving: false,
      managing: null,
      panelError: '',
      timer: null
    }
  },
  computed: {
    typeOptions() {
      const t = this.form.exam_type
      return t && !this.examTypes.includes(t) ? [...this.examTypes, t] : this.examTypes
    }
  },
  async mounted() {
    adminApi.get('/api/admin/courses').then((c) => (this.courses = c)).catch((e) => (this.error = e.message))
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
        this.exams = await adminApi.get('/api/exams', { q: this.search, status: this.statusFilter })
        if (this.managing) this.managing = this.exams.find((e) => e.id === this.managing.id) || null
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
    async openForm(exam) {
      this.formError = ''
      this.notice = ''
      this.showForm = true
      if (!exam) {
        this.form = blank()
        return
      }
      try {
        // the list has no instructions, so fetch the full exam
        const data = await adminApi.get(`/api/exams/${exam.id}`)
        this.form = { ...blank(), ...data, exam_instructions: data.exam_instructions || '' }
      } catch (e) {
        this.formError = e.message
      }
    },
    async save() {
      this.saving = true
      this.formError = ''
      const f = this.form
      const body = {
        course_id: f.course_id, exam_name: f.exam_name, exam_type: f.exam_type,
        exam_duration: f.exam_duration, maximum_marks: f.maximum_marks,
        slot_creation_start_date: f.slot_creation_start_date, slot_creation_end_date: f.slot_creation_end_date,
        slot_booking_start_date: f.slot_booking_start_date, slot_booking_end_date: f.slot_booking_end_date,
        exam_instructions: f.exam_instructions
      }
      try {
        if (f.id) await adminApi.put(`/api/admin/exams/${f.id}`, body)
        else await adminApi.post('/api/admin/exams', body)
        this.notice = f.id ? 'Exam updated.' : 'Exam created (status: Draft).'
        this.showForm = false
        await this.load()
      } catch (e) {
        this.formError = e.message
      } finally {
        this.saving = false
      }
    },
    async remove(exam) {
      if (!confirm(`Delete exam "${exam.exam_name}"?`)) return
      this.error = ''
      this.notice = ''
      try {
        await adminApi.del(`/api/admin/exams/${exam.id}`)
        this.notice = 'Exam deleted.'
        await this.load()
      } catch (e) {
        this.error = e.message
      }
    },
    manage(exam) {
      this.managing = exam
      this.panelError = ''
    },
    async changeStatus(status) {
      this.panelError = ''
      try {
        await adminApi.put(`/api/admin/exams/${this.managing.id}/status`, { exam_status: status })
        await this.load()
      } catch (e) {
        this.panelError = e.message
      }
    },
    async publish() {
      this.panelError = ''
      try {
        await adminApi.post(`/api/admin/exams/${this.managing.id}/publish`)
        await this.load()
      } catch (e) {
        this.panelError = e.message
      }
    }
  }
}
</script>
