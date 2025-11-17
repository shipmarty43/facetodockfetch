import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  results: [],
  loading: false,
  similarityThreshold: 0.6,
  query: null,
}

const searchSlice = createSlice({
  name: 'search',
  initialState,
  reducers: {
    setResults: (state, action) => {
      state.results = action.payload
    },
    setLoading: (state, action) => {
      state.loading = action.payload
    },
    setSimilarityThreshold: (state, action) => {
      state.similarityThreshold = action.payload
    },
    setQuery: (state, action) => {
      state.query = action.payload
    },
  },
})

export const { setResults, setLoading, setSimilarityThreshold, setQuery } = searchSlice.actions
export default searchSlice.reducer
