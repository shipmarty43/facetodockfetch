import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  isAuthenticated: !!localStorage.getItem('accessToken'),
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  accessToken: localStorage.getItem('accessToken'),
  refreshToken: localStorage.getItem('refreshToken'),
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials: (state, action) => {
      const { user, accessToken, refreshToken } = action.payload
      state.user = user
      state.accessToken = accessToken
      state.refreshToken = refreshToken
      state.isAuthenticated = true

      localStorage.setItem('user', JSON.stringify(user))
      localStorage.setItem('accessToken', accessToken)
      localStorage.setItem('refreshToken', refreshToken)
    },
    logout: (state) => {
      state.user = null
      state.accessToken = null
      state.refreshToken = null
      state.isAuthenticated = false

      localStorage.removeItem('user')
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
    },
  },
})

export const { setCredentials, logout } = authSlice.actions
export default authSlice.reducer
