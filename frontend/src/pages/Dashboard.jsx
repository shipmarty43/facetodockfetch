import { useEffect, useState } from 'react'
import { Grid, Card, CardContent, Typography, Box } from '@mui/material'
import {
  Description as DocumentIcon,
  Face as FaceIcon,
  Person as UserIcon,
  CloudQueue as QueueIcon,
} from '@mui/icons-material'
import { adminAPI } from '../services/api'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [tasks, setTasks] = useState(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [statsRes, tasksRes] = await Promise.all([
        adminAPI.getStats(),
        adminAPI.getTasks(),
      ])
      setStats(statsRes.data)
      setTasks(tasksRes.data)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    }
  }

  const StatCard = ({ title, value, icon, color }) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="text.secondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4">{value || 0}</Typography>
          </Box>
          <Box
            sx={{
              backgroundColor: `${color}.light`,
              borderRadius: 2,
              p: 1.5,
              display: 'flex',
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  )

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3} mt={2}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Documents"
            value={stats?.total_documents}
            icon={<DocumentIcon />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Faces"
            value={stats?.total_faces}
            icon={<FaceIcon />}
            color="secondary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Users"
            value={stats?.total_users}
            icon={<UserIcon />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Tasks"
            value={tasks?.active_tasks}
            icon={<QueueIcon />}
            color="warning"
          />
        </Grid>
      </Grid>

      {stats && (
        <Grid container spacing={3} mt={2}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Documents by Status
                </Typography>
                {Object.entries(stats.documents_by_status || {}).map(([status, count]) => (
                  <Box key={status} display="flex" justifyContent="space-between" my={1}>
                    <Typography>{status}</Typography>
                    <Typography fontWeight="bold">{count}</Typography>
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Documents by Type
                </Typography>
                {Object.entries(stats.documents_by_type || {}).map(([type, count]) => (
                  <Box key={type} display="flex" justifyContent="space-between" my={1}>
                    <Typography>{type.toUpperCase()}</Typography>
                    <Typography fontWeight="bold">{count}</Typography>
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  )
}
