<template>
  <div class="container py-5">
    <div class="text-center mb-5">
      <h1 class="display-6">Examination Management Portal</h1>
      <p class="text-muted mb-0">Manage examinations, slots, bookings and evaluations in one place.</p>
    </div>
    <div class="row g-4 justify-content-center">
      <div v-for="p in portals" :key="p.to" class="col-md-4 col-lg-3">
        <div class="card h-100 shadow-sm text-center">
          <div class="card-body d-flex flex-column">
            <h2 class="h5">{{ p.title }}</h2>
            <p class="text-muted small flex-grow-1">{{ p.text }}</p>
            <RouterLink :to="p.to" class="btn btn-primary">Open {{ p.title }} portal</RouterLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { RouterLink } from 'vue-router'

export default {
  name: 'HomeView',
  components: { RouterLink },
  data() {
    return {
      portals: [
        { to: '/admin', title: 'Admin', text: 'Courses, exams, rubrics, examiners, slots, bookings and results.' },
        { to: '/examiner', title: 'Examiner', text: 'Create slots, see booked students and evaluate with rubrics.' },
        { to: '/student', title: 'Student', text: 'Book exam slots, track bookings and view published results.' }
      ]
    }
  }
}
</script>
