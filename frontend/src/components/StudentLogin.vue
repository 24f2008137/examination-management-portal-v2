<template>
  <LoginForm role="student" title="Student Login" @login-success="$emit('login-success')">
    <p class="mt-3 mb-0 text-center">
      New student?
      <a href="#" @click.prevent="$emit('show-register')">Register here</a>
    </p>
  </LoginForm>
</template>

<script>
import LoginForm from '@/components/shared/LoginForm.vue'

export default {
  name: 'StudentLogin',
  components: { LoginForm },
  emits: ['login-success', 'show-register']
}
</script>
