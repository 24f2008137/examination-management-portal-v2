<template>
  <div>
    <div class="d-flex flex-wrap gap-2 mb-3">
      <input v-model="search" class="form-control" style="max-width: 320px" placeholder="Search courses by name" @input="debouncedLoad" />
      <button class="btn btn-primary ms-auto" @click="openForm()">+ New course</button>
    </div>

    <form v-if="showForm" class="card card-body bg-light mb-3" @submit.prevent="save">
      <h2 class="h5">{{ form.id ? 'Edit course' : 'New course' }}</h2>
      <div class="row g-3">
        <div class="col-md-3">
          <label class="form-label">Course code</label>
          <input v-model="form.course_code" class="form-control" required />
        </div>
        <div class="col-md-6">
          <label class="form-label">Course name</label>
          <input v-model="form.course_name" class="form-control" required />
        </div>
        <div class="col-md-3">
          <label class="form-label">Status</label>
          <select v-model="form.course_status" class="form-select">
            <option>Active</option>
            <option>Inactive</option>
          </select>
        </div>
        <div class="col-12">
          <label class="form-label">Description</label>
          <textarea v-model="form.course_description" rows="2" class="form-control" required></textarea>
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
          <tr><th>Code</th><th>Name</th><th>Description</th><th>Status</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="c in courses" :key="c.id">
            <td>{{ c.course_code }}</td>
            <td>{{ c.course_name }}</td>
            <td>{{ c.course_description }}</td>
            <td><StatusBadge :status="c.course_status" /></td>
            <td class="text-nowrap">
              <button class="btn btn-sm btn-outline-secondary me-1" @click="openForm(c)">Edit</button>
              <button class="btn btn-sm btn-outline-danger" @click="remove(c)">Delete</button>
            </td>
          </tr>
          <tr v-if="!loading && !courses.length"><td colspan="5" class="text-muted">No courses found.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import { adminApi } from '@/api/http'

const blank = () => ({ id: null, course_code: '', course_name: '', course_description: '', course_status: 'Active' })

export default {
  name: 'AdminCourses',
  components: { AlertBox, StatusBadge },
  data() {
    return { courses: [], search: '', loading: true, error: '', notice: '', showForm: false, form: blank(), formError: '', saving: false, timer: null }
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
        this.courses = await adminApi.get('/api/admin/courses', { q: this.search })
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
    openForm(course) {
      this.form = course ? { ...course } : blank()
      this.formError = ''
      this.notice = ''
      this.showForm = true
    },
    async save() {
      this.saving = true
      this.formError = ''
      const f = this.form
      const body = { course_code: f.course_code, course_name: f.course_name, course_description: f.course_description, course_status: f.course_status }
      try {
        if (f.id) await adminApi.put(`/api/admin/courses/${f.id}`, body)
        else await adminApi.post('/api/admin/courses', body)
        this.notice = f.id ? 'Course updated.' : 'Course created.'
        this.showForm = false
        await this.load()
      } catch (e) {
        this.formError = e.message
      } finally {
        this.saving = false
      }
    },
    async remove(course) {
      if (!confirm(`Delete course ${course.course_code}?`)) return
      this.error = ''
      this.notice = ''
      try {
        await adminApi.del(`/api/admin/courses/${course.id}`)
        this.notice = 'Course deleted.'
        await this.load()
      } catch (e) {
        this.error = e.message
      }
    }
  }
}
</script>
