<template>
  <div>
    <ExaminerLogin v-if="!isLoggedIn" @login-success="isLoggedIn = true" />
    <ExaminerDash v-else @logout="logout" />
  </div>
</template>

<script>
import ExaminerLogin from '@/components/ExaminerLogin.vue'
import ExaminerDash from '@/components/ExaminerDash.vue'

export default {
  name: 'ExaminerView',
  components: { ExaminerLogin, ExaminerDash },
  data() {
    return {
      isLoggedIn: !!localStorage.getItem('examiner-token')
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
      if (event.detail === 'examiner-token') this.isLoggedIn = false
    },
    logout() {
      localStorage.removeItem('examiner-token')
      this.isLoggedIn = false
    }
  }
}
</script>
