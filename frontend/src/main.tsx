import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// StrictMode is intentionally omitted: its dev-only double-mount opens and
// immediately closes the WebSocket, breaking the live agent stream.
ReactDOM.createRoot(document.getElementById('root')!).render(<App />)
