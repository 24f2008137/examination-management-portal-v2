<template>
    <div>
        <h1>Examiner View</h1>
        <div v-if="!isLoggedIn">
            <div v-if="!isRegistered">
                <ExaminerLogin @loggedIn-success="handleLoginSuccess" @register-success="isRegistered = true" />
            </div>
            <div v-else>
                <ExaminerReg @registration-success="handleRegistration" @login-success="isRegistered = false" />
            </div>
        </div>
        <ExaminerDash v-else />
    </div>
</template>

<script>
import ExaminerLogin from '@/components/ExaminerLogin.vue'
import ExaminerReg from '@/components/ExaminerReg.vue'
import ExaminerDash from '@/components/ExaminerDash.vue'

export default {
    name: 'ExaminerView',
    components: {
        ExaminerLogin,
        ExaminerReg,
        ExaminerDash
    },
    data() {
        return {
            isLoggedIn: false,
            isRegistered: false
        }
    },
    methods: {
        handleLoginSuccess() {
            this.isLoggedIn = true
        },
        handleRegistration() {
            this.isRegistered = true
            this.isLoggedIn = false
        }
    }
}
</script>
