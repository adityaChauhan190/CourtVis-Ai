'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

interface User {
  id: string
  email: string
  name: string
  role: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (token: string, user: User) => void
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    // Check localStorage for token on mount
    const storedToken = localStorage.getItem('access_token')
    if (storedToken) {
      setToken(storedToken)
      // Validate the stored token against the server
      fetch((process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000') + '/api/auth/me', {
        headers: { Authorization: `Bearer ${storedToken}` }
      })
        .then(res => {
          if (res.ok) return res.json()
          // Token is invalid/expired — clear it and redirect
          throw new Error('Invalid token')
        })
        .then(userData => {
          setUser(userData)
        })
        .catch(() => {
          // Inline logout to avoid stale closure issues
          localStorage.removeItem('access_token')
          setToken(null)
          setUser(null)
          if (window.location.pathname !== '/auth') {
            router.push('/auth')
          }
        })
        .finally(() => setIsLoading(false))
    } else {
      setIsLoading(false)
      // If we are not on the auth page, redirect
      if (window.location.pathname !== '/auth') {
        router.push('/auth')
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const login = (newToken: string, userData: User) => {
    localStorage.setItem('access_token', newToken)
    setToken(newToken)
    setUser(userData)
    router.push('/workspace') // Default redirect after login
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    setToken(null)
    setUser(null)
    router.push('/auth')
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
