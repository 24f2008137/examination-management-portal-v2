<template>
  <div>
    <template v-if="!isLoggedIn">
      <StudentReg v-if="showRegister" @registered="onRegistered" @show-login="showRegister = false" />
      <template v-else>
        <div v-if="justRegistered" class="container mt-4">
          <div class="alert alert-success mb-0">Registration successful. Please log in.</div>
        </div>
        <StudentLogin @login-success="isLoggedIn = true" @show-register="showRegister = true" />
      </template>
    </template>
    <StudentDash v-else @logout="logout" />
  </div>
</template>

<script>
import StudentLogin from '@/components/StudentLogin.vue'
import StudentReg from '@/components/StudentReg.vue'
import StudentDash from '@/components/StudentDash.vue'

export default {
  name: 'StudentView',
  components: { StudentLogin, StudentReg, StudentDash },
  data() {
    return {
      isLoggedIn: !!localStorage.getItem('student-token'),
      showRegister: false,
      justRegistered: false
    }
  },
  mounted() {
    window.addEventListener('auth-expired', this.handleExpired)
  },
  beforeUnmount() {
    window.removeEventListener('auth-expired', this.handleExpired)
  },
  methods: {
    handleExpired(event) {
      if (event.detail === 'student-token') this.isLoggedIn = false
    },
    onRegistered() {
      this.showRegister = false
      this.justRegistered = true
    },
    logout() {
      localStorage.removeItem('student-token')
      this.isLoggedIn = false
      this.justRegistered = false
    }
  }
}
</script>
