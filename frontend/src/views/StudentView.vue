<template>
    <div>
        <h1>Student View</h1>
        <StudentLogin />
    </div>
</template>

<script>
import StudentLogin from '@/components/StudentLogin.vue'

export default {
    name: 'StudentView',
    components: {
        StudentLogin
    }
}
</script>