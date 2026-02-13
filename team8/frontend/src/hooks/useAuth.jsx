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
        const res = await coreApi.get('/me/')
        return res.data.user || null
      } catch (err) {
        if (err?.response?.status === 401) return null
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
