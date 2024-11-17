// static/js/utils.js
const MatrixUtils = {
    // Formatierung & Konvertierung
    format: {
        bytes: (bytes) => {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },

        duration: (seconds) => {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const remainingSeconds = Math.floor(seconds % 60);
            return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
        },

        number: (number, decimals = 2) => {
            return new Intl.NumberFormat('de-DE', {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            }).format(number);
        },

        currency: (amount) => {
            return new Intl.NumberFormat('de-DE', {
                style: 'currency',
                currency: 'EUR'
            }).format(amount);
        },

        percentage: (value, total) => {
            return ((value / total) * 100).toFixed(1) + '%';
        }
    },

    // DOM Manipulation
    dom: {
        create: (tag, classes = [], attributes = {}) => {
            const element = document.createElement(tag);
            classes.forEach(cls => element.classList.add(cls));
            Object.entries(attributes).forEach(([key, value]) => {
                element.setAttribute(key, value);
            });
            return element;
        },

        getById: (id) => document.getElementById(id),

        query: (selector) => document.querySelector(selector),

        queryAll: (selector) => document.querySelectorAll(selector),

        addClass: (element, ...classes) => {
            element.classList.add(...classes);
            return element;
        },

        removeClass: (element, ...classes) => {
            element.classList.remove(...classes);
            return element;
        },

        toggleClass: (element, className) => {
            element.classList.toggle(className);
            return element;
        }
    },

    // Animation Utilities
    animation: {
        typeWriter: (element, text, speed = 50) => {
            return new Promise((resolve) => {
                let i = 0;
                element.textContent = '';
                const type = () => {
                    if (i < text.length) {
                        element.textContent += text.charAt(i);
                        i++;
                        setTimeout(type, speed);
                    } else {
                        resolve();
                    }
                };
                type();
            });
        },

        glitchText: (element, duration = 1000) => {
            const original = element.textContent;
            const glitchChars = '!@#$%^&*()_+-=[]{}|;:,.<>?';
            
            let intervals = [];
            for (let i = 0; i < 10; i++) {
                intervals.push(setTimeout(() => {
                    element.textContent = original.split('').map(char => 
                        Math.random() > 0.5 ? glitchChars[Math.floor(Math.random() * glitchChars.length)] : char
                    ).join('');
                }, i * (duration / 10)));
            }
            
            setTimeout(() => {
                intervals.forEach(clearTimeout);
                element.textContent = original;
            }, duration);
        },

        fadeIn: (element, duration = 300) => {
            element.style.opacity = '0';
            element.style.display = 'block';
            
            let start = null;
            const animate = (timestamp) => {
                if (!start) start = timestamp;
                const progress = timestamp - start;
                
                element.style.opacity = Math.min(progress / duration, 1);
                
                if (progress < duration) {
                    requestAnimationFrame(animate);
                }
            };
            
            requestAnimationFrame(animate);
        },

        fadeOut: (element, duration = 300) => {
            return new Promise(resolve => {
                let start = null;
                const animate = (timestamp) => {
                    if (!start) start = timestamp;
                    const progress = timestamp - start;
                    
                    element.style.opacity = Math.max(1 - (progress / duration), 0);
                    
                    if (progress < duration) {
                        requestAnimationFrame(animate);
                    } else {
                        element.style.display = 'none';
                        resolve();
                    }
                };
                
                requestAnimationFrame(animate);
            });
        }
    },

    // Matrix-spezifische Effekte
    matrix: {
        randomChar: () => {
            const chars = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン";
            return chars[Math.floor(Math.random() * chars.length)];
        },

        createRainDrop: (canvas, x, speed) => {
            const ctx = canvas.getContext('2d');
            let y = 0;
            
            return {
                update: () => {
                    y += speed;
                    if (y > canvas.height) {
                        y = 0;
                    }
                    ctx.fillStyle = '#0F0';
                    ctx.fillText(MatrixUtils.matrix.randomChar(), x, y);
                }
            };
        }
    },

    // LocalStorage Wrapper
    storage: {
        set: (key, value) => {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (e) {
                console.error('Storage error:', e);
                return false;
            }
        },

        get: (key, defaultValue = null) => {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (e) {
                console.error('Storage error:', e);
                return defaultValue;
            }
        },

        remove: (key) => localStorage.removeItem(key),
        
        clear: () => localStorage.clear()
    },

    // Debug & Logging
    debug: {
        log: (message, type = 'info') => {
            const timestamp = new Date().toISOString();
            const formattedMessage = `[${timestamp}] [${type.toUpperCase()}] ${message}`;
            
            console.log(formattedMessage);
            
            // Füge Log zum Matrix-Console hinzu, wenn vorhanden
            const consoleElement = document.getElementById('matrixConsole');
            if (consoleElement) {
                const entry = document.createElement('div');
                entry.className = `console-entry ${type}`;
                entry.textContent = formattedMessage;
                consoleElement.insertBefore(entry, consoleElement.firstChild);
                
                // Begrenze die Anzahl der Log-Einträge
                while (consoleElement.children.length > 100) {
                    consoleElement.removeChild(consoleElement.lastChild);
                }
            }
        },
        
        error: (message) => MatrixUtils.debug.log(message, 'error'),
        warn: (message) => MatrixUtils.debug.log(message, 'warning'),
        success: (message) => MatrixUtils.debug.log(message, 'success'),

        measure: async (fn, label) => {
            console.time(label);
            const result = await fn();
            console.timeEnd(label);
            return result;
        }
    },

    // Performance Monitoring
    performance: {
        startTime: null,
        marks: new Map(),

        start: (label) => {
            MatrixUtils.performance.marks.set(label, performance.now());
        },

        end: (label) => {
            const startTime = MatrixUtils.performance.marks.get(label);
            if (startTime) {
                const duration = performance.now() - startTime;
                MatrixUtils.performance.marks.delete(label);
                return duration;
            }
            return null;
        },

        measureMemory: async () => {
            if ('memory' in performance) {
                return {
                    usedJSHeapSize: performance.memory.usedJSHeapSize,
                    totalJSHeapSize: performance.memory.totalJSHeapSize,
                    jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
                };
            }
            return null;
        }
    },

    // Health Check Utilities
    health: {
        checkConnection: async () => {
            try {
                const response = await fetch('/api/health');
                return response.ok;
            } catch {
                return false;
            }
        },

        checkLocalStorage: () => {
            try {
                localStorage.setItem('test', 'test');
                localStorage.removeItem('test');
                return true;
            } catch {
                return false;
            }
        },

        checkWebGL: () => {
            const canvas = document.createElement('canvas');
            return !!(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'));
        }
    }
};

export default MatrixUtils;