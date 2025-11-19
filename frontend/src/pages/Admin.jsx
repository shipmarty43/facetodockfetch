import { useState, useEffect } from 'react'
import {
  Box,
  Tabs,
  Tab,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Alert,
  CircularProgress,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Snackbar,
} from '@mui/material'
import {
  Refresh,
  PlayArrow,
  Warning,
  CheckCircle,
  Error as ErrorIcon,
} from '@mui/icons-material'
import { adminAPI } from '../services/api'

function TabPanel({ children, value, index }) {
  return value === index ? <Box sx={{ p: 3 }}>{children}</Box> : null
}

export default function Admin() {
  const [tab, setTab] = useState(0)
  const [stats, setStats] = useState(null)
  const [tasks, setTasks] = useState(null)
  const [loading, setLoading] = useState(true)
  const [reindexDialog, setReindexDialog] = useState(false)
  const [reindexType, setReindexType] = useState('all')
  const [reindexing, setReindexing] = useState(false)
  const [notification, setNotification] = useState(null)
  const [logs, setLogs] = useState([])
  const [logsLoading, setLogsLoading] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    if (tab === 1) {
      loadLogs()
    }
  }, [tab])

  const loadData = async () => {
    setLoading(true)
    try {
      const [statsRes, tasksRes] = await Promise.all([
        adminAPI.getStats(),
        adminAPI.getTasks().catch(() => ({ data: null })),
      ])
      setStats(statsRes.data)
      setTasks(tasksRes.data)
    } catch (error) {
      console.error('Failed to load admin data:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadLogs = async () => {
    setLogsLoading(true)
    try {
      const response = await adminAPI.getLogs({ page: 1, page_size: 50 })
      setLogs(response.data.logs || [])
    } catch (error) {
      console.error('Failed to load logs:', error)
    } finally {
      setLogsLoading(false)
    }
  }

  const handleReindex = async () => {
    setReindexing(true)
    try {
      const response = await adminAPI.reindex({ reindex_type: reindexType })
      setNotification({
        message: response.data.message || 'Reindexing started',
        severity: 'success',
      })
      setReindexDialog(false)
      // Refresh data
      loadData()
    } catch (error) {
      console.error('Reindex failed:', error)
      setNotification({
        message: error.response?.data?.detail || 'Reindexing failed',
        severity: 'error',
      })
    } finally {
      setReindexing(false)
    }
  }

  const formatBytes = (bytes) => {
    if (!bytes) return '0 B'
    const units = ['B', 'KB', 'MB', 'GB']
    let i = 0
    while (bytes >= 1024 && i < units.length - 1) {
      bytes /= 1024
      i++
    }
    return `${bytes.toFixed(1)} ${units[i]}`
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Admin Panel</Typography>
        <Button startIcon={<Refresh />} onClick={loadData}>
          Refresh
        </Button>
      </Box>

      <Card>
        <Tabs value={tab} onChange={(e, v) => setTab(v)}>
          <Tab label="Overview" />
          <Tab label="System Logs" />
          <Tab label="Reindex" />
        </Tabs>

        {/* Overview Tab */}
        <TabPanel value={tab} index={0}>
          <Grid container spacing={3}>
            {/* Statistics Cards */}
            <Grid item xs={12} md={3}>
              <Paper elevation={2} sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h3" color="primary">
                  {stats?.total_documents || 0}
                </Typography>
                <Typography variant="subtitle1">Total Documents</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={3}>
              <Paper elevation={2} sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h3" color="primary">
                  {stats?.total_faces || 0}
                </Typography>
                <Typography variant="subtitle1">Detected Faces</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={3}>
              <Paper elevation={2} sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h3" color="primary">
                  {stats?.total_users || 0}
                </Typography>
                <Typography variant="subtitle1">Users</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={3}>
              <Paper elevation={2} sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h3" color="primary">
                  {formatBytes(stats?.storage_size_bytes)}
                </Typography>
                <Typography variant="subtitle1">Storage Used</Typography>
              </Paper>
            </Grid>

            {/* Processing Status */}
            <Grid item xs={12} md={6}>
              <Paper elevation={2} sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Documents by Status
                </Typography>
                <Box display="flex" gap={1} flexWrap="wrap">
                  {stats?.documents_by_status &&
                    Object.entries(stats.documents_by_status).map(([status, count]) => (
                      <Chip
                        key={status}
                        label={`${status}: ${count}`}
                        color={
                          status === 'completed'
                            ? 'success'
                            : status === 'failed'
                            ? 'error'
                            : status === 'processing'
                            ? 'info'
                            : 'default'
                        }
                        variant="outlined"
                      />
                    ))}
                </Box>
              </Paper>
            </Grid>

            {/* Task Queue Status */}
            <Grid item xs={12} md={6}>
              <Paper elevation={2} sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Task Queue
                </Typography>
                {tasks ? (
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Active Tasks
                      </Typography>
                      <Typography variant="h5">{tasks.active_tasks}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Pending Tasks
                      </Typography>
                      <Typography variant="h5">{tasks.pending_tasks}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Workers Online
                      </Typography>
                      <Typography variant="h5">{tasks.workers_online}</Typography>
                    </Grid>
                  </Grid>
                ) : (
                  <Alert severity="warning">Unable to connect to task queue</Alert>
                )}
              </Paper>
            </Grid>

            {/* Recent Activity */}
            <Grid item xs={12}>
              <Paper elevation={2} sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Recent Activity
                </Typography>
                {stats?.recent_activity && stats.recent_activity.length > 0 ? (
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Time</TableCell>
                          <TableCell>Action</TableCell>
                          <TableCell>Level</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {stats.recent_activity.slice(0, 5).map((activity, idx) => (
                          <TableRow key={idx}>
                            <TableCell>
                              {new Date(activity.timestamp).toLocaleString()}
                            </TableCell>
                            <TableCell>{activity.action}</TableCell>
                            <TableCell>
                              <Chip
                                label={activity.level}
                                size="small"
                                color={
                                  activity.level === 'ERROR'
                                    ? 'error'
                                    : activity.level === 'WARNING'
                                    ? 'warning'
                                    : 'default'
                                }
                              />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Typography color="text.secondary">No recent activity</Typography>
                )}
              </Paper>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Logs Tab */}
        <TabPanel value={tab} index={1}>
          {logsLoading ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : logs.length > 0 ? (
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Time</TableCell>
                    <TableCell>Level</TableCell>
                    <TableCell>Action</TableCell>
                    <TableCell>Details</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {logs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell>
                        {new Date(log.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={log.level}
                          size="small"
                          color={
                            log.level === 'ERROR'
                              ? 'error'
                              : log.level === 'WARNING'
                              ? 'warning'
                              : 'default'
                          }
                        />
                      </TableCell>
                      <TableCell>{log.action}</TableCell>
                      <TableCell>
                        <Typography variant="body2" noWrap sx={{ maxWidth: 300 }}>
                          {JSON.stringify(log.details)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Alert severity="info">No logs available</Alert>
          )}
        </TabPanel>

        {/* Reindex Tab */}
        <TabPanel value={tab} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Alert severity="info" sx={{ mb: 3 }}>
                Reindexing will reprocess documents through OCR, face detection, and MRZ
                extraction. This may take a long time for large datasets.
              </Alert>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Reindex All Documents
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Reprocess all {stats?.total_documents || 0} documents in the system.
                  </Typography>
                  <Button
                    variant="contained"
                    color="primary"
                    startIcon={<PlayArrow />}
                    onClick={() => {
                      setReindexType('all')
                      setReindexDialog(true)
                    }}
                  >
                    Reindex All
                  </Button>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Reindex Failed Only
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Reprocess only documents with failed status (
                    {stats?.documents_by_status?.failed || 0} documents).
                  </Typography>
                  <Button
                    variant="contained"
                    color="warning"
                    startIcon={<Warning />}
                    onClick={() => {
                      setReindexType('failed_only')
                      setReindexDialog(true)
                    }}
                    disabled={!stats?.documents_by_status?.failed}
                  >
                    Reindex Failed
                  </Button>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Reindex Pending
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Process documents stuck in pending status (
                    {stats?.documents_by_status?.pending || 0} documents).
                  </Typography>
                  <Button
                    variant="contained"
                    color="info"
                    startIcon={<Refresh />}
                    onClick={() => {
                      setReindexType('pending_only')
                      setReindexDialog(true)
                    }}
                    disabled={!stats?.documents_by_status?.pending}
                  >
                    Process Pending
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Card>

      {/* Reindex Confirmation Dialog */}
      <Dialog open={reindexDialog} onClose={() => setReindexDialog(false)}>
        <DialogTitle>Confirm Reindexing</DialogTitle>
        <DialogContent>
          <Typography paragraph>
            Are you sure you want to start reindexing?
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Type:{' '}
            <strong>
              {reindexType === 'all'
                ? 'All Documents'
                : reindexType === 'failed_only'
                ? 'Failed Documents Only'
                : 'Pending Documents'}
            </strong>
          </Typography>
          <Typography variant="body2" color="text.secondary">
            This will queue documents for reprocessing. Processing happens in the
            background.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReindexDialog(false)} disabled={reindexing}>
            Cancel
          </Button>
          <Button
            onClick={handleReindex}
            variant="contained"
            color="primary"
            disabled={reindexing}
          >
            {reindexing ? <CircularProgress size={24} /> : 'Start Reindexing'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notification */}
      <Snackbar
        open={!!notification}
        autoHideDuration={6000}
        onClose={() => setNotification(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setNotification(null)}
          severity={notification?.severity || 'info'}
          sx={{ width: '100%' }}
        >
          {notification?.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}
