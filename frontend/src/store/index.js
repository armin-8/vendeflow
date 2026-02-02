/**
 * VendeFlow - Store Global (Zustand)
 * ===================================
 * 
 * DIFERENCIA CON REVÍSTETE (useReducer):
 * --------------------------------------
 * 
 * En Revístete usabas useReducer + Context, así:
 * 
 *    const [store, dispatch] = useReducer(storeReducer, initialStore)
 *    dispatch({ type: 'auth_success', payload: { token, user } })
 * 
 * Con Zustand es MÁS SIMPLE:
 * 
 *    const { token, user, login } = useAuthStore()
 *    login(token, user)  // ← Llamas directamente a la función
 * 
 * VENTAJAS DE ZUSTAND:
 * - Sin Provider (no necesitas envolver la app)
 * - Menos código
 * - Más fácil de entender
 * - Mejor performance
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/**
 * Store de Autenticación
 * ----------------------
 * Maneja el estado del usuario y token JWT.
 */
export const useAuthStore = create(
  persist(
    (set, get) => ({
      // ═══════════════════════════════════════════════════════
      // ESTADO
      // ═══════════════════════════════════════════════════════
      
      token: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      
      // ═══════════════════════════════════════════════════════
      // ACCIONES
      // ═══════════════════════════════════════════════════════
      
      /**
       * Guarda los datos después del login/registro exitoso.
       */
      login: (token, user) => {
        set({
          token,
          user,
          isAuthenticated: true,
          error: null
        })
      },
      
      /**
       * Limpia el estado al cerrar sesión.
       */
      logout: () => {
        set({
          token: null,
          user: null,
          isAuthenticated: false,
          error: null
        })
      },
      
      /**
       * Actualiza los datos del usuario.
       */
      updateUser: (userData) => {
        set({
          user: { ...get().user, ...userData }
        })
      },
      
      /**
       * Establece el estado de carga.
       */
      setLoading: (isLoading) => {
        set({ isLoading })
      },
      
      /**
       * Establece un error.
       */
      setError: (error) => {
        set({ error })
      },
      
      /**
       * Limpia el error.
       */
      clearError: () => {
        set({ error: null })
      }
    }),
    {
      name: 'vendeflow-auth', // Nombre para localStorage
      partialize: (state) => ({
        // Solo persistimos token y user (no isLoading ni error)
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
)


/**
 * Store de UI
 * -----------
 * Maneja estados de la interfaz (sidebar, modales, etc.)
 */
export const useUIStore = create((set) => ({
  // Estado del sidebar
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  
  // Notificaciones/Toast
  notification: null,
  showNotification: (message, type = 'info') => {
    set({ notification: { message, type } })
    // Auto-ocultar después de 5 segundos
    setTimeout(() => set({ notification: null }), 5000)
  },
  hideNotification: () => set({ notification: null })
}))
