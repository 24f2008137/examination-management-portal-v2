<template>
  <LoginForm role="examiner" title="Examiner Login" @login-success="$emit('login-success')" />
</template>

<script>
import LoginForm from '@/components/shared/LoginForm.vue'

export default {
  name: 'ExaminerLogin',
  components: { LoginForm },
  emits: ['login-success']
}
</script>
