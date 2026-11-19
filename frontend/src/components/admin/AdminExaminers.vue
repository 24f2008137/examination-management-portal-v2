<template>
  <div>
    <div class="d-flex flex-wrap gap-2 mb-3">
      <input v-model="search" class="form-control" style="max-width: 320px" placeholder="Search by name, department or username" @input="debouncedLoad" />
      <button class="btn btn-primary ms-auto" @click="openForm()">+ New examiner</button>
    </div>

    <form v-if="showForm" class="card card-body bg-light mb-3" @submit.prevent="save">
      <h2 class="h5">{{ form.id ? 'Edit examiner' : 'New examiner' }}</h2>
      <div class="row g-3">
        <div class="col-md-4">
          <label class="form-label">Full name</label>
          <input v-model="form.name" class="form-control" required />
        </div>
        <template v-if="!form.id">
          <div class="col-md-4">
            <label class="form-label">Username</label>
            <input v-model="form.username" class="form-control" required />
          </div>
          <div class="col-md-4">
            <label class="form-label">Email</label>
            <input v-model="form.email" type="email" class="form-control" required />
          </div>
          <div class="col-md-4">
            <label class="form-label">Password</label>
            <input v-model="form.password" type="password" minlength="6" class="form-control" required />
          </div>
        </template>
        <div class="col-md-4">
          <label class="form-label">Department</label>
          <input v-model="form.department" class="form-control" />
        </div>
        <div class="col-md-4">
          <label class="form-label">Contact details</label>
          <input v-model="form.contact_details" class="form-control" />
        </div>
        <div v-if="form.id" class="col-md-4">
          <label class="form-label">Status</label>
          <select v-model="form.status" class="form-select">
            <option>Active</option>
            <option>Inactive</option>
          </select>
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
          <tr><th>Name</th><th>Username</th><th>Department</th><th>Contact</th><th>Status</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="x in examiners" :key="x.id">
            <td>{{ x.name }}</td>
            <td>{{ x.username }}</td>
            <td>{{ x.department }}</td>
            <td>{{ x.contact_details }}</td>
            <td><StatusBadge :status="x.status" /></td>
            <td class="text-nowrap">
              <button class="btn btn-sm btn-outline-secondary me-1" @click="openForm(x)">Edit</button>
              <button class="btn btn-sm btn-outline-secondary" @click="toggle(x)">
                {{ x.status === 'Active' ? 'Deactivate' : 'Activate' }}
              </button>
            </td>
          </tr>
          <tr v-if="!loading && !examiners.length"><td colspan="6" class="text-muted">No examiners found.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import { adminApi } from '@/api/http'

const blank = () => ({ id: null, name: '', username: '', email: '', password: '', contact_details: '', department: '', status: 'Active' })

export default {
  name: 'AdminExaminers',
  components: { AlertBox, StatusBadge },
  data() {
    return { examiners: [], search: '', loading: true, error: '', notice: '', showForm: false, form: blank(), formError: '', saving: false, timer: null }
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
        this.examiners = await adminApi.get('/api/admin/examiners', { q: this.search })
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },
    openForm(x) {
      this.form = x ? { ...blank(), ...x, contact_details: x.contact_details || '', department: x.department || '' } : blank()
      this.formError = ''
      this.notice = ''
      this.showForm = true
    },
    async save() {
      this.saving = true
      this.formError = ''
      const f = this.form
      try {
        if (f.id) {
          await adminApi.put(`/api/admin/examiners/${f.id}`, { name: f.name, contact_details: f.contact_details, department: f.department, status: f.status })
        } else {
          await adminApi.post('/api/admin/examiners', {
            name: f.name, username: f.username, email: f.email, password: f.password,
            contact_details: f.contact_details, department: f.department
          })
        }
        this.notice = f.id ? 'Examiner updated.' : 'Examiner created.'
        this.showForm = false
        await this.load()
      } catch (e) {
        this.formError = e.message
      } finally {
        this.saving = false
      }
    },
    async toggle(x) {
      this.error = ''
      this.notice = ''
      try {
        await adminApi.put(`/api/admin/examiners/${x.id}`, { status: x.status === 'Active' ? 'Inactive' : 'Active' })
        await this.load()
      } catch (e) {
        this.error = e.message
      }
    }
  }
}
</script>
