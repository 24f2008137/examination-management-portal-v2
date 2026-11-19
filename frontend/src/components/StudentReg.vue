<template>
  <div class="row justify-content-center mt-4">
    <div class="col-11 col-sm-10 col-md-6 col-lg-5">
      <div class="card shadow-sm">
        <div class="card-body p-4">
          <h2 class="h4 mb-3">Student Registration</h2>
          <form @submit.prevent="register">
            <div class="mb-3">
              <label class="form-label" for="name">Full name</label>
              <input id="name" v-model="form.name" class="form-control" required />
            </div>
            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label" for="username">Username</label>
                <input id="username" v-model="form.username" class="form-control" required />
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label" for="email">Email</label>
                <input id="email" v-model="form.email" type="email" class="form-control" required />
              </div>
            </div>
            <div class="mb-3">
              <label class="form-label" for="password">Password</label>
              <input id="password" v-model="form.password" type="password" minlength="6" class="form-control" required />
              <div class="form-text">At least 6 characters.</div>
            </div>
            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label" for="department">Department (optional)</label>
                <input id="department" v-model="form.department" class="form-control" />
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label" for="contact">Contact (optional)</label>
                <input id="contact" v-model="form.contact_details" class="form-control" />
              </div>
            </div>
            <AlertBox :error="error" />
            <button class="btn btn-primary w-100" type="submit" :disabled="busy">
              {{ busy ? 'Creating account...' : 'Register' }}
            </button>
          </form>
          <p class="mt-3 mb-0 text-center">
            Already have an account?
            <a href="#" @click.prevent="$emit('show-login')">Login</a>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import { publicApi } from '@/api/http'

export default {
  name: 'StudentReg',
  components: { AlertBox },
  emits: ['registered', 'show-login'],
  data() {
    return {
      form: { name: '', username: '', email: '', password: '', department: '', contact_details: '' },
      error: '',
      busy: false
    }
  },
  methods: {
    async register() {
      this.error = ''
      this.busy = true
      try {
        await publicApi.post('/api/register', this.form)
        this.$emit('registered')
      } catch (e) {
        this.error = e.message
      } finally {
        this.busy = false
      }
    }
  }
}
</script>
