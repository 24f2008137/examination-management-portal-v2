<template>
  <div>
    <div class="d-flex flex-wrap gap-2 mb-3">
      <input v-model="filters.q" class="form-control" style="max-width: 280px" placeholder="Search examinations" @input="debouncedLoad" />
      <select v-model="filters.type" class="form-select" style="max-width: 190px" @change="load">
        <option value="">All types</option>
        <option v-for="t in types" :key="t">{{ t }}</option>
      </select>
      <select v-model="filters.status" class="form-select" style="max-width: 190px" @change="load">
        <option value="">All statuses</option>
        <option v-for="s in statuses" :key="s">{{ s }}</option>
      </select>
    </div>

    <AlertBox :error="error" :notice="notice" />

    <div class="table-responsive">
      <table class="table table-hover align-middle">
        <thead class="table-light">
          <tr><th>Exam</th><th>Course</th><th>Type</th><th>Marks / Duration</th><th>Booking window</th><th>Status</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="e in exams" :key="e.id" :class="{ 'table-active': selected && selected.id === e.id }">
            <td>{{ e.exam_name }}</td>
            <td>{{ e.course_name }}</td>
            <td>{{ e.exam_type }}</td>
            <td>{{ e.maximum_marks }} / {{ e.exam_duration }} min</td>
            <td class="small">{{ e.slot_booking_start_date }} to {{ e.slot_booking_end_date }}</td>
            <td><StatusBadge :status="e.exam_status" /></td>
            <td>
              <button class="btn btn-sm btn-primary text-nowrap" @click="selected = e">
                {{ e.exam_status === 'Booking Open' ? 'View & book' : 'View details' }}
              </button>
            </td>
          </tr>
          <tr v-if="!loading && !exams.length"><td colspan="7" class="text-muted">No examinations found.</td></tr>
        </tbody>
      </table>
    </div>

    <StudentExamDetail v-if="selected" :key="selected.id" :exam="selected" @booked="onBooked" @close="selected = null" />
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import StudentExamDetail from '@/components/student/StudentExamDetail.vue'
import { studentApi } from '@/api/http'

export default {
  name: 'StudentExams',
  components: { AlertBox, StatusBadge, StudentExamDetail },
  data() {
    return {
      exams: [],
      types: ['Viva', 'Assessment'],
      statuses: ['Slot Creation', 'Booking Open', 'Closed', 'Completed'],
      filters: { q: '', type: '', status: '' },
      loading: true, error: '', notice: '', selected: null, timer: null
    }
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
        this.exams = await studentApi.get('/api/exams', this.filters)
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
    onBooked() {
      this.notice = 'Slot booked. You can see it under My bookings.'
      this.selected = null
    }
  }
}
</script>
