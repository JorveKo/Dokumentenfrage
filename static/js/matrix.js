// static/js/matrix.js

import MatrixUtils from './utils.js';

// Matrix Rain Effect Class
class MatrixRain {
    constructor() {
        this.canvas = document.getElementById('matrixCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.characters = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン";
        this.fontSize = 14;
        this.drops = [];
        
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
        this.initDrops();
        this.animate();
    }
    
    resizeCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        this.columns = Math.floor(this.canvas.width / this.fontSize);
    }
    
    initDrops() {
        this.drops = Array(this.columns).fill(1);
    }
    
    animate() {
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.ctx.fillStyle = '#0F0';
        this.ctx.font = `${this.fontSize}px monospace`;
        
        for (let i = 0; i < this.drops.length; i++) {
            const char = this.characters[Math.floor(Math.random() * this.characters.length)];
            this.ctx.fillText(char, i * this.fontSize, this.drops[i] * this.fontSize);
            
            if (this.drops[i] * this.fontSize > this.canvas.height && Math.random() > 0.975) {
                this.drops[i] = 0;
            }
            this.drops[i]++;
        }
        requestAnimationFrame(() => this.animate());
    }
}

// Dashboard Controller Class
class DashboardController {
    constructor() {
        this.initializeVariables();
        this.initializeWebSocket();
        this.setupEventListeners();
        this.setupCharts();
        this.startPeriodicUpdates();
    }
    
    initializeVariables() {
        this.status = {
            isRunning: false,
            currentTerm: '',
            progress: 0,
            totalDocuments: 0,
            completedTerms: new Set(),
            error: null,
            apiCosts: 0,
            downloadedFiles: 0,
            successfulDownloads: 0,
            failedDownloads: 0,
            totalBytes: 0,
            processingSpeed: 0
        };
        
        this.charts = {
            typeChart: null,
            progressChart: null
        };
        
        this.updateIntervals = {
            status: null,
            stats: null,
            health: null
        };
    }
    
    // WebSocket Setup and Management
    initializeWebSocket() {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/${this.generateClientId()}`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            MatrixUtils.debug.log('WebSocket Connected');
            this.showNotification('Connected to Matrix', 'success');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.ws.onclose = () => {
            MatrixUtils.debug.log('WebSocket Disconnected - Attempting Reconnect');
            setTimeout(() => this.initializeWebSocket(), 5000);
        };
        
        this.ws.onerror = (error) => {
            MatrixUtils.debug.error('WebSocket Error:', error);
        };
    }
    
    generateClientId() {
        return `client_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    // Event Listeners Setup
    setupEventListeners() {
        // Theme Switcher
        document.getElementById('themeSelector')?.addEventListener('change', (e) => {
            document.body.dataset.theme = e.target.value;
            MatrixUtils.storage.set('theme', e.target.value);
        });
        
        // Control Buttons
        document.getElementById('startButton')?.addEventListener('click', () => this.startScraping());
        document.getElementById('stopButton')?.addEventListener('click', () => this.stopScraping());
        document.getElementById('checkHealth')?.addEventListener('click', () => this.performHealthCheck());
        
        // Advanced Options Toggle
        document.getElementById('advancedOptionsToggle')?.addEventListener('click', () => {
            const options = document.getElementById('advancedOptions');
            options?.classList.toggle('hidden');
        });
        
        // Console Controls
        document.getElementById('clearConsole')?.addEventListener('click', () => {
            const console = document.getElementById('matrixConsole');
            if (console) console.innerHTML = '';
        });
        
        document.getElementById('logLevel')?.addEventListener('change', (e) => {
            const console = document.getElementById('matrixConsole');
            if (console) {
                const entries = console.getElementsByClassName('console-entry');
                Array.from(entries).forEach(entry => {
                    entry.style.display = e.target.value === 'all' || entry.classList.contains(e.target.value)
                        ? 'block' : 'none';
                });
            }
        });
        
        // Similarity Threshold Slider
        const slider = document.getElementById('similarityThreshold');
        const sliderValue = document.getElementById('similarityValue');
        if (slider && sliderValue) {
            slider.addEventListener('input', (e) => {
                sliderValue.textContent = e.target.value;
            });
        }
        
        // File Type Selection
        document.querySelectorAll('.fileType').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    document.querySelectorAll('.fileType').forEach(cb => {
                        if (cb !== e.target) cb.checked = false;
                    });
                }
            });
        });
    }

// Charts Setup
setupCharts() {
    // Document Type Distribution Chart
    const typeCtx = document.getElementById('documentTypeChart')?.getContext('2d');
    if (typeCtx) {
        this.charts.typeChart = new Chart(typeCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        'rgba(0, 255, 0, 0.8)',
                        'rgba(0, 200, 0, 0.8)',
                        'rgba(0, 150, 0, 0.8)',
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#00ff00'
                        }
                    }
                }
            }
        });
    }
}

// Periodic Updates
startPeriodicUpdates() {
    this.updateIntervals.status = setInterval(() => this.updateStatus(), 1000);
    this.updateIntervals.stats = setInterval(() => this.updateStats(), 5000);
    this.updateIntervals.health = setInterval(() => this.performHealthCheck(), 3000);
}

async startScraping() {
    const term = document.getElementById('searchTerm')?.value;
    const maxResults = document.getElementById('maxResults')?.value;
    const fileTypes = Array.from(document.getElementsByClassName('fileType'))
        .filter(cb => cb.checked)
        .map(cb => cb.value);
    const similarityThreshold = document.getElementById('similarityThreshold')?.value;
    
    if (!term || fileTypes.length === 0) {
        this.showNotification('Bitte geben Sie einen Suchbegriff ein und wählen Sie mindestens einen Dokumenttyp aus.', 'error');
        return;
    }
    
    const requestData = {
        term: term,
        file_type: fileTypes[0],
        max_results: parseInt(maxResults),
        similarity_threshold: parseFloat(similarityThreshold) / 100
    };
    
    try {
        MatrixUtils.debug.log('Starting scraping process...', 'info');
        const response = await fetch('/api/scraping/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            this.updateButtonStates(true);
            this.showNotification('Neural Document Acquisition Initialized', 'success');
            this.addLogEntry('System initialized and running', 'success');
        } else {
            this.showNotification(data.error || 'Error initializing system', 'error');
            this.addLogEntry(`Initialization error: ${data.error}`, 'error');
        }
        
    } catch (error) {
        this.showNotification(`System Error: ${error.message}`, 'error');
        this.addLogEntry(`System error: ${error.message}`, 'error');
    }
}

async stopScraping() {
    try {
        const response = await fetch('/api/scraping/stop', { method: 'POST' });
        
        if (response.ok) {
            this.updateButtonStates(false);
            this.showNotification('Neural Process Terminated', 'info');
            this.addLogEntry('System shutdown completed', 'info');
        }
    } catch (error) {
        this.showNotification(`Termination Error: ${error.message}`, 'error');
        this.addLogEntry(`Termination error: ${error.message}`, 'error');
    }
}

async performHealthCheck() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        this.updateHealthDisplay(data);
    } catch (error) {
        this.updateHealthDisplay({
            status: 'unhealthy',
            database: 'disconnected',
            filesystem: 'error',
            scraping_active: false
        });
    }
}

// UI Updates
updateHealthDisplay(health) {
    const indicators = {
        'system-health': health.status,
        'db-health': health.database,
        'fs-health': health.filesystem,
        'scraper-health': health.scraping_active ? 'active' : 'inactive'
    };
    
    Object.entries(indicators).forEach(([id, status]) => {
        const element = document.getElementById(id);
        if (element) {
            element.className = `health-status ${this.getHealthStatusClass(status)}`;
            element.textContent = status;
        }
    });
    
    document.getElementById('lastHealthCheck').textContent = 
        `Last Check: ${new Date().toLocaleTimeString()}`;
}

getHealthStatusClass(status) {
    return ['healthy', 'connected', 'active', 'ok'].includes(status) 
        ? 'healthy' : 'unhealthy';
}

updateButtonStates(isRunning) {
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');
    
    if (startButton) startButton.disabled = isRunning;
    if (stopButton) stopButton.disabled = !isRunning;
}

async updateStatus() {
    try {
        const response = await fetch('/api/scraping/status');
        const data = await response.json();
        this.updateStatusDisplay(data);
    } catch (error) {
        MatrixUtils.debug.error('Status update failed:', error);
    }
}

async updateStats() {
    try {
        const response = await fetch('/api/scraping/stats');
        const data = await response.json();
        this.updateStatsDisplay(data);
    } catch (error) {
        MatrixUtils.debug.error('Stats update failed:', error);
    }
}

updateStatusDisplay(status) {
    // Progress Bar
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    if (progressBar && progressText) {
        progressBar.style.width = `${status.progress}%`;
        progressText.textContent = `${Math.round(status.progress)}%`;
    }
    
    // Current Term
    const currentTermText = document.getElementById('currentTermText');
    if (currentTermText) {
        currentTermText.textContent = `Current Term: ${status.current_term || 'None'}`;
    }
    
    // Process Counts
    document.getElementById('processedCount').textContent = status.downloaded_files;
    document.getElementById('successCount').textContent = status.successful_downloads;
    document.getElementById('failCount').textContent = status.failed_downloads;
    
    // API Costs
    document.getElementById('apiCosts').textContent = 
        MatrixUtils.format.currency(status.api_costs);
    
    // Update Button States
    this.updateButtonStates(status.is_running);
}

updateStatsDisplay(stats) {
    if (this.charts.typeChart) {
        this.charts.typeChart.data.labels = Object.keys(stats.documents_per_type);
        this.charts.typeChart.data.datasets[0].data = Object.values(stats.documents_per_type);
        this.charts.typeChart.update();
    }
    
    document.getElementById('totalSize').textContent = 
        MatrixUtils.format.bytes(stats.total_size);
    document.getElementById('processingSpeed').textContent = 
        `${Math.round(stats.processing_speed)} docs/min`;
    document.getElementById('successRate').textContent = 
        MatrixUtils.format.percentage(stats.success_rate, 100);
}

showNotification(message, type = 'info') {
    const notification = MatrixUtils.dom.create('div', 
        ['matrix-notification', `matrix-notification-${type}`]);
    notification.textContent = message;
    
    document.getElementById('notificationContainer').appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

addLogEntry(message, type = 'info') {
    const console = document.getElementById('matrixConsole');
    if (!console) return;
    
    const entry = document.createElement('div');
    entry.className = `console-entry ${type}`;
    
    const timestamp = new Date().toLocaleTimeString();
    entry.textContent = `[${timestamp}] ${message}`;
    
    console.insertBefore(entry, console.firstChild);
    
    while (console.children.length > 100) {
        console.removeChild(console.lastChild);
    }
}

handleWebSocketMessage(data) {
    switch (data.type) {
        case 'status_update':
            this.updateStatusDisplay(data.data.scraping_status);
            this.updateStatsDisplay(data.data.stats);
            break;
        case 'error':
            this.showNotification(data.data.message, 'error');
            this.addLogEntry(data.data.message, 'error');
            break;
        case 'notification':
            this.showNotification(data.data.message, data.data.level);
            this.addLogEntry(data.data.message, data.data.level);
            break;
    }
}

async updateRecentDocuments() {
    try {
        const response = await fetch('/api/documents/recent');
        const data = await response.json();
        
        const recentDocs = document.getElementById('recentDocuments');
        document.getElementById('displayedCount').textContent = 
            data.documents.length;
        document.getElementById('totalCount').textContent = 
            data.total_count;

        recentDocs.innerHTML = data.documents
            .map(doc => `
                <div class="matrix-document-item fade-in">
                    <div class="flex justify-between items-center">
                        <span class="font-medium truncate" title="${doc.title}">
                            ${doc.title}
                        </span>
                        <span class="text-sm opacity-75">
                            ${MatrixUtils.format.bytes(doc.size)}
                        </span>
                    </div>
                    <div class="flex justify-between text-sm opacity-75">
                        <span>${doc.file_type.toUpperCase()}</span>
                        <span>${new Date(doc.timestamp).toLocaleString()}</span>
                    </div>
                    <div class="text-sm opacity-75">
                        Search term: ${doc.term}
                    </div>
                </div>
            `)
            .join('');
    } catch (error) {
        this.showNotification('Failed to load recent documents', 'error');
    }
}

async handleStatusUpdate(status) {
    this.updateStatusDisplay(status);
    this.updateStatsDisplay(status);
    if (status.downloaded_files > 0) {
        await this.updateRecentDocuments();
    }
}
}

// Initialize on DOM Load
document.addEventListener('DOMContentLoaded', () => {
new MatrixRain();
window.dashboard = new DashboardController();
});

// End of File