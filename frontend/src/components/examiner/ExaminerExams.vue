<template>
  <div>
    <AlertBox :error="error" :notice="notice" />
    <div class="table-responsive">
      <table class="table table-hover align-middle">
        <thead class="table-light">
          <tr>
            <th>Exam</th><th>Course</th><th>Type</th><th>Marks / Duration</th><th>Slot creation window</th>
            <th>My slots</th><th>Booked</th><th>Pending eval.</th><th>Status</th><th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in exams" :key="e.id">
            <td>{{ e.exam_name }}</td>
            <td>{{ e.course_name }}</td>
            <td>{{ e.exam_type }}</td>
            <td>{{ e.maximum_marks }} / {{ e.exam_duration }} min</td>
            <td class="small">{{ e.slot_creation_start_date }} to {{ e.slot_creation_end_date }}</td>
            <td>{{ e.my_slots }}</td>
            <td>{{ e.booked_students }}</td>
            <td>{{ e.pending_evaluations }}</td>
            <td><StatusBadge :status="e.exam_status" /></td>
            <td>
              <button
                class="btn btn-sm btn-outline-success text-nowrap"
                :disabled="e.exam_status !== 'Closed'"
                :title="e.exam_status !== 'Closed' ? 'Available once booking is closed' : ''"
                @click="complete(e)"
              >
                Mark completed
              </button>
            </td>
          </tr>
          <tr v-if="!loading && !exams.length"><td colspan="10" class="text-muted">No exams assigned yet.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import { examinerApi } from '@/api/http'

export default {
  name: 'ExaminerExams',
  components: { AlertBox, StatusBadge },
  data() {
    return { exams: [], loading: true, error: '', notice: '' }
  },
  mounted() {
    this.load()
  },
  methods: {
    async load() {
      try {
        this.exams = await examinerApi.get('/api/examiner/exams')
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
    async complete(exam) {
      if (!confirm(`Mark "${exam.exam_name}" as completed?`)) return
      this.error = ''
      this.notice = ''
      try {
        const data = await examinerApi.put(`/api/examiner/exams/${exam.id}/complete`)
        this.notice = data.message || 'Exam marked as completed.'
        await this.load()
      } catch (e) {
        this.error = e.message
      }
    }
  }
}
</script>
