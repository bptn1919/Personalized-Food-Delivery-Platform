import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

// Log kiểm tra
console.log('🔥🔥🔥 MAIN.JSX ĐANG CHẠY 🔥🔥🔥')
console.log('📦 Root element:', document.getElementById('root'))

try {
  const root = ReactDOM.createRoot(document.getElementById('root'))
  console.log('✅ Created root successfully')
  
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  )
  console.log('✅ Rendered successfully')
} catch (error) {
  console.error('❌ Error:', error)
}