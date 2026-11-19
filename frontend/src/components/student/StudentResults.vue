<template>
  <div>
    <AlertBox :error="error" />
    <p v-if="loading" class="text-muted">Loading...</p>
    <p v-else-if="!results.length && !error" class="text-muted">No results have been published yet.</p>

    <div class="row g-3">
      <div v-for="(r, i) in results" :key="i" class="col-lg-6">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <h2 class="h5 mb-0">{{ r.exam_name }}</h2>
                <div class="small text-muted">{{ r.exam_date }}</div>
              </div>
              <span class="badge text-bg-primary fs-6">{{ r.marks }} marks</span>
            </div>
            <table class="table table-sm mt-3 mb-2">
              <thead class="table-light"><tr><th>Criterion</th><th>Marks</th></tr></thead>
              <tbody>
                <tr v-for="s in r.scores" :key="s.criterion_name">
                  <td>{{ s.criterion_name }}</td>
                  <td>{{ s.marks_obtained }} / {{ s.max_marks }}</td>
                </tr>
              </tbody>
            </table>
            <p class="mb-0"><strong>Examiner feedback:</strong> {{ r.remarks || 'No remarks.' }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import { studentApi } from '@/api/http'

export default {
  name: 'StudentResults',
  components: { AlertBox },
  data() {
    return { results: [], loading: true, error: '' }
  },
  async mounted() {
    try {
      this.results = await studentApi.get('/api/student/results')
    } catch (e) {
      this.error = e.message
    } finally {
      this.loading = false
    }
  }
}
</script>
