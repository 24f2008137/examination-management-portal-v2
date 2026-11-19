<template>
  <div>
    <h3 class="h6">Assigned examiners</h3>
    <AlertBox :error="error" :notice="notice" />
    <p v-if="!examiners.length" class="text-muted small">No active examiners available. Add one in the Examiners tab.</p>
    <div class="row g-2">
      <div v-for="x in examiners" :key="x.id" class="col-md-4">
        <div class="form-check">
          <input :id="'ex' + x.id" v-model="selected" class="form-check-input" type="checkbox" :value="x.id" />
          <label class="form-check-label" :for="'ex' + x.id">
            {{ x.name }} <span class="text-muted small">({{ x.department || 'no department' }})</span>
          </label>
        </div>
      </div>
    </div>
    <button class="btn btn-sm btn-primary mt-2" :disabled="saving" @click="save">Save assignment</button>
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import { adminApi } from '@/api/http'

export default {
  name: 'AdminExamExaminers',
  components: { AlertBox },
  props: { examId: { type: Number, required: true } },
  data() {
    return { examiners: [], selected: [], error: '', notice: '', saving: false }
  },
  watch: {
    examId: {
      immediate: true,
      handler() {
        this.load()
      }
    }
  },
  methods: {
    async load() {
      this.error = ''
      this.notice = ''
      try {
        const [all, assigned] = await Promise.all([
          adminApi.get('/api/admin/examiners'),
          adminApi.get(`/api/admin/exams/${this.examId}/examiners`)
        ])
        this.selected = assigned.map((x) => x.id)
        // only active examiners can be assigned, but keep already-assigned ones visible
        this.examiners = all.filter((x) => x.status === 'Active' || this.selected.includes(x.id))
      } catch (e) {
        this.error = e.message
      }
    },
    async save() {
      this.saving = true
      this.error = ''
      this.notice = ''
      try {
        await adminApi.put(`/api/admin/exams/${this.examId}/examiners`, { examiner_ids: this.selected })
        this.notice = 'Assignment saved.'
      } catch (e) {
        this.error = e.message
      } finally {
        this.saving = false
      }
    }
  }
}
</script>
