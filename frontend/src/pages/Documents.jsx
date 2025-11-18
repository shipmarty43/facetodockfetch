import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import {
  Box,
  Button,
  Card,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Snackbar,
  CircularProgress,
  Grid,
  Divider,
  Paper,
} from '@mui/material'
import { CloudUpload, Delete, Visibility, Download, Close } from '@mui/icons-material'
import { useDropzone } from 'react-dropzone'
import { setDocuments, setLoading } from '../store/documentsSlice'
import { documentsAPI } from '../services/api'

export default function Documents() {
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(50)
  const [uploadDialog, setUploadDialog] = useState(false)
  const [selectedDoc, setSelectedDoc] = useState(null)
  const [docDetails, setDocDetails] = useState(null)
  const [detailsLoading, setDetailsLoading] = useState(false)
  const [uploadResult, setUploadResult] = useState(null)

  const dispatch = useDispatch()
  const { documents, total, loading } = useSelector((state) => state.documents)

  useEffect(() => {
    loadDocuments()
  }, [page, rowsPerPage])

  // Load document details when selected
  useEffect(() => {
    if (selectedDoc) {
      loadDocumentDetails(selectedDoc.id)
    } else {
      setDocDetails(null)
    }
  }, [selectedDoc])

  const loadDocuments = async () => {
    dispatch(setLoading(true))
    try {
      const response = await documentsAPI.list({
        page: page + 1,
        page_size: rowsPerPage,
      })
      dispatch(setDocuments(response.data))
    } catch (error) {
      console.error('Failed to load documents:', error)
    } finally {
      dispatch(setLoading(false))
    }
  }

  const loadDocumentDetails = async (id) => {
    setDetailsLoading(true)
    try {
      const response = await documentsAPI.get(id)
      setDocDetails(response.data)
    } catch (error) {
      console.error('Failed to load document details:', error)
    } finally {
      setDetailsLoading(false)
    }
  }

  const onDrop = async (acceptedFiles) => {
    const results = {
      success: 0,
      duplicates: 0,
      errors: 0,
      total: acceptedFiles.length
    }

    for (const file of acceptedFiles) {
      try {
        const response = await documentsAPI.upload(file)
        if (response.data.is_duplicate) {
          results.duplicates++
        } else {
          results.success++
        }
      } catch (error) {
        console.error('Upload failed:', error)
        results.errors++
      }
    }

    // Show results to user
    let message = ''
    let severity = 'success'

    if (results.errors > 0) {
      severity = 'error'
      message = `${results.errors} file(s) failed to upload. `
    }
    if (results.duplicates > 0) {
      message += `${results.duplicates} duplicate(s) skipped. `
    }
    if (results.success > 0) {
      message += `${results.success} file(s) uploaded successfully.`
    }

    setUploadResult({ message, severity })
    setUploadDialog(false)
    loadDocuments()
  }

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.jpg', '.jpeg', '.png']
    },
  })

  const handleDelete = async (id) => {
    if (window.confirm('Delete this document?')) {
      try {
        await documentsAPI.delete(id)
        loadDocuments()
      } catch (error) {
        console.error('Delete failed:', error)
      }
    }
  }

  const handleDownload = async (doc) => {
    try {
      await documentsAPI.downloadFile(doc.id, doc.original_filename)
    } catch (error) {
      console.error('Download failed:', error)
    }
  }

  const getStatusColor = (status) => {
    const colors = {
      pending: 'warning',
      processing: 'info',
      completed: 'success',
      failed: 'error',
      requires_review: 'warning',
    }
    return colors[status] || 'default'
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return 'N/A'
    const units = ['B', 'KB', 'MB', 'GB']
    let i = 0
    while (bytes >= 1024 && i < units.length - 1) {
      bytes /= 1024
      i++
    }
    return `${bytes.toFixed(1)} ${units[i]}`
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Documents</Typography>
        <Button
          variant="contained"
          startIcon={<CloudUpload />}
          onClick={() => setUploadDialog(true)}
        >
          Upload Document
        </Button>
      </Box>

      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Filename</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Uploaded</TableCell>
                <TableCell>Has MRZ</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {documents.map((doc) => (
                <TableRow key={doc.id}>
                  <TableCell>{doc.id}</TableCell>
                  <TableCell>{doc.original_filename}</TableCell>
                  <TableCell>{doc.file_type.toUpperCase()}</TableCell>
                  <TableCell>
                    <Chip
                      label={doc.processing_status}
                      color={getStatusColor(doc.processing_status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {new Date(doc.uploaded_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    {doc.has_mrz ? <Chip label="Yes" color="success" size="small" /> : '-'}
                  </TableCell>
                  <TableCell>
                    <IconButton size="small" onClick={() => setSelectedDoc(doc)} title="View">
                      <Visibility />
                    </IconButton>
                    <IconButton size="small" onClick={() => handleDownload(doc)} title="Download">
                      <Download />
                    </IconButton>
                    <IconButton size="small" color="error" onClick={() => handleDelete(doc.id)} title="Delete">
                      <Delete />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={total}
          page={page}
          onPageChange={(e, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10))
            setPage(0)
          }}
        />
      </Card>

      {/* Upload Dialog */}
      <Dialog open={uploadDialog} onClose={() => setUploadDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Upload Documents</DialogTitle>
        <DialogContent>
          <Box
            {...getRootProps()}
            sx={{
              border: '2px dashed',
              borderColor: 'divider',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
            }}
          >
            <input {...getInputProps()} />
            <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography>Drag and drop files here, or click to select</Typography>
            <Typography variant="caption" color="text.secondary">
              Supported: PDF, JPG, PNG
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Document Viewer Dialog */}
      <Dialog
        open={!!selectedDoc}
        onClose={() => setSelectedDoc(null)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">
              {selectedDoc?.original_filename}
            </Typography>
            <IconButton onClick={() => setSelectedDoc(null)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {detailsLoading ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : (
            <Grid container spacing={3}>
              {/* Document Preview */}
              <Grid item xs={12} md={6}>
                <Paper
                  elevation={2}
                  sx={{
                    p: 2,
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    minHeight: 400,
                    bgcolor: 'grey.100',
                  }}
                >
                  {selectedDoc && (
                    selectedDoc.file_type === 'pdf' ? (
                      <Box sx={{ width: '100%', height: 400 }}>
                        <iframe
                          src={`${documentsAPI.getFileUrl(selectedDoc.id)}#toolbar=0`}
                          width="100%"
                          height="100%"
                          style={{ border: 'none' }}
                          title="PDF Preview"
                        />
                      </Box>
                    ) : (
                      <img
                        src={documentsAPI.getFileUrl(selectedDoc.id)}
                        alt={selectedDoc.original_filename}
                        style={{
                          maxWidth: '100%',
                          maxHeight: 400,
                          objectFit: 'contain',
                        }}
                      />
                    )
                  )}
                </Paper>
              </Grid>

              {/* Document Details */}
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Document Information
                </Typography>

                <Box mb={2}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Status
                  </Typography>
                  <Chip
                    label={selectedDoc?.processing_status}
                    color={getStatusColor(selectedDoc?.processing_status)}
                    size="small"
                  />
                </Box>

                <Box mb={2}>
                  <Typography variant="subtitle2" color="text.secondary">
                    File Type
                  </Typography>
                  <Typography>{selectedDoc?.file_type?.toUpperCase()}</Typography>
                </Box>

                <Box mb={2}>
                  <Typography variant="subtitle2" color="text.secondary">
                    File Size
                  </Typography>
                  <Typography>{formatFileSize(selectedDoc?.file_size_bytes)}</Typography>
                </Box>

                <Box mb={2}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Uploaded At
                  </Typography>
                  <Typography>
                    {selectedDoc?.uploaded_at && new Date(selectedDoc.uploaded_at).toLocaleString()}
                  </Typography>
                </Box>

                {docDetails?.has_mrz && (
                  <>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="h6" gutterBottom>
                      MRZ Data
                    </Typography>
                    {docDetails?.mrz_data && (
                      <Box>
                        <Grid container spacing={1}>
                          {docDetails.mrz_data.surname && (
                            <Grid item xs={6}>
                              <Typography variant="subtitle2" color="text.secondary">
                                Surname
                              </Typography>
                              <Typography>{docDetails.mrz_data.surname}</Typography>
                            </Grid>
                          )}
                          {docDetails.mrz_data.given_names && (
                            <Grid item xs={6}>
                              <Typography variant="subtitle2" color="text.secondary">
                                Given Names
                              </Typography>
                              <Typography>{docDetails.mrz_data.given_names}</Typography>
                            </Grid>
                          )}
                          {docDetails.mrz_data.document_number && (
                            <Grid item xs={6}>
                              <Typography variant="subtitle2" color="text.secondary">
                                Document Number
                              </Typography>
                              <Typography>{docDetails.mrz_data.document_number}</Typography>
                            </Grid>
                          )}
                          {docDetails.mrz_data.country_code && (
                            <Grid item xs={6}>
                              <Typography variant="subtitle2" color="text.secondary">
                                Country
                              </Typography>
                              <Typography>{docDetails.mrz_data.country_code}</Typography>
                            </Grid>
                          )}
                          {docDetails.mrz_data.date_of_birth && (
                            <Grid item xs={6}>
                              <Typography variant="subtitle2" color="text.secondary">
                                Date of Birth
                              </Typography>
                              <Typography>{docDetails.mrz_data.date_of_birth}</Typography>
                            </Grid>
                          )}
                          {docDetails.mrz_data.expiry_date && (
                            <Grid item xs={6}>
                              <Typography variant="subtitle2" color="text.secondary">
                                Expiry Date
                              </Typography>
                              <Typography>{docDetails.mrz_data.expiry_date}</Typography>
                            </Grid>
                          )}
                        </Grid>
                      </Box>
                    )}
                  </>
                )}

                {docDetails?.faces && docDetails.faces.length > 0 && (
                  <>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="h6" gutterBottom>
                      Detected Faces: {docDetails.faces.length}
                    </Typography>
                  </>
                )}

                {docDetails?.ocr_text && (
                  <>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="h6" gutterBottom>
                      OCR Text
                    </Typography>
                    <Paper
                      variant="outlined"
                      sx={{
                        p: 1,
                        maxHeight: 150,
                        overflow: 'auto',
                        bgcolor: 'grey.50',
                      }}
                    >
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                        {docDetails.ocr_text}
                      </Typography>
                    </Paper>
                  </>
                )}
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => selectedDoc && handleDownload(selectedDoc)} startIcon={<Download />}>
            Download
          </Button>
          <Button onClick={() => setSelectedDoc(null)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Upload result notification */}
      <Snackbar
        open={!!uploadResult}
        autoHideDuration={6000}
        onClose={() => setUploadResult(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setUploadResult(null)}
          severity={uploadResult?.severity || 'success'}
          sx={{ width: '100%' }}
        >
          {uploadResult?.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}
