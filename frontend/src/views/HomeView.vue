<template>
  <div>
    <nav>
      <RouterLink to="/">Home</RouterLink>
      <RouterLink to="/admin">Admin</RouterLink>
      <RouterLink to="/student">Student</RouterLink>
      <RouterLink to="/examiner">Examiner</RouterLink>
    </nav>
    <h1>welcome to examination management portal</h1>
  </div>
</template>


<script>
export default {
  name: 'HomeView'
}
</script>