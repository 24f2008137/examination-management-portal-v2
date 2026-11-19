<template>
  <LoginForm role="admin" title="Admin Login" @login-success="$emit('login-success')" />
</template>

<script>
import LoginForm from '@/components/shared/LoginForm.vue'

export default {
  name: 'AdminLogin',
  components: { LoginForm },
  emits: ['login-success']
}
</script>
