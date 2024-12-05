// static/js/matrix.js

import MatrixUtils from './utils.js';

// static/js/matrix.js

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
    }

    generateClientId() {
        return 'client_' + Math.random().toString(36).substr(2, 9);
    }
    
    initializeWebSocket() {
        const wsUrl = `ws://${window.location.host}/ws/${this.generateClientId()}`;
        console.log('Initializing WebSocket connection to:', wsUrl);
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected successfully');
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket connection closed');
        };
        
        this.ws.onmessage = (event) => {
            console.log('WebSocket message received:', event.data);
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
    }
    
    setupEventListeners() {
        // Start Button
        const startButton = document.getElementById('startButton');
        if (startButton) {
            startButton.addEventListener('click', () => this.startScraping());
        }
        
        // Health Check Button
        const healthCheckButton = document.getElementById('checkHealth');
        if (healthCheckButton) {
            healthCheckButton.addEventListener('click', () => this.forceHealthCheck());
        }
    }
    
    async startScraping() {
        console.log('Start button clicked');
        try {
            const searchTerm = document.getElementById('searchTerm').value;
            const maxResults = parseInt(document.getElementById('maxResults').value);
            
            console.log('Sending scraping request with:', { searchTerm, maxResults });
            
            const response = await fetch('/api/scraping/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    term: searchTerm,
                    file_type: 'pdf',
                    max_results: maxResults
                })
            });
            
            const data = await response.json();
            console.log('API response:', data);
            
            if (data.status === 'success') {
                this.showNotification('Scraping started successfully', 'success');
            } else {
                this.showNotification('Failed to start scraping', 'error');
            }
        } catch (error) {
            console.error('Error starting scraping:', error);
            this.showNotification('Error starting scraping process', 'error');
        }
    }
    
    async forceHealthCheck() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            this.updateHealthStatus(data);
        } catch (error) {
            console.error('Health check error:', error);
        }
    }
    
    setupCharts() {
        // Chart setup code here
    }
    
    startPeriodicUpdates() {
        setInterval(() => this.forceHealthCheck(), 30000); // Every 30 seconds
    }
    
    showNotification(message, type = 'info') {
        const container = document.getElementById('notificationContainer');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        container.appendChild(notification);
        setTimeout(() => notification.remove(), 5000);
    }
    
    updateHealthStatus(data) {
        document.getElementById('system-health').textContent = data.status;
        document.getElementById('db-health').textContent = data.database;
        document.getElementById('fs-health').textContent = data.filesystem || 'checking...';
        document.getElementById('scraper-health').textContent = 
            data.scraping_active ? 'active' : 'idle';
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

    handleWebSocketMessage(data) {
        console.log('Processing WebSocket message:', data);
        switch (data.type) {
            case 'status_update':
                this.updateStatusDisplay(data.data.scraping_status);
                this.updateStatsDisplay(data.data.stats);
                break;
            case 'error':
                this.showNotification(data.data.message, 'error');
                break;
            case 'notification':
                this.showNotification(data.data.message, data.data.level);
                break;
        }
    }
}

// Initialize on DOM Load
document.addEventListener('DOMContentLoaded', () => {
    new MatrixRain();
    window.dashboard = new DashboardController();
});

// End of File