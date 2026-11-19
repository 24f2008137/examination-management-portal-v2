<template>
  <DashLayout title="EMP · Student" :tabs="tabs" v-model="tab" @logout="$emit('logout')">
    <StudentOverview v-if="tab === 'overview'" />
    <StudentExams v-else-if="tab === 'exams'" />
    <StudentBookings v-else-if="tab === 'bookings'" />
    <StudentResults v-else-if="tab === 'results'" />
    <ProfileForm v-else role="student" />
  </DashLayout>
</template>

<script>
import DashLayout from '@/components/shared/DashLayout.vue'
import ProfileForm from '@/components/shared/ProfileForm.vue'
import StudentOverview from '@/components/student/StudentOverview.vue'
import StudentExams from '@/components/student/StudentExams.vue'
import StudentBookings from '@/components/student/StudentBookings.vue'
import StudentResults from '@/components/student/StudentResults.vue'

export default {
  name: 'StudentDash',
  emits: ['logout'],
  components: { DashLayout, ProfileForm, StudentOverview, StudentExams, StudentBookings, StudentResults },
  data() {
    return {
      tab: 'overview',
      tabs: [
        { key: 'overview', label: 'Overview' },
        { key: 'exams', label: 'Examinations' },
        { key: 'bookings', label: 'My bookings' },
        { key: 'results', label: 'Results' },
        { key: 'profile', label: 'Profile' }
      ]
    }
  }
}
</script>
