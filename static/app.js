// RemoveBG Pro - Frontend Application Logic

const API_BASE = window.location.origin;

// State
let selectedFile = null;
let selectedFormat = 'png';
let downloadUrl = null;
let currentUser = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    // Check if user is logged in
    const token = localStorage.getItem('token');
    if (token) {
        try {
            await loadUserProfile();
        } catch (error) {
            // Token invalid, clear it
            localStorage.removeItem('token');
        }
    }
    
    setupEventListeners();
}

function setupEventListeners() {
    // Upload area
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    uploadArea.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#764ba2';
        uploadArea.style.background = '#f0f4ff';
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#667eea';
        uploadArea.style.background = '';
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#667eea';
        uploadArea.style.background = '';
        
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });
    
    // Format selection
    document.querySelectorAll('.format-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.format-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedFormat = btn.dataset.format;
        });
    });
    
    // Process button
    document.getElementById('processBtn').addEventListener('click', processImage);
    
    // Download button
    document.getElementById('downloadBtn').addEventListener('click', downloadImage);
    
    // Reset button
    document.getElementById('resetBtn').addEventListener('click', reset);
    
    // Forms
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('signupForm').addEventListener('submit', handleSignup);
}

// Navigation
function showApp() {
    document.getElementById('appContainer').style.display = 'block';
    document.getElementById('pricingContainer').style.display = 'none';
}

function showPricing() {
    document.getElementById('appContainer').style.display = 'none';
    document.getElementById('pricingContainer').style.display = 'block';
}

// Modals
function showLogin() {
    document.getElementById('loginModal').classList.add('active');
}

function showSignup() {
    document.getElementById('signupModal').classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Auth Functions
async function handleLogin(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {
        email: formData.get('email'),
        password: formData.get('password')
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }
        
        const result = await response.json();
        localStorage.setItem('token', result.access_token);
        
        closeModal('loginModal');
        await loadUserProfile();
        showSuccess('Logged in successfully!');
        
    } catch (error) {
        showError(error.message, 'loginError');
    }
}

async function handleSignup(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {
        email: formData.get('email'),
        password: formData.get('password'),
        full_name: formData.get('full_name') || null
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/auth/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Signup failed');
        }
        
        const result = await response.json();
        localStorage.setItem('token', result.access_token);
        
        closeModal('signupModal');
        await loadUserProfile();
        showSuccess('Account created successfully! You have 3 free credits.');
        
    } catch (error) {
        showError(error.message, 'signupError');
    }
}

async function loadUserProfile() {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Failed to load profile');
        
        currentUser = await response.json();
        updateUI();
        
    } catch (error) {
        console.error('Failed to load user:', error);
        localStorage.removeItem('token');
        currentUser = null;
        updateUI();
    }
}

function logout() {
    localStorage.removeItem('token');
    currentUser = null;
    updateUI();
    showSuccess('Logged out successfully');
    reset();
}

function updateUI() {
    if (currentUser) {
        // Show user menu
        document.getElementById('authButtons').style.display = 'none';
        document.getElementById('userButtons').style.display = 'flex';
        document.getElementById('userEmail').textContent = currentUser.email;
        
        // Show user info bar
        document.getElementById('userInfo').classList.add('active');
        document.getElementById('creditsRemaining').textContent = currentUser.credits_remaining;
        document.getElementById('creditsTotal').textContent = currentUser.monthly_credits;
        document.getElementById('tierBadge').textContent = currentUser.subscription_tier.toUpperCase();
        
        // Show API Keys link for Pro/Business users
        const apiKeysLink = document.getElementById('apiKeysLink');
        if (['pro', 'business'].includes(currentUser.subscription_tier)) {
            apiKeysLink.style.display = 'inline';
        } else {
            apiKeysLink.style.display = 'none';
        }
    } else {
        // Show auth buttons
        document.getElementById('authButtons').style.display = 'flex';
        document.getElementById('userButtons').style.display = 'none';
        
        // Hide user info bar
        document.getElementById('userInfo').classList.remove('active');
        
        // Hide API Keys link
        document.getElementById('apiKeysLink').style.display = 'none';
    }
}

// File handling
function handleFile(file) {
    // Check if logged in
    if (!currentUser) {
        showError('Please log in to process images');
        showLogin();
        return;
    }
    
    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
        showError('Invalid file type. Please upload JPG, PNG, or WebP.');
        return;
    }
    
    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
        showError('File too large. Maximum size is 10MB.');
        return;
    }
    
    selectedFile = file;
    document.getElementById('processBtn').disabled = false;
    document.getElementById('uploadArea').querySelector('h3').textContent = file.name;
    document.getElementById('uploadArea').querySelector('p').textContent = `${(file.size / 1024).toFixed(0)} KB - Ready to process`;
    hideError();
}

// Image processing
async function processImage() {
    if (!selectedFile || !currentUser) return;
    
    // Preview is FREE! No credit check here.
    // Credits are only checked/deducted on download.
    
    // Show loading
    document.getElementById('uploadSection').style.display = 'none';
    document.getElementById('loadingSection').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('format', selectedFormat);
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE}/api/remove-background`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Processing failed');
        }
        
        const result = await response.json();
        displayResults(result);
        
        // Update credits
        if (result.credits_remaining !== undefined) {
            currentUser.credits_remaining = result.credits_remaining;
            updateUI();
        }
        
    } catch (error) {
        showError(error.message);
        document.getElementById('uploadSection').style.display = 'block';
        document.getElementById('loadingSection').style.display = 'none';
    }
}

function displayResults(result) {
    // Hide loading, show results
    document.getElementById('loadingSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'block';
    
    // Display images
    document.getElementById('originalImage').src = URL.createObjectURL(selectedFile);
    document.getElementById('processedImage').src = result.output_url;
    
    // Preview is always watermarked (free)
    // Watermark notice is always shown in HTML
    
    // Store download URL
    downloadUrl = result.download_url;
}

function downloadImage() {
    if (!downloadUrl) return;
    
    // Check if user has credits for download
    if (currentUser.credits_remaining === 0) {
        showError('No download credits remaining. Upgrade to download clean images without watermark!');
        showPricing();
        return;
    }
    
    const token = localStorage.getItem('token');
    
    // Create download link
    const a = document.createElement('a');
    a.href = `${API_BASE}${downloadUrl}`;
    a.download = `removebg-pro-${Date.now()}.${selectedFormat}`;
    
    // Add auth header via fetch and create blob
    fetch(`${API_BASE}${downloadUrl}`, {
        headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Download failed');
        }
        return response.blob();
    })
    .then(blob => {
        const url = URL.createObjectURL(blob);
        a.href = url;
        a.click();
        URL.revokeObjectURL(url);
        
        // Refresh user data to update credits
        fetchUserProfile();
    })
    .catch(error => {
        showError('Download failed. You may be out of credits.');
    });
}

function reset() {
    selectedFile = null;
    downloadUrl = null;
    document.getElementById('processBtn').disabled = true;
    document.getElementById('uploadArea').querySelector('h3').textContent = 'Drop your image here';
    document.getElementById('uploadArea').querySelector('p').textContent = 'or click to browse (JPG, PNG, WebP - max 10MB)';
    document.getElementById('fileInput').value = '';
    
    document.getElementById('uploadSection').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
}

// Stripe checkout
async function checkout(tier) {
    if (!currentUser) {
        showError('Please log in to upgrade');
        showLogin();
        return;
    }
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE}/api/create-checkout-session`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ tier })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Checkout failed');
        }
        
        const result = await response.json();
        
        // Redirect to Stripe Checkout
        window.location.href = result.url;
        
    } catch (error) {
        showError(error.message);
    }
}

// UI helpers
function showError(message, elementId = 'errorBox') {
    const errorBox = document.getElementById(elementId);
    errorBox.textContent = message;
    errorBox.style.display = 'block';
    
    setTimeout(() => {
        errorBox.style.display = 'none';
    }, 5000);
}

function hideError(elementId = 'errorBox') {
    document.getElementById(elementId).style.display = 'none';
}

function showSuccess(message, elementId = 'successBox') {
    const successBox = document.getElementById(elementId);
    successBox.textContent = message;
    successBox.style.display = 'block';
    
    setTimeout(() => {
        successBox.style.display = 'none';
    }, 5000);
}
