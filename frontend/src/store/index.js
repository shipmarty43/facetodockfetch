import { configureStore } from '@reduxjs/toolkit'
import authReducer from './authSlice'
import documentsReducer from './documentsSlice'
import searchReducer from './searchSlice'

export default configureStore({
  reducer: {
    auth: authReducer,
    documents: documentsReducer,
    search: searchReducer,
  },
})
