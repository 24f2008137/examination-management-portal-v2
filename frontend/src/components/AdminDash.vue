<template>
  <DashLayout title="EMP · Admin" :tabs="tabs" v-model="tab" @logout="$emit('logout')">
    <component :is="current" />
  </DashLayout>
</template>

<script>
import DashLayout from '@/components/shared/DashLayout.vue'
import AdminOverview from '@/components/admin/AdminOverview.vue'
import AdminCourses from '@/components/admin/AdminCourses.vue'
import AdminExams from '@/components/admin/AdminExams.vue'
import AdminSlots from '@/components/admin/AdminSlots.vue'
import AdminBookings from '@/components/admin/AdminBookings.vue'
import AdminExaminers from '@/components/admin/AdminExaminers.vue'
import AdminStudents from '@/components/admin/AdminStudents.vue'

const TABS = [
  { key: 'overview', label: 'Overview', component: 'AdminOverview' },
  { key: 'courses', label: 'Courses', component: 'AdminCourses' },
  { key: 'exams', label: 'Exams', component: 'AdminExams' },
  { key: 'slots', label: 'Slots', component: 'AdminSlots' },
  { key: 'bookings', label: 'Bookings', component: 'AdminBookings' },
  { key: 'examiners', label: 'Examiners', component: 'AdminExaminers' },
  { key: 'students', label: 'Students', component: 'AdminStudents' }
]

export default {
  name: 'AdminDash',
  emits: ['logout'],
  components: { DashLayout, AdminOverview, AdminCourses, AdminExams, AdminSlots, AdminBookings, AdminExaminers, AdminStudents },
  data() {
    return { tab: 'overview', tabs: TABS }
  },
  computed: {
    current() {
      return TABS.find((t) => t.key === this.tab).component
    }
  }
}
</script>
