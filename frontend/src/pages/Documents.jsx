import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import {
  Box,
  Button,
  Card,
  CardContent,
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
} from '@mui/material'
import { CloudUpload, Delete, Visibility } from '@mui/icons-material'
import { useDropzone } from 'react-dropzone'
import { setDocuments, setLoading } from '../store/documentsSlice'
import { documentsAPI } from '../services/api'

export default function Documents() {
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(50)
  const [uploadDialog, setUploadDialog] = useState(false)
  const [selectedDoc, setSelectedDoc] = useState(null)

  const dispatch = useDispatch()
  const { documents, total, loading } = useSelector((state) => state.documents)

  useEffect(() => {
    loadDocuments()
  }, [page, rowsPerPage])

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

  const onDrop = async (acceptedFiles) => {
    for (const file of acceptedFiles) {
      try {
        await documentsAPI.upload(file)
      } catch (error) {
        console.error('Upload failed:', error)
      }
    }
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
                    <IconButton size="small" onClick={() => setSelectedDoc(doc)}>
                      <Visibility />
                    </IconButton>
                    <IconButton size="small" color="error" onClick={() => handleDelete(doc.id)}>
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
    </Box>
  )
}
