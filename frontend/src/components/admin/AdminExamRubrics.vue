<template>
  <div>
    <h3 class="h6">Evaluation rubric</h3>
    <p class="small text-muted">Rubric marks used: {{ total }} of {{ exam.maximum_marks }}</p>
    <AlertBox :error="error" />

    <div class="table-responsive">
      <table class="table table-sm align-middle">
        <thead class="table-light">
          <tr><th>Criterion</th><th>Max marks</th><th>Weightage</th><th>Description</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="r in rubrics" :key="r.id">
            <td>{{ r.criterion_name }}</td>
            <td>{{ r.max_marks }}</td>
            <td>{{ r.weightage }}</td>
            <td>{{ r.description }}</td>
            <td class="text-nowrap">
              <button class="btn btn-sm btn-outline-secondary me-1" @click="edit(r)">Edit</button>
              <button class="btn btn-sm btn-outline-danger" @click="remove(r)">Delete</button>
            </td>
          </tr>
          <tr v-if="!rubrics.length"><td colspan="5" class="text-muted">No criteria yet.</td></tr>
        </tbody>
      </table>
    </div>

    <form class="row g-2 align-items-end" @submit.prevent="save">
      <div class="col-md-3">
        <label class="form-label small mb-0">Criterion</label>
        <input v-model="form.criterion_name" class="form-control form-control-sm" required />
      </div>
      <div class="col-md-2">
        <label class="form-label small mb-0">Max marks</label>
        <input v-model.number="form.max_marks" type="number" min="1" class="form-control form-control-sm" required />
      </div>
      <div class="col-md-2">
        <label class="form-label small mb-0">Weightage</label>
        <input v-model.number="form.weightage" type="number" min="0" class="form-control form-control-sm" required />
      </div>
      <div class="col-md-3">
        <label class="form-label small mb-0">Description</label>
        <input v-model="form.description" class="form-control form-control-sm" required />
      </div>
      <div class="col-md-2 d-flex gap-1">
        <button class="btn btn-sm btn-primary" type="submit">{{ form.id ? 'Save' : 'Add' }}</button>
        <button v-if="form.id" class="btn btn-sm btn-outline-secondary" type="button" @click="reset">Cancel</button>
      </div>
    </form>
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import { adminApi } from '@/api/http'

const blank = () => ({ id: null, criterion_name: '', max_marks: 10, weightage: 0, description: '' })

export default {
  name: 'AdminExamRubrics',
  components: { AlertBox },
  props: { exam: { type: Object, required: true } },
  data() {
    return { rubrics: [], form: blank(), error: '' }
  },
  computed: {
    total() {
      return this.rubrics.reduce((sum, r) => sum + r.max_marks, 0)
    }
  },
  watch: {
    'exam.id': {
      immediate: true,
      handler() {
        this.reset()
        this.load()
      }
    }
  },
  methods: {
    async load() {
      try {
        this.rubrics = await adminApi.get(`/api/exams/${this.exam.id}/rubrics`)
      } catch (e) {
        this.error = e.message
      }
    },
    reset() {
      this.form = blank()
      this.error = ''
    },
    edit(r) {
      this.form = { ...r }
      this.error = ''
    },
    async save() {
      this.error = ''
      const f = this.form
      const body = { criterion_name: f.criterion_name, max_marks: f.max_marks, weightage: f.weightage, description: f.description }
      try {
        if (f.id) await adminApi.put(`/api/admin/rubrics/${f.id}`, body)
        else await adminApi.post(`/api/admin/exams/${this.exam.id}/rubrics`, body)
        this.form = blank()
        await this.load()
      } catch (e) {
        this.error = e.message
      }
    },
    async remove(r) {
      if (!confirm(`Delete criterion "${r.criterion_name}"?`)) return
      this.error = ''
      try {
        await adminApi.del(`/api/admin/rubrics/${r.id}`)
        await this.load()
      } catch (e) {
        this.error = e.message
      }
    }
  }
}
</script>
