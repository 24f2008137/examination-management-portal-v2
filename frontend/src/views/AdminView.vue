<template>
  <div>
    <h1>Admin View</h1>
    <div v-if="!isLoggedIn">
      <AdminLogin @login-success="handleLoginSuccess"/>
    </div>
    <AdminDash v-else />
  </div>
</template>

<script>
import AdminLogin from '@/components/AdminLogin.vue'
import AdminDash from '@/components/AdminDash.vue'

export default {
  name: 'AdminView',
  components: {
    AdminLogin,
    AdminDash
  },
  data() {
    return {
      isLoggedIn: false
    }
  },
  methods: {
    handleLoginSuccess() {
      this.isLoggedIn = true
    }
  }
}
</script>
