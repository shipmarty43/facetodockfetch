import { useEffect, useState } from 'react'
import { useSelector } from 'react-redux'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Divider,
  CircularProgress,
  Chip,
  Alert,
  LinearProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
} from '@mui/material'
import {
  Memory,
  Storage,
  Speed,
  CloudQueue,
  DataObject,
  CheckCircle,
  Error,
  Warning,
} from '@mui/icons-material'
import { adminAPI } from '../services/api'
import axios from 'axios'

export default function Settings() {
  const [systemInfo, setSystemInfo] = useState(null)
  const [healthStatus, setHealthStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const { user } = useSelector((state) => state.auth)

  useEffect(() => {
    loadSystemInfo()
  }, [])

  const loadSystemInfo = async () => {
    setLoading(true)
    setError(null)

    try {
      // Load system stats and health in parallel
      const [statsResponse, healthResponse] = await Promise.all([
        adminAPI.getStats().catch(() => ({ data: null })),
        axios.get('/health').catch(() => ({ data: null })),
      ])

      setSystemInfo(statsResponse.data)
      setHealthStatus(healthResponse.data)
    } catch (err) {
      console.error('Failed to load system info:', err)
      setError('Failed to load system information')
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status) => {
    if (status === 'connected' || status === 'ok' || status === 'healthy') {
      return <CheckCircle color="success" fontSize="small" />
    } else if (status === 'disconnected' || status === 'error') {
      return <Error color="error" fontSize="small" />
    }
    return <Warning color="warning" fontSize="small" />
  }

  const getStatusColor = (status) => {
    if (status === 'connected' || status === 'ok' || status === 'healthy') {
      return 'success'
    } else if (status === 'disconnected' || status === 'error') {
      return 'error'
    }
    return 'warning'
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
      <Typography variant="h4" gutterBottom>
        System Settings
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* System Health */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <Speed sx={{ mr: 1, verticalAlign: 'middle' }} />
                System Health
              </Typography>
              <Divider sx={{ mb: 2 }} />

              {healthStatus ? (
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Overall Status
                      </Typography>
                      <Box display="flex" alignItems="center" justifyContent="center" mt={1}>
                        {getStatusIcon(healthStatus.status)}
                        <Typography sx={{ ml: 1 }}>
                          {healthStatus.status?.toUpperCase() || 'Unknown'}
                        </Typography>
                      </Box>
                    </Paper>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Database
                      </Typography>
                      <Box display="flex" alignItems="center" justifyContent="center" mt={1}>
                        {getStatusIcon(healthStatus.database)}
                        <Typography sx={{ ml: 1 }}>
                          {healthStatus.database || 'Unknown'}
                        </Typography>
                      </Box>
                    </Paper>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Redis
                      </Typography>
                      <Box display="flex" alignItems="center" justifyContent="center" mt={1}>
                        {getStatusIcon(healthStatus.redis)}
                        <Typography sx={{ ml: 1 }}>
                          {healthStatus.redis || 'Unknown'}
                        </Typography>
                      </Box>
                    </Paper>
                  </Grid>

                  <Grid item xs={12} sm={6} md={3}>
                    <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Elasticsearch
                      </Typography>
                      <Box display="flex" alignItems="center" justifyContent="center" mt={1}>
                        {getStatusIcon(healthStatus.elasticsearch)}
                        <Typography sx={{ ml: 1 }}>
                          {healthStatus.elasticsearch || 'Unknown'}
                        </Typography>
                      </Box>
                    </Paper>
                  </Grid>

                  {healthStatus.gpu_available !== undefined && (
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="subtitle2" color="text.secondary">
                          GPU
                        </Typography>
                        <Box display="flex" alignItems="center" justifyContent="center" mt={1}>
                          <Chip
                            label={healthStatus.gpu_available ? 'Available' : 'Not Available'}
                            color={healthStatus.gpu_available ? 'success' : 'default'}
                            size="small"
                          />
                        </Box>
                      </Paper>
                    </Grid>
                  )}
                </Grid>
              ) : (
                <Alert severity="warning">
                  Unable to fetch health status
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* System Statistics */}
        {systemInfo && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <DataObject sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Database Statistics
                </Typography>
                <Divider sx={{ mb: 2 }} />

                <TableContainer>
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell>Total Documents</TableCell>
                        <TableCell align="right">
                          <Typography fontWeight="bold">
                            {systemInfo.total_documents || 0}
                          </Typography>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Total Faces</TableCell>
                        <TableCell align="right">
                          <Typography fontWeight="bold">
                            {systemInfo.total_faces || 0}
                          </Typography>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Total Users</TableCell>
                        <TableCell align="right">
                          <Typography fontWeight="bold">
                            {systemInfo.total_users || 0}
                          </Typography>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Documents with MRZ</TableCell>
                        <TableCell align="right">
                          <Typography fontWeight="bold">
                            {systemInfo.documents_with_mrz || 0}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>

                {systemInfo.processing_status && (
                  <Box mt={2}>
                    <Typography variant="subtitle2" gutterBottom>
                      Processing Status
                    </Typography>
                    <Box display="flex" gap={1} flexWrap="wrap">
                      {Object.entries(systemInfo.processing_status).map(([status, count]) => (
                        <Chip
                          key={status}
                          label={`${status}: ${count}`}
                          size="small"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Storage Information */}
        {systemInfo && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <Storage sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Storage
                </Typography>
                <Divider sx={{ mb: 2 }} />

                <TableContainer>
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell>Upload Directory</TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" color="text.secondary">
                            data/uploads
                          </Typography>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Total Storage Used</TableCell>
                        <TableCell align="right">
                          <Typography fontWeight="bold">
                            {systemInfo.storage_used || 'N/A'}
                          </Typography>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Database Size</TableCell>
                        <TableCell align="right">
                          <Typography fontWeight="bold">
                            {systemInfo.database_size || 'N/A'}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* User Information */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <Memory sx={{ mr: 1, verticalAlign: 'middle' }} />
                Current User
              </Typography>
              <Divider sx={{ mb: 2 }} />

              <TableContainer>
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell>Username</TableCell>
                      <TableCell align="right">
                        <Typography fontWeight="bold">
                          {user?.username}
                        </Typography>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Role</TableCell>
                      <TableCell align="right">
                        <Chip
                          label={user?.role?.toUpperCase()}
                          color={user?.role === 'admin' ? 'primary' : 'default'}
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* API Information */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <CloudQueue sx={{ mr: 1, verticalAlign: 'middle' }} />
                API Configuration
              </Typography>
              <Divider sx={{ mb: 2 }} />

              <TableContainer>
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell>API Base URL</TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" color="text.secondary">
                          /api/v1
                        </Typography>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>API Documentation</TableCell>
                      <TableCell align="right">
                        <Typography
                          variant="body2"
                          component="a"
                          href="/api/v1/docs"
                          target="_blank"
                          sx={{ color: 'primary.main' }}
                        >
                          /api/v1/docs
                        </Typography>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Max Upload Size</TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          50 MB
                        </Typography>
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
