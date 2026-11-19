<template>
  <div class="row justify-content-center mt-5">
    <div class="col-11 col-sm-8 col-md-5 col-lg-4">
      <div class="card shadow-sm">
        <div class="card-body p-4">
          <h2 class="h4 mb-3">{{ title }}</h2>
          <form @submit.prevent="login">
            <div class="mb-3">
              <label class="form-label" for="username">Username</label>
              <input id="username" v-model="form.username" class="form-control" autocomplete="username" required />
            </div>
            <div class="mb-3">
              <label class="form-label" for="password">Password</label>
              <input id="password" v-model="form.password" type="password" class="form-control" autocomplete="current-password" required />
            </div>
            <AlertBox :error="error" />
            <button class="btn btn-primary w-100" type="submit" :disabled="busy">
              {{ busy ? 'Signing in...' : 'Login' }}
            </button>
          </form>
          <slot />
        </div>
      </div>
      <p class="text-center mt-3"><RouterLink to="/">Back to home</RouterLink></p>
    </div>
  </div>
</template>

<script>
import { RouterLink } from 'vue-router'
import AlertBox from '@/components/shared/AlertBox.vue'
import { publicApi } from '@/api/http'

export default {
  name: 'LoginForm',
  components: { AlertBox, RouterLink },
  props: {
    role: { type: String, required: true }, // admin / examiner / student
    title: { type: String, required: true }
  },
  emits: ['login-success'],
  data() {
    return { form: { username: '', password: '' }, error: '', busy: false }
  },
  methods: {
    async login() {
      this.error = ''
      this.busy = true
      try {
        const data = await publicApi.post('/api/login', this.form)
        if (data.role !== this.role) {
          this.error = `This is not ${this.role === 'admin' ? 'an' : 'a'} ${this.role} account.`
          return
        }
        localStorage.setItem(`${this.role}-token`, data.access_token)
        this.$emit('login-success', data.name)
      } catch (e) {
        this.error = e.message
      } finally {
        this.busy = false
      }
    }
  }
}
</script>
