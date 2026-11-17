<template>
    <div>
        Examiner Registration
        <form @submit.prevent="handleRegister">
            <div>
                <label for="username">Username:</label>
                <input type="text" id="username" v-model="form.username" required />
            </div>
            <div>
                <label for="email">Email:</label>
                <input type="email" id="email" v-model="form.email" required />
            </div>
            <div>
                <label for="password">Password:</label>
                <input type="password" id="password" v-model="form.password" required />
            </div>
            <button type="submit">Register</button>
        </form>
        <a href="#" @click="$emit('login-success')">Already have an account? Login</a>
    </div>
</template>

<script>
import axios from 'axios';

export default {
    name: 'ExaminerReg',
    data() {
        return {
            form: {
                username: '',
                email: '',
                password: ''
            }
        }
    },
    methods: {
        async handleRegister() {
            try{
                const response = await axios.post('http://127.0.0.1:5000/api/register', {
                    username: this.form.username,
                    email: this.form.email,
                    password: this.form.password,
                    role: 'examiner'
                })
                console.log("Registration Success", response.data)
                this.$emit('registration-success');
            }catch(error){
                console.error("Error Registering:", error);
            }
        }
    }
}
</script>