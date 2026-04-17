import React, { useState } from 'react';
import { API_BASE } from '../api.js';


const UploadDocument = ({ onClose }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');

  const handleUpload = async () => {
    if (!file) {
      setMessage('❌ Please select a file');
      return;
    }

    setUploading(true);
    setMessage('⏳ Uploading...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE}/upload/document`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(`✅ ${data.message}`);
        setFile(null);
        document.getElementById('fileInput').value = '';
        // Auto close after 2 seconds on success
        setTimeout(() => {
          if (onClose) onClose();
        }, 2000);
      } else {
        setMessage(`❌ ${data.detail}`);
      }
    } catch (error) {
      setMessage(`❌ Upload failed: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <p style={{ color: '#666', marginBottom: '15px', fontSize: '14px' }}>
        Upload PDF or TXT files
      </p>
      
      <input
        id="fileInput"
        type="file"
        accept=".pdf,.txt"
        onChange={(e) => setFile(e.target.files[0])}
        style={{
          display: 'block',
          width: '100%',
          padding: '8px',
          marginBottom: '10px',
          border: '1px solid #ddd',
          borderRadius: '5px',
          fontSize: '14px'
        }}
      />
      
      {file && (
        <p style={{ 
          color: '#2563eb', 
          marginBottom: '10px',
          padding: '8px',
          background: '#e3f2fd',
          borderRadius: '5px',
          fontSize: '13px'
        }}>
          📄 {file.name} ({(file.size / 1024).toFixed(2)} KB)
        </p>
      )}
      
      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        style={{
          background: file && !uploading ? '#2563eb' : '#ccc',
          color: 'white',
          padding: '10px 20px',
          border: 'none',
          borderRadius: '5px',
          fontSize: '14px',
          cursor: file && !uploading ? 'pointer' : 'not-allowed',
          width: '100%'
        }}
      >
        {uploading ? '⏳ Uploading...' : '📤 Upload'}
      </button>
      
      {message && (
        <div style={{
          marginTop: '12px',
          padding: '10px',
          borderRadius: '5px',
          background: message.includes('✅') ? '#d4edda' : '#f8d7da',
          color: message.includes('✅') ? '#155724' : '#721c24',
          border: `1px solid ${message.includes('✅') ? '#c3e6cb' : '#f5c6cb'}`,
          fontSize: '13px'
        }}>
          {message}
        </div>
      )}
    </div>
  );
};

export default UploadDocument;
