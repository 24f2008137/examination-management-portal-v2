<template>
  <div class="border rounded p-3 mt-3">
    <h3 class="h6">{{ viewOnly ? 'Evaluation' : 'Evaluate' }}: {{ studentName }}</h3>
    <AlertBox :error="error" />
    <p v-if="loading" class="text-muted mb-0">Loading...</p>

    <template v-else-if="viewOnly && evaluation">
      <table class="table table-sm">
        <thead class="table-light"><tr><th>Criterion</th><th>Marks</th></tr></thead>
        <tbody>
          <tr v-for="s in evaluation.scores" :key="s.rubric_id">
            <td>{{ s.criterion_name }}</td>
            <td>{{ s.marks }} / {{ s.max_marks }}</td>
          </tr>
        </tbody>
        <tfoot><tr><th>Total</th><th>{{ evaluation.marks }}</th></tr></tfoot>
      </table>
      <p class="mb-2"><strong>Remarks:</strong> {{ evaluation.remarks || '-' }}</p>
      <button class="btn btn-sm btn-outline-secondary" @click="$emit('close')">Close</button>
    </template>

    
    <form v-else-if="!viewOnly" @submit.prevent="submit">
      <p v-if="!rubrics.length" class="text-danger small">This exam has no rubric yet, so it cannot be evaluated.</p>
      <div v-for="r in rubrics" :key="r.id" class="row g-2 align-items-center mb-2">
        <div class="col-md-5">
          <div class="fw-semibold">{{ r.criterion_name }}</div>
          <div class="small text-muted">{{ r.description }}</div>
        </div>
        <div class="col-md-3">
          <div class="input-group input-group-sm">
            <input v-model.number="marks[r.id]" type="number" min="0" :max="r.max_marks" step="0.5" class="form-control" required />
            <span class="input-group-text">/ {{ r.max_marks }}</span>
          </div>
        </div>
      </div>
      <div class="mb-3">
        <label class="form-label">Remarks</label>
        <textarea v-model="remarks" rows="2" class="form-control"></textarea>
      </div>
      <div class="d-flex align-items-center gap-2">
        <button class="btn btn-primary btn-sm" type="submit" :disabled="saving || !rubrics.length">Submit marks ({{ total }})</button>
        <button class="btn btn-outline-secondary btn-sm" type="button" @click="$emit('close')">Cancel</button>
      </div>
    </form>
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import { examinerApi } from '@/api/http'

export default {
  name: 'EvaluationForm',
  components: { AlertBox },
  props: {
    bookingId: { type: Number, required: true },
    examId: { type: Number, required: true },
    studentName: { type: String, default: '' },
    viewOnly: { type: Boolean, default: false }
  },
  emits: ['done', 'close'],
  data() {
    return { rubrics: [], evaluation: null, marks: {}, remarks: '', loading: true, saving: false, error: '' }
  },
  computed: {
    total() {
      return this.rubrics.reduce((sum, r) => sum + (Number(this.marks[r.id]) || 0), 0)
    }
  },
  async mounted() {
    try {
      if (this.viewOnly) {
        this.evaluation = await examinerApi.get(`/api/examiner/bookings/${this.bookingId}/evaluation`)
      } else {
        this.rubrics = await examinerApi.get(`/api/exams/${this.examId}/rubrics`)
      }
    } catch (e) {
      this.error = e.message
    } finally {
      this.loading = false
    }
  },
  methods: {
    async submit() {
      this.error = ''
      this.saving = true
      try {
        await examinerApi.post(`/api/examiner/bookings/${this.bookingId}/evaluate`, {
          scores: this.rubrics.map((r) => ({ rubric_id: r.id, marks: this.marks[r.id] })),
          remarks: this.remarks
        })
        this.$emit('done')
      } catch (e) {
        this.error = e.message
      } finally {
        this.saving = false
      }
    }
  }
}
</script>
