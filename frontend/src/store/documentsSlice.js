import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  documents: [],
  total: 0,
  page: 1,
  pageSize: 50,
  loading: false,
  selectedDocument: null,
}

const documentsSlice = createSlice({
  name: 'documents',
  initialState,
  reducers: {
    setDocuments: (state, action) => {
      state.documents = action.payload.documents
      state.total = action.payload.total
      state.page = action.payload.page
      state.pageSize = action.payload.pageSize
    },
    setLoading: (state, action) => {
      state.loading = action.payload
    },
    setSelectedDocument: (state, action) => {
      state.selectedDocument = action.payload
    },
  },
})

export const { setDocuments, setLoading, setSelectedDocument } = documentsSlice.actions
export default documentsSlice.reducer
