import React from 'react';
import ReactDOM from 'react-dom/client';
import { InsurDrop } from './InsurDrop';
import './index.css';

// Mount to a specific div if sticking to React root, 
// OR expose as a window global for embedding.
// For the hackathon, we'll just render it as the main app.

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <InsurDrop />
  </React.StrictMode>,
);
