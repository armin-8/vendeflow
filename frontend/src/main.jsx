/**
 * VendeFlow - Punto de Entrada
 * ============================
 * 
 * Este archivo inicializa React y monta la aplicación en el DOM.
 * Es equivalente al main.jsx de Revístete.
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
