<template>
  <div class="card shadow-sm">
    <div class="card-body">
      <h2 class="h5">Export examination history</h2>
      <p class="small text-muted">Generates a CSV of your bookings and marks in the background.</p>
      <AlertBox :error="error" :notice="notice" />
      <button class="btn btn-primary btn-sm mb-3" :disabled="starting || running" @click="start">
        {{ running ? 'Export in progress...' : 'Export as CSV' }}
      </button>

      <ul v-if="jobs.length" class="list-group list-group-flush">
        <li v-for="j in jobs" :key="j.id" class="list-group-item px-0 d-flex align-items-center gap-2">
          <span class="small">#{{ j.id }} · {{ j.created_at.slice(0, 16) }}</span>
          <StatusBadge :status="j.status" />
          <span v-if="j.error" class="small text-danger">{{ j.error }}</span>
          <button v-if="j.download_url" class="btn btn-sm btn-outline-success ms-auto" @click="download(j)">Download</button>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import AlertBox from '@/components/shared/AlertBox.vue'
import StatusBadge from '@/components/shared/StatusBadge.vue'
import { studentApi } from '@/api/http'

const ACTIVE = ['Pending', 'Processing']

export default {
  name: 'StudentExport',
  components: { AlertBox, StatusBadge },
  data() {
    return { jobs: [], starting: false, error: '', notice: '', timer: null }
  },
  computed: {
    running() {
      return this.jobs.some((j) => ACTIVE.includes(j.status))
    }
  },
  async mounted() {
    await this.refresh()
  },
  beforeUnmount() {
    clearTimeout(this.timer)
  },
  methods: {
    async refresh() {
      clearTimeout(this.timer)
      try {
        const previous = this.jobs
        this.jobs = await studentApi.get('/api/student/exports')
        // alert the student when a running export finishes
        for (const job of this.jobs) {
          const before = previous.find((p) => p.id === job.id)
          if (before && ACTIVE.includes(before.status) && job.status === 'Completed') {
            this.notice = 'Your examination history export is ready to download.'
          } else if (before && ACTIVE.includes(before.status) && job.status === 'Failed') {
            this.error = job.error || 'The export failed.'
          }
        }
      } catch (e) {
        this.error = e.message
        return
      }
      
      if (this.running) this.timer = setTimeout(this.refresh, 3000)
    },
    async start() {
      this.error = ''
      this.notice = ''
      this.starting = true
      try {
        const data = await studentApi.post('/api/student/exports')
        this.notice = data.message
      } catch (e) {
        this.error = e.message
      } finally {
        this.starting = false
      }
      await this.refresh()
    },
    async download(job) {
      this.error = ''
      try {
        await studentApi.download(job.download_url, 'examination_history.csv')
      } catch (e) {
        this.error = e.message
      }
    }
  }
}
</script>
