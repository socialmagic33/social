// LeadMagic JavaScript

// CSRF Token management
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
}

// API request helper
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': getCSRFToken(),
            ...options.headers
        }
    };

    const response = await fetch(url, { ...defaultOptions, ...options });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Request failed');
    }
    
    return response.json();
}

// Show alert messages
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alert-container') || createAlertContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} fade-in`;
    alert.innerHTML = `
        ${message}
        <button onclick="this.parentElement.remove()" style="float: right; background: none; border: none; font-size: 1.2rem; cursor: pointer;">&times;</button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentElement) {
            alert.remove();
        }
    }, 5000);
}

function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alert-container';
    container.style.position = 'fixed';
    container.style.top = '1rem';
    container.style.right = '1rem';
    container.style.zIndex = '1000';
    container.style.maxWidth = '400px';
    document.body.appendChild(container);
    return container;
}

// Form validation
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('error');
            isValid = false;
        } else {
            input.classList.remove('error');
        }
    });
    
    return isValid;
}

// Password strength checker
function checkPasswordStrength(password) {
    const checks = {
        length: password.length >= 8,
        uppercase: /[A-Z]/.test(password),
        lowercase: /[a-z]/.test(password),
        number: /[0-9]/.test(password),
        special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };
    
    return checks;
}

function updatePasswordStrength(passwordInput, strengthContainer) {
    const password = passwordInput.value;
    const checks = checkPasswordStrength(password);
    
    const requirements = [
        { key: 'length', text: 'At least 8 characters' },
        { key: 'uppercase', text: 'One uppercase letter' },
        { key: 'lowercase', text: 'One lowercase letter' },
        { key: 'number', text: 'One number' },
        { key: 'special', text: 'One special character' }
    ];
    
    strengthContainer.innerHTML = requirements.map(req => 
        `<div class="${checks[req.key] ? 'text-success' : 'text-secondary'}">${req.text}</div>`
    ).join('');
}

// File upload with progress
function setupFileUpload(inputElement, progressCallback) {
    inputElement.addEventListener('change', async (e) => {
        const files = Array.from(e.target.files);
        
        for (const file of files) {
            await uploadFile(file, progressCallback);
        }
    });
}

async function uploadFile(file, progressCallback) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                progressCallback?.(percentComplete);
            }
        });
        
        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                showAlert('File uploaded successfully', 'success');
            } else {
                showAlert('Upload failed', 'error');
            }
        });
        
        xhr.open('POST', '/api/media/upload');
        xhr.setRequestHeader('X-CSRF-Token', getCSRFToken());
        xhr.send(formData);
        
    } catch (error) {
        showAlert(`Upload failed: ${error.message}`, 'error');
    }
}

// Drag and drop file upload
function setupDragAndDrop(dropZone, fileInput) {
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files);
        fileInput.files = e.dataTransfer.files;
        
        // Trigger change event
        fileInput.dispatchEvent(new Event('change'));
    });
}

// Media gallery filtering
function filterMedia(status) {
    const mediaItems = document.querySelectorAll('.media-item');
    const filterButtons = document.querySelectorAll('.filter-btn');
    
    // Update active button
    filterButtons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Filter items
    mediaItems.forEach(item => {
        if (status === 'all' || item.dataset.status === status) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

// Auto-save form data
function setupAutoSave(form, saveKey) {
    const inputs = form.querySelectorAll('input, textarea, select');
    
    // Load saved data
    const savedData = localStorage.getItem(saveKey);
    if (savedData) {
        const data = JSON.parse(savedData);
        inputs.forEach(input => {
            if (data[input.name]) {
                input.value = data[input.name];
            }
        });
    }
    
    // Save on change
    inputs.forEach(input => {
        input.addEventListener('change', () => {
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            localStorage.setItem(saveKey, JSON.stringify(data));
        });
    });
    
    // Clear on submit
    form.addEventListener('submit', () => {
        localStorage.removeItem(saveKey);
    });
}

// Schedule posts
async function schedulePosts() {
    try {
        const response = await apiRequest('/api/posts/schedule', {
            method: 'POST'
        });
        
        showAlert('Posts scheduled successfully', 'success');
        setTimeout(() => window.location.reload(), 1000);
        
    } catch (error) {
        showAlert(`Failed to schedule posts: ${error.message}`, 'error');
    }
}

// Process jobsite media
async function processJobsiteMedia(jobsiteId) {
    try {
        const response = await apiRequest(`/api/posts/process-media/${jobsiteId}`, {
            method: 'POST'
        });
        
        showAlert('Media processed successfully', 'success');
        setTimeout(() => window.location.reload(), 1000);
        
    } catch (error) {
        showAlert(`Failed to process media: ${error.message}`, 'error');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Add fade-in animation to elements
    document.querySelectorAll('[data-fade-in]').forEach(el => {
        el.classList.add('fade-in');
    });
    
    // Setup password strength checker
    const passwordInput = document.getElementById('password');
    const strengthContainer = document.getElementById('password-strength');
    if (passwordInput && strengthContainer) {
        passwordInput.addEventListener('input', () => {
            updatePasswordStrength(passwordInput, strengthContainer);
        });
    }
    
    // Setup file upload
    const fileInput = document.querySelector('input[type="file"]');
    const dropZone = document.querySelector('.file-upload');
    if (fileInput && dropZone) {
        setupDragAndDrop(dropZone, fileInput);
    }
    
    // Setup auto-save for forms
    const forms = document.querySelectorAll('form[data-autosave]');
    forms.forEach(form => {
        const saveKey = form.dataset.autosave;
        setupAutoSave(form, saveKey);
    });
});

// Export functions for global use
window.LeadMagic = {
    showAlert,
    validateForm,
    schedulePosts,
    processJobsiteMedia,
    filterMedia,
    apiRequest
};