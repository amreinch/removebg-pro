// RemoveBG Pro - Frontend JavaScript

// DOM elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const processing = document.getElementById('processing');
const result = document.getElementById('result');
const originalImage = document.getElementById('original-image');
const resultImage = document.getElementById('result-image');
const originalSize = document.getElementById('original-size');
const resultSize = document.getElementById('result-size');
const downloadBtn = document.getElementById('download-btn');

let currentDownloadUrl = null;

// File input change
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
});

// Drag and drop
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        handleFile(file);
    } else {
        alert('Please drop an image file (JPG, PNG, WebP)');
    }
});

// Handle file upload and processing
async function handleFile(file) {
    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
        alert('File too large! Maximum size is 10MB');
        return;
    }
    
    // Show original image preview
    const reader = new FileReader();
    reader.onload = (e) => {
        originalImage.src = e.target.result;
    };
    reader.readAsDataURL(file);
    
    // Show processing state
    dropZone.style.display = 'none';
    processing.style.display = 'block';
    result.style.display = 'none';
    
    // Prepare form data
    const formData = new FormData();
    formData.append('file', file);
    formData.append('format', 'png');
    
    try {
        // Call API
        const response = await fetch('/api/remove-background', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Processing failed');
        }
        
        const data = await response.json();
        
        // Display result
        displayResult(data);
        
    } catch (error) {
        console.error('Error:', error);
        alert(`Error: ${error.message}`);
        resetUpload();
    }
}

// Display processing result
function displayResult(data) {
    // Hide processing, show result
    processing.style.display = 'none';
    result.style.display = 'block';
    
    // Set result image
    resultImage.src = data.output_url;
    
    // Set file sizes
    originalSize.textContent = formatFileSize(data.original_size);
    resultSize.textContent = formatFileSize(data.output_size);
    
    // Set download URL
    currentDownloadUrl = data.download_url;
    
    // Add download handler
    downloadBtn.onclick = () => {
        downloadImage(currentDownloadUrl, data.output_filename);
    };
}

// Download image
function downloadImage(url, filename) {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

// Reset upload interface
function resetUpload() {
    dropZone.style.display = 'block';
    processing.style.display = 'none';
    result.style.display = 'none';
    fileInput.value = '';
    currentDownloadUrl = null;
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Track page views (optional analytics)
if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    // Add analytics here (Google Analytics, Plausible, etc.)
}

console.log('RemoveBG Pro v1.0.0 - Ready!');
