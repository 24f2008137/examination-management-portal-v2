<template>
  <DashLayout title="EMP · Examiner" :tabs="tabs" v-model="tab" @logout="$emit('logout')">
    <ExaminerOverview v-if="tab === 'overview'" />
    <ExaminerExams v-else-if="tab === 'exams'" />
    <ExaminerSlots v-else-if="tab === 'slots'" />
    <ExaminerEvaluations v-else-if="tab === 'evaluations'" />
    <ProfileForm v-else role="examiner" />
  </DashLayout>
</template>

<script>
import DashLayout from '@/components/shared/DashLayout.vue'
import ProfileForm from '@/components/shared/ProfileForm.vue'
import ExaminerOverview from '@/components/examiner/ExaminerOverview.vue'
import ExaminerExams from '@/components/examiner/ExaminerExams.vue'
import ExaminerSlots from '@/components/examiner/ExaminerSlots.vue'
import ExaminerEvaluations from '@/components/examiner/ExaminerEvaluations.vue'

export default {
  name: 'ExaminerDash',
  emits: ['logout'],
  components: { DashLayout, ProfileForm, ExaminerOverview, ExaminerExams, ExaminerSlots, ExaminerEvaluations },
  data() {
    return {
      tab: 'overview',
      tabs: [
        { key: 'overview', label: 'Overview' },
        { key: 'exams', label: 'Assigned exams' },
        { key: 'slots', label: 'My slots' },
        { key: 'evaluations', label: 'Evaluations' },
        { key: 'profile', label: 'Profile' }
      ]
    }
  }
}
</script>
