<template>
    <div>
        <form @submit.prevent="handleLogin">
            <div>
                <label for="username">Username: </label>
                <input type="text" id="username" v-model="form.username" placeholder="Username" required/>
            </div>
            <div>
                <label for="password">Password: </label>
                <input type="password" id="password" v-model="form.password" placeholder="Password" required/>
            </div>
            <div>
                <button type="submit">Login</button>
            </div>
        </form>
        <a href="#" @click="$emit('register-success')">Register</a>
    </div>
</template>

<script>
import axios from 'axios';

export default {
    name: 'ExaminerLogin',
    data() {
        return {
            form: {
                username: '',
                password: ''
            }
        }
    },
    methods: {
        async handleLogin() {
            try{
                const response = await axios.post('http://127.0.0.1:5000/api/login', {
                    username: this.form.username,
                    password: this.form.password,
                    role: 'examiner'
                })
                console.log("Login Success", response.data)
                localStorage.setItem('examiner-token', response.data.access_token);
                this.$emit('login-success');
            }catch(error){
                console.error("Error Logging in:", error);
            }
        }
    }
}
</script>