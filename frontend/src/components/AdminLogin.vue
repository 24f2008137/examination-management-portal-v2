<template>
    <div>
        <form @submit.prevent="loggedIn">
            <div>
                <label for="username">Username: </label>
                <input type="text" id="username" v-model="username" placeholder="Username" required/>
            </div>
            <div>
                <label for="password">Password: </label>
                <input type="password" id="password" v-model="password" placeholder="Password" required/>
            </div>
            <div>
                <button type="submit">Login</button>
            </div>
        </form>
    </div>
</template>

<script>
import axios from 'axios'

export default {
    name: 'AdminLogin',
    data() {
        return {
            form: {
                username: '',
                password: ''
            }
        }
    },
    methods: {
        async loggedIn() {
            try{
                const response = await axios.post('http://127.0.0.1:5000/api/login', {
                    username: this.username,
                    password: this.password,
                    role: 'admin'
                })
                console.log("Login Success", response.data)
                localStorage.setItem('admin-token', response.data.access_token);
                this.$emit('login-success');
            }catch(error){
                console.error("Error Logging in:", error);
            }
        }
    }
}
</script>