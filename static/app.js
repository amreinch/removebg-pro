// QuickTools - Professional Frontend Application
const API_BASE = window.location.origin;

// State
let selectedFile = null;
let selectedFormat = 'png';
let downloadUrl = null;
let currentUser = null;
let currentTool = null;

// Handle out of credits error
function handleOutOfCredits(errorMessage) {
    // Check if error is about credits
    if (errorMessage.includes('No credits remaining') || errorMessage.includes('credits')) {
        // Show message and redirect to pricing
        alert('⚠️ No Credits Remaining!\n\nYou need credits to download. Redirecting to pricing page...');
        setTimeout(() => {
            window.location.href = '/static/index.html#pricing';
        }, 1000);
        return true;
    }
    return false;
}

// Initialize
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
            localStorage.removeItem('token');
        }
    }
    
    setupEventListeners();
}

function setupEventListeners() {
    // Upload area
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    if (uploadArea && fileInput) {
        uploadArea.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFile(e.target.files[0]);
            }
        });
        
        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#3B82F6';
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.style.borderColor = '#D1D5DB';
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#D1D5DB';
            if (e.dataTransfer.files.length > 0) {
                handleFile(e.dataTransfer.files[0]);
            }
        });
    }
    
    // Format buttons
    document.querySelectorAll('.format-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.format-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedFormat = btn.dataset.format;
        });
    });
    
    // Process button
    const processBtn = document.getElementById('processBtn');
    if (processBtn) {
        processBtn.addEventListener('click', processImage);
    }
    
    // Download button
    const downloadBtn = document.getElementById('downloadBtn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadImage);
    }
    
    // Reset button
    const resetBtn = document.getElementById('resetBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', reset);
    }
    
    // Forms
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
    }
}

// Navigation
function showLogin() {
    document.getElementById('loginModal').classList.add('active');
}

function showSignup() {
    document.getElementById('signupModal').classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

function scrollToTools() {
    document.getElementById('tools').scrollIntoView({ behavior: 'smooth' });
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
        showMessage('success', 'Welcome back!');
        
    } catch (error) {
        document.getElementById('loginError').textContent = error.message;
        document.getElementById('loginError').style.display = 'block';
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
        showMessage('success', `Welcome! You have ${currentUser.credits_balance} free credits.`);
        
    } catch (error) {
        document.getElementById('signupError').textContent = error.message;
        document.getElementById('signupError').style.display = 'block';
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
    showMessage('success', 'Signed out successfully');
    closeToolWorkspace();
}

function updateUI() {
    if (currentUser) {
        // Show user menu
        document.getElementById('authButtons').style.display = 'none';
        document.getElementById('userButtons').style.display = 'flex';
        document.getElementById('userEmail').textContent = currentUser.email;
        document.getElementById('userCredits').textContent = `${currentUser.credits_balance} credits`;
        
        // Update workspace credits if visible
        const creditsDisplay = document.getElementById('creditsDisplay');
        if (creditsDisplay) {
            creditsDisplay.textContent = `${currentUser.credits_balance} credits`;
        }
        
        // Show API nav if API access unlocked
        const apiKeysNav = document.getElementById('apiKeysNav');
        if (apiKeysNav) {
            if (currentUser.api_access_unlocked) {
                apiKeysNav.style.display = 'inline';
            } else {
                apiKeysNav.style.display = 'none';
            }
        }
    } else {
        // Show auth buttons
        document.getElementById('authButtons').style.display = 'flex';
        document.getElementById('userButtons').style.display = 'none';
    }
}

// Tool Selection
function selectTool(toolId) {
    if (!currentUser) {
        showMessage('error', 'Please sign in to use tools');
        showLogin();
        return;
    }
    
    currentTool = toolId;
    
    // Hide hero and tools section
    document.getElementById('hero').style.display = 'none';
    document.getElementById('tools').style.display = 'none';
    
    // Show workspace
    document.getElementById('toolWorkspace').style.display = 'block';
    
    // Update title
    const titles = {
        'remove-bg': 'Remove Background'
    };
    document.getElementById('workspaceTitle').textContent = titles[toolId] || 'Tool';
    
    // Update credits display
    document.getElementById('creditsDisplay').textContent = 
        `${currentUser.credits_balance} credits`;
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function closeToolWorkspace() {
    document.getElementById('toolWorkspace').style.display = 'none';
    document.getElementById('hero').style.display = 'block';
    document.getElementById('tools').style.display = 'block';
    reset();
}

function closeToolWorkspaceIfOpen(event) {
    const workspace = document.getElementById('toolWorkspace');
    if (workspace && workspace.style.display !== 'none') {
        closeToolWorkspace();
        // Let the default anchor behavior work after closing
        setTimeout(() => {
            const target = event.target.getAttribute('href');
            if (target) {
                document.querySelector(target)?.scrollIntoView({ behavior: 'smooth' });
            }
        }, 100);
        event.preventDefault();
    }
    // If workspace is not open, let the default anchor behavior work
}

// File handling
function handleFile(file) {
    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!validTypes.includes(file.type)) {
        showMessage('error', 'Invalid file type. Please upload JPG, PNG, or WebP.');
        return;
    }
    
    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
        showMessage('error', 'File too large. Maximum size is 10MB.');
        return;
    }
    
    selectedFile = file;
    document.getElementById('processBtn').disabled = false;
    
    const uploadArea = document.getElementById('uploadArea');
    uploadArea.querySelector('h3').textContent = file.name;
    uploadArea.querySelector('p').textContent = `${(file.size / 1024).toFixed(0)} KB - Ready to process`;
}

// Image processing
async function processImage() {
    if (!selectedFile || !currentUser) return;
    
    // Show processing
    document.getElementById('uploadSection').style.display = 'none';
    document.getElementById('processingSection').style.display = 'block';
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
            currentUser.credits_balance = result.credits_remaining;
            updateUI();
        }
        
    } catch (error) {
        showMessage('error', error.message);
        document.getElementById('uploadSection').style.display = 'block';
        document.getElementById('processingSection').style.display = 'none';
    }
}

function displayResults(result) {
    // Hide processing, show results
    document.getElementById('processingSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'block';
    
    // Display images
    document.getElementById('originalImage').src = URL.createObjectURL(selectedFile);
    document.getElementById('processedImage').src = result.output_url;
    
    // Store download URL
    downloadUrl = result.download_url;
}

function downloadImage() {
    if (!downloadUrl) return;
    
    // Check if user has credits
    if (currentUser.credits_balance === 0) {
        showMessage('error', 'No credits remaining. Buy more credits to continue!');
        window.location.href = '/static/index.html#pricing';
        return;
    }
    
    const token = localStorage.getItem('token');
    
    // Download via fetch
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
        const a = document.createElement('a');
        a.href = url;
        a.download = `quicktools-${Date.now()}.${selectedFormat}`;
        a.click();
        URL.revokeObjectURL(url);
        
        // Refresh user data
        loadUserProfile();
        showMessage('success', 'Image downloaded successfully!');
    })
    .catch(error => {
        showMessage('error', 'Download failed. You may be out of credits.');
    });
}

function reset() {
    selectedFile = null;
    downloadUrl = null;
    document.getElementById('processBtn').disabled = true;
    
    const uploadArea = document.getElementById('uploadArea');
    uploadArea.querySelector('h3').textContent = 'Drop your image here';
    uploadArea.querySelector('p').textContent = 'or click to browse (JPG, PNG, WebP - max 10MB)';
    document.getElementById('fileInput').value = '';
    
    document.getElementById('uploadSection').style.display = 'block';
    document.getElementById('processingSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'none';
}

// Stripe checkout
async function checkout(tier) {
    if (!currentUser) {
        showMessage('error', 'Please sign in to upgrade');
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
        window.location.href = result.url;
        
    } catch (error) {
        showMessage('error', error.message);
    }
}

// UI helpers
function showMessage(type, message) {
    const messageBox = document.getElementById('messageBox');
    if (!messageBox) return;
    
    messageBox.className = `message ${type}`;
    messageBox.textContent = message;
    messageBox.style.display = 'block';
    
    setTimeout(() => {
        messageBox.style.display = 'none';
    }, 5000);
    
    // Scroll to message
    messageBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
