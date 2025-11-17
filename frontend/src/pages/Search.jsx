import { useState, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import {
  Box,
  Card,
  CardContent,
  Button,
  Typography,
  Slider,
  Grid,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
} from '@mui/material'
import { CloudUpload, Videocam } from '@mui/icons-material'
import Webcam from 'react-webcam'
import { useDropzone } from 'react-dropzone'
import { setResults, setLoading, setSimilarityThreshold } from '../store/searchSlice'
import { searchAPI } from '../services/api'

export default function Search() {
  const [searchMode, setSearchMode] = useState('upload') // upload, webcam
  const [previewImage, setPreviewImage] = useState(null)
  const [error, setError] = useState('')

  const webcamRef = useRef(null)
  const dispatch = useDispatch()
  const { results, loading, similarityThreshold } = useSelector((state) => state.search)

  const onDrop = (acceptedFiles) => {
    const file = acceptedFiles[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = () => {
        setPreviewImage(reader.result)
      }
      reader.readAsDataURL(file)
    }
  }

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png'] },
    multiple: false,
  })

  const captureWebcam = () => {
    const imageSrc = webcamRef.current.getScreenshot()
    setPreviewImage(imageSrc)
  }

  const handleSearch = async () => {
    if (!previewImage) {
      setError('Please select or capture an image first')
      return
    }

    setError('')
    dispatch(setLoading(true))

    try {
      // Remove data URL prefix
      const base64Image = previewImage.split(',')[1]

      const response = await searchAPI.searchByFace({
        image_base64: base64Image,
        similarity_threshold: similarityThreshold,
        max_results: 10,
      })

      dispatch(setResults(response.data.results))
    } catch (err) {
      setError(err.response?.data?.detail || 'Search failed')
    } finally {
      dispatch(setLoading(false))
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Face Search
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Tabs value={searchMode} onChange={(e, v) => setSearchMode(v)} sx={{ mb: 2 }}>
                <Tab label="Upload Photo" value="upload" />
                <Tab label="Webcam" value="webcam" />
              </Tabs>

              {searchMode === 'upload' ? (
                <Box
                  {...getRootProps()}
                  sx={{
                    border: '2px dashed',
                    borderColor: 'divider',
                    borderRadius: 2,
                    p: 4,
                    textAlign: 'center',
                    cursor: 'pointer',
                    '&:hover': { borderColor: 'primary.main' },
                  }}
                >
                  <input {...getInputProps()} />
                  <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                  <Typography>Drag and drop image here, or click to select</Typography>
                </Box>
              ) : (
                <Box textAlign="center">
                  <Webcam
                    ref={webcamRef}
                    screenshotFormat="image/jpeg"
                    style={{ width: '100%', borderRadius: 8 }}
                  />
                  <Button
                    variant="contained"
                    startIcon={<Videocam />}
                    onClick={captureWebcam}
                    sx={{ mt: 2 }}
                  >
                    Capture Photo
                  </Button>
                </Box>
              )}

              {previewImage && (
                <Box mt={3}>
                  <Typography variant="h6" gutterBottom>
                    Preview
                  </Typography>
                  <img src={previewImage} alt="Preview" style={{ width: '100%', borderRadius: 8 }} />
                </Box>
              )}

              <Box mt={3}>
                <Typography gutterBottom>
                  Similarity Threshold: {(similarityThreshold * 100).toFixed(0)}%
                </Typography>
                <Slider
                  value={similarityThreshold}
                  onChange={(e, v) => dispatch(setSimilarityThreshold(v))}
                  min={0.4}
                  max={0.9}
                  step={0.05}
                  marks
                  valueLabelDisplay="auto"
                  valueLabelFormat={(v) => `${(v * 100).toFixed(0)}%`}
                />
              </Box>

              {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {error}
                </Alert>
              )}

              <Button
                fullWidth
                variant="contained"
                size="large"
                onClick={handleSearch}
                disabled={loading || !previewImage}
                sx={{ mt: 2 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Search'}
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Search Results ({results.length})
              </Typography>

              {results.length === 0 ? (
                <Typography color="text.secondary">
                  No results yet. Upload an image and click Search.
                </Typography>
              ) : (
                <Box>
                  {results.map((result, index) => (
                    <Card key={index} sx={{ mb: 2 }}>
                      <CardContent>
                        <Typography variant="h6">
                          Match: {(result.similarity_score * 100).toFixed(1)}%
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Document: {result.document_info.filename}
                        </Typography>
                        {result.mrz_data && (
                          <Box mt={1}>
                            <Typography variant="body2">
                              Name: {result.mrz_data.given_names} {result.mrz_data.surname}
                            </Typography>
                            <Typography variant="body2">
                              Document #: {result.mrz_data.document_number}
                            </Typography>
                          </Box>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
