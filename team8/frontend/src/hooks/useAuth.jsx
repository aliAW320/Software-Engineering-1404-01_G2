import { createContext, useContext, useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api, coreApi } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const queryClient = useQueryClient()

  const { data: profile, isLoading: authLoading } = useQuery({
    queryKey: ['auth', 'profile'],
    queryFn: async () => {
      try {
        // Use Team8 profile endpoint so local fields (user_id/is_admin/username) are available.
        const res = await api.get('/auth/profile/')
        return res.data.user || null
      } catch (err) {
        const status = err?.response?.status
        if (status === 401 || status === 403) return null
        throw err
      }
    },
    retry: false,
    staleTime: 1000 * 60 * 5,
  })

  const login = async (payload) => {
    const res = await coreApi.post('/login/', payload)
    await queryClient.invalidateQueries({ queryKey: ['auth'] })
    return res.data
  }

  const register = async (payload) => {
    const res = await coreApi.post('/signup/', payload)
    await queryClient.invalidateQueries({ queryKey: ['auth'] })
    return res.data
  }

  const logout = async () => {
    try {
      await coreApi.post('/logout/')
    } catch (err) {
      // ignore
    }
    queryClient.removeQueries()
  }

  const value = useMemo(
    () => ({
      user: profile,
      authLoading,
      login,
      register,
      logout,
      isAuthenticated: !!profile,
    }),
    [profile, authLoading]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
