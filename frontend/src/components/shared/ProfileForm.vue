<template>
  <div class="row">
    <div class="col-lg-6">
      <h2 class="h5 mb-3">My profile</h2>
      <p v-if="loading" class="text-muted">Loading...</p>
      <form v-else class="card card-body" @submit.prevent="save">
        <div class="row g-3">
          <div class="col-md-6">
            <label class="form-label">Full name</label>
            <input v-model="form.name" class="form-control" required />
          </div>
          <div class="col-md-6">
            <label class="form-label">Username</label>
            <input v-model="form.username" class="form-control" required />
          </div>
          <div class="col-md-6">
            <label class="form-label">Email</label>
            <input v-model="form.email" type="email" class="form-control" required />
          </div>
          <div class="col-md-6">
            <label class="form-label">Department</label>
            <input v-model="form.department" class="form-control" />
          </div>
          <div class="col-12">
            <label class="form-label">Contact details</label>
            <input v-model="form.contact_details" class="form-control" />
          </div>
        </div>

        <hr />
        <h3 class="h6">Change password (optional)</h3>
        <div class="row g-3">
          <div class="col-md-6">
            <label class="form-label">Current password</label>
            <input v-model="form.current_password" type="password" class="form-control" autocomplete="current-password" />
          </div>
          <div class="col-md-6">
            <label class="form-label">New password</label>
            <input v-model="form.new_password" type="password" minlength="6" class="form-control" autocomplete="new-password" />
          </div>
        </div>

        <AlertBox :error="error" :notice="notice" class="mt-3" />
        <div><button class="btn btn-primary" type="submit" :disabled="saving">Save changes</button></div>
      </form>
    </div>
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import { apis } from '@/api/http'

export default {
  name: 'ProfileForm',
  components: { AlertBox },
  props: { role: { type: String, required: true } }, // examiner / student
  data() {
    return { form: {}, loading: true, saving: false, error: '', notice: '' }
  },
  async mounted() {
    try {
      const p = await apis[this.role].get('/api/profile')
      this.form = {
        name: p.name, username: p.username, email: p.email,
        department: p.department || '', contact_details: p.contact_details || '',
        current_password: '', new_password: ''
      }
    } catch (e) {
      this.error = e.message
    } finally {
      this.loading = false
    }
  },
  methods: {
    async save() {
      this.error = ''
      this.notice = ''
      this.saving = true
      const body = {
        name: this.form.name, username: this.form.username, email: this.form.email,
        department: this.form.department, contact_details: this.form.contact_details
      }
      if (this.form.new_password) {
        body.new_password = this.form.new_password
        body.current_password = this.form.current_password
      }
      try {
        const data = await apis[this.role].put('/api/profile', body)
        this.notice = data.message
        this.form.current_password = ''
        this.form.new_password = ''
      } catch (e) {
        this.error = e.message
      } finally {
        this.saving = false
      }
    }
  }
}
</script>
