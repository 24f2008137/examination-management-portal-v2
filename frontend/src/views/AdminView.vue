<template>
  <div>
    <AdminLogin v-if="!isLoggedIn" @login-success="isLoggedIn = true" />
    <AdminDash v-else @logout="logout" />
  </div>
</template>

<script>
import AdminLogin from '@/components/AdminLogin.vue'
import AdminDash from '@/components/AdminDash.vue'

export default {
  name: 'AdminView',
  components: { AdminLogin, AdminDash },
  data() {
    return {
      isLoggedIn: !!localStorage.getItem('admin-token')
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
      if (event.detail === 'admin-token') this.isLoggedIn = false
    },
    logout() {
      localStorage.removeItem('admin-token')
      this.isLoggedIn = false
    }
  }
}
</script>
