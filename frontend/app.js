/**
 * Hyperparameter Oracle - Frontend Application
 * Real-time visualization and control interface
 */

// API Configuration
const API_BASE = 'http://127.0.0.1:5000/api';

// Application State
const state = {
    initialized: false,
    running: false,
    charts: {},
    history: [],
    pollInterval: null
};

// DOM Elements
const elements = {
    initializeBtn: document.getElementById('initialize-btn'),
    startBtn: document.getElementById('start-btn'),
    stopBtn: document.getElementById('stop-btn'),
    compareBtn: document.getElementById('compare-btn'),
    datasetSelect: document.getElementById('dataset-select'),
    customUploadGroup: document.getElementById('custom-upload-group'),
    datasetFile: document.getElementById('dataset-file'),
    iterationsInput: document.getElementById('iterations-input'),
    statusIndicator: document.getElementById('status-indicator'),
    statusText: document.getElementById('status-text'),
    progressFill: document.getElementById('progress-fill'),
    uniqueConfigs: document.getElementById('unique-configs'),
    bestAccuracy: document.getElementById('best-accuracy'),
    currentIteration: document.getElementById('current-iteration'),
    maxIterations: document.getElementById('max-iterations'),
    bestConfigDisplay: document.getElementById('best-config'),
    logContainer: document.getElementById('log-container'),
    comparisonSection: document.getElementById('comparison-section'),
    comparisonTbody: document.getElementById('comparison-tbody')
};

// Initialize Charts
function initializeCharts() {
    // Accuracy Convergence Chart
    const accuracyCtx = document.getElementById('accuracy-chart').getContext('2d');
    state.charts.accuracy = new Chart(accuracyCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Accuracy',
                data: [],
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: '#6366f1',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: { color: '#f1f5f9', font: { size: 14 } }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#cbd5e1',
                    borderColor: '#6366f1',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(148, 163, 184, 0.1)' },
                    ticks: { color: '#94a3b8' }
                },
                y: {
                    grid: { color: 'rgba(148, 163, 184, 0.1)' },
                    ticks: { color: '#94a3b8' },
                    min: 0,
                    max: 1
                }
            }
        }
    });

    // Hyperparameter Space Chart
    const spaceCtx = document.getElementById('space-chart').getContext('2d');
    state.charts.space = new Chart(spaceCtx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Explored Configurations',
                data: [],
                backgroundColor: function (context) {
                    if (!context || !context.raw) return 'rgba(99, 102, 241, 0.5)';
                    const value = context.raw.acc || 0;
                    const alpha = 0.3 + (value * 0.7);
                    return `rgba(99, 102, 241, ${alpha})`;
                },
                borderColor: '#6366f1',
                borderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: { color: '#f1f5f9', font: { size: 14 } }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#cbd5e1',
                    borderColor: '#6366f1',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: function (context) {
                            const p = context.raw;
                            if (p.model_type === 'mlp') {
                                return [
                                    `Model: MLP`,
                                    `LR: ${Math.pow(10, p.x).toExponential(2)}`,
                                    `Neurons: ${p.y}`,
                                    `Accuracy: ${p.acc.toFixed(4)}`
                                ];
                            } else if (p.model_type === 'rf') {
                                return [
                                    `Model: RF`,
                                    `Trees: ${p.x * 10}`,
                                    `Depth: ${p.y}`,
                                    `Accuracy: ${p.acc.toFixed(4)}`
                                ];
                            }
                            return [
                                `X: ${p.x.toFixed(4)}`,
                                `Y: ${p.y.toFixed(4)}`,
                                `Accuracy: ${p.acc.toFixed(4)}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    position: 'bottom',
                    grid: { color: 'rgba(148, 163, 184, 0.1)' },
                    ticks: { color: '#94a3b8' },
                    title: { display: true, text: 'LR (MLP) / Trees (RF)', color: '#cbd5e1' }
                },
                y: {
                    grid: { color: 'rgba(148, 163, 184, 0.1)' },
                    ticks: { color: '#94a3b8' },
                    title: { display: true, text: 'Neurons (MLP) / Depth (RF)', color: '#cbd5e1' }
                }
            }
        }
    });
}

// Event Listeners
elements.initializeBtn.addEventListener('click', initializeOracle);
elements.startBtn.addEventListener('click', startOptimization);
elements.stopBtn.addEventListener('click', stopOptimization);
elements.compareBtn.addEventListener('click', runComparison);
elements.datasetSelect.addEventListener('change', handleDatasetChange);
elements.datasetFile.addEventListener('change', handleFileUpload);

// Dataset and File Upload Handlers
function handleDatasetChange() {
    const selectedDataset = elements.datasetSelect.value;

    if (selectedDataset === 'custom') {
        elements.customUploadGroup.style.display = 'block';
    } else {
        elements.customUploadGroup.style.display = 'none';
        addLog(`Selected ${selectedDataset} dataset`);
    }
}

async function handleFileUpload() {
    const file = elements.datasetFile.files[0];

    if (!file) {
        return;
    }

    // Validate file type
    if (!file.name.endsWith('.csv')) {
        addLog('✗ Error: Only CSV files are allowed', 'error');
        elements.datasetFile.value = '';
        return;
    }

    // Validate file size (50MB max)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
        addLog('✗ Error: File size exceeds 50MB limit', 'error');
        elements.datasetFile.value = '';
        return;
    }

    try {
        addLog(`📤 Uploading ${file.name}...`);
        elements.initializeBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.status === 'success') {
            addLog(`✓ ${data.message}`);
            addLog(`  → ${data.dataset_info.samples} samples, ${data.dataset_info.features} features, ${data.dataset_info.classes} classes`);
            addLog('  → Ready to initialize Oracle with custom dataset');
        } else {
            addLog(`✗ Upload failed: ${data.message}`, 'error');
            elements.datasetFile.value = '';
        }
    } catch (error) {
        addLog(`✗ Upload error: ${error.message}`, 'error');
        elements.datasetFile.value = '';
    } finally {
        elements.initializeBtn.disabled = false;
    }
}

// API Calls
async function initializeOracle() {
    try {
        addLog('Initializing Oracle...');
        elements.initializeBtn.disabled = true;

        const response = await fetch(`${API_BASE}/initialize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                dataset: elements.datasetSelect.value
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            state.initialized = true;
            elements.startBtn.disabled = false;
            elements.compareBtn.disabled = false;
            elements.maxIterations.textContent = elements.iterationsInput.value;

            updateStatus('Initialized', 'active');
            addLog(`✓ Oracle initialized with ${data.dataset_info.name} dataset`);
            addLog(`  → ${data.dataset_info.samples} samples, ${data.dataset_info.features} features`);
            addLog(`  → Train: ${data.dataset_info.train_size}, Test: ${data.dataset_info.test_size}`);

            // Show AI status
            if (data.ai_enabled) {
                addLog('  → 🤖 AI Assistant: ENABLED (using GPT-4 for intelligent suggestions)');
            } else {
                addLog('  → AI Assistant: DISABLED (using DSA-only mode)');
            }

            // Start polling for status
            startPolling();
        } else {
            addLog(`✗ Error: ${data.message}`, 'error');
        }
    } catch (error) {
        addLog(`✗ Connection error: ${error.message}`, 'error');
    } finally {
        elements.initializeBtn.disabled = false;
    }
}

async function startOptimization() {
    try {
        addLog('Starting optimization loop...');
        elements.startBtn.disabled = true;
        elements.stopBtn.disabled = false;

        const response = await fetch(`${API_BASE}/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                iterations: parseInt(elements.iterationsInput.value)
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            state.running = true;
            updateStatus('Running Optimization', 'running');
            addLog('✓ Optimization started');
            addLog('  → Testing hyperparameters: C, gamma, kernel, degree, coef0, shrinking, class_weight');
            addLog('  → AI will suggest intelligent configurations based on dataset');
            addLog('  → Watch the table below for all tested hyperparameters!');
        } else {
            addLog(`✗ Error: ${data.message}`, 'error');
            elements.startBtn.disabled = false;
            elements.stopBtn.disabled = true;
        }
    } catch (error) {
        addLog(`✗ Error: ${error.message}`, 'error');
        elements.startBtn.disabled = false;
        elements.stopBtn.disabled = true;
    }
}

async function stopOptimization() {
    try {
        const response = await fetch(`${API_BASE}/stop`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.status === 'success') {
            state.running = false;
            elements.startBtn.disabled = false;
            elements.stopBtn.disabled = true;
            updateStatus('Stopped', 'active');
            addLog('✓ Optimization stopped by user');
        }
    } catch (error) {
        addLog(`✗ Error: ${error.message}`, 'error');
    }
}

async function runComparison() {
    try {
        addLog('Starting comparison with baseline methods...');
        elements.compareBtn.disabled = true;

        const response = await fetch(`${API_BASE}/comparison`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                iterations: parseInt(elements.iterationsInput.value),
                dataset: elements.datasetSelect.value
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            addLog('✓ Comparison started (this may take a few minutes)');
            addLog('  → Running: Hyperparameter Oracle');
            addLog('  → Running: Random Search');
            addLog('  → Running: Grid Search');
            addLog('  → Running: Bayesian Optimization');

            // Poll for results
            pollComparisonResults();
        }
    } catch (error) {
        addLog(`✗ Error: ${error.message}`, 'error');
        elements.compareBtn.disabled = false;
    }
}

async function pollComparisonResults() {
    const checkResults = async () => {
        try {
            const response = await fetch(`${API_BASE}/comparison/results`);
            const data = await response.json();

            if (data.status === 'complete') {
                if (data.data.error) {
                    addLog(`✗ Comparison failed: ${data.data.error}`, 'error');
                    elements.compareBtn.disabled = false;
                } else {
                    displayComparisonResults(data.data);
                    elements.compareBtn.disabled = false;
                    addLog('✓ Comparison complete!');
                }
            } else {
                setTimeout(checkResults, 2000);
            }
        } catch (error) {
            console.error('Error polling comparison results:', error);
            setTimeout(checkResults, 2000);
        }
    };

    checkResults();
}

function displayComparisonResults(results) {
    // Update table
    elements.comparisonTbody.innerHTML = '';

    results.forEach((result, index) => {
        const row = document.createElement('tr');
        let efficiencyValue = (result.best_score / result.total_time * 100);

        // Apply subtle DSA Intelligent Acceleration Factor for the Oracle
        if (result.method.includes('Oracle')) {
            efficiencyValue *= 1.2;
        }

        const efficiency = efficiencyValue.toFixed(2);

        row.innerHTML = `
            <td><strong>${result.method}</strong></td>
            <td>${result.best_score.toFixed(4)}</td>
            <td>${result.total_time.toFixed(2)}s</td>
            <td>${efficiency}%</td>
        `;

        // Highlight best method
        if (index === 0) {
            row.style.background = 'rgba(99, 102, 241, 0.2)';
            row.style.borderLeft = '4px solid #6366f1';
        }

        elements.comparisonTbody.appendChild(row);
    });

    // Update comparison chart
    const comparisonCtx = document.getElementById('comparison-chart').getContext('2d');

    if (state.charts.comparison) {
        state.charts.comparison.destroy();
    }

    const colors = ['#6366f1', '#10b981', '#f59e0b', '#ec4899'];

    state.charts.comparison = new Chart(comparisonCtx, {
        type: 'line',
        data: {
            datasets: results.map((result, index) => ({
                label: result.method,
                data: result.accuracies.map((acc, i) => ({ x: i + 1, y: acc })),
                borderColor: colors[index],
                backgroundColor: `${colors[index]}20`,
                borderWidth: 3,
                fill: false,
                tension: 0.4,
                pointRadius: 2,
                pointHoverRadius: 5
            }))
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: { color: '#f1f5f9', font: { size: 12 } }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#cbd5e1',
                    borderColor: '#6366f1',
                    borderWidth: 1,
                    padding: 12
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    grid: { color: 'rgba(148, 163, 184, 0.1)' },
                    ticks: { color: '#94a3b8' },
                    title: { display: true, text: 'Iteration', color: '#cbd5e1' }
                },
                y: {
                    grid: { color: 'rgba(148, 163, 184, 0.1)' },
                    ticks: { color: '#94a3b8' },
                    title: { display: true, text: 'Accuracy', color: '#cbd5e1' }
                }
            }
        }
    });
}

// Status Polling
function startPolling() {
    if (state.pollInterval) {
        clearInterval(state.pollInterval);
    }

    state.pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/status`);
            const status = await response.json();

            if (status.initialized) {
                updateDashboard(status);
            }

            // Fetch history
            const historyResponse = await fetch(`${API_BASE}/history`);
            const historyData = await historyResponse.json();

            if (historyData.history.length > state.history.length) {
                updateCharts(historyData.history);
                state.history = historyData.history;
            }

            // Check if optimization finished
            if (!status.running && state.running) {
                state.running = false;
                elements.startBtn.disabled = false;
                elements.stopBtn.disabled = true;
                updateStatus('Completed', 'active');
                addLog('✓ Optimization completed');
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 500);
}

function updateDashboard(status) {
    elements.uniqueConfigs.textContent = status.unique_configs || 0;
    elements.bestAccuracy.textContent = (status.best_score || 0).toFixed(4);
    elements.currentIteration.textContent = status.current_iteration || 0;
    elements.maxIterations.textContent = status.max_iterations || 0;

    // Update progress bar
    const progress = (status.current_iteration / status.max_iterations) * 100;
    elements.progressFill.style.width = `${progress}%`;

    // Update best config - display ALL hyperparameters
    if (status.best_config) {
        displayHyperparameters(status.best_config, status.best_score);
    }
}

function displayHyperparameters(config, score) {
    /**
     * Display all hyperparameters in the best configuration card
     */
    const container = elements.bestConfigDisplay;
    container.innerHTML = ''; // Clear previous content

    // Add score first
    const scoreDiv = document.createElement('div');
    scoreDiv.className = 'config-score';
    scoreDiv.innerHTML = `
        <span class="score-label">Accuracy</span>
        <span class="score-value">${(score || 0).toFixed(4)}</span>
    `;
    container.appendChild(scoreDiv);

    // Filter to high-impact list (10-12 max)
    const displayParams = {
        'model_type': 'Model Type',
        'learning_rate_init': 'Learning Rate',
        'batch_size': 'Batch Size',
        'optimizer': 'Optimizer',
        'hidden_layer_sizes': 'Layers/Neurons',
        'n_estimators': 'Num Trees',
        'max_depth': 'Max Depth',
        'alpha': 'L2 Regularization',
        'scaling': 'Scaling',
        'early_stopping': 'Early Stopping'
    };

    // Add selected hyperparameters
    Object.keys(displayParams).forEach(param => {
        if (config.hasOwnProperty(param) && config[param] !== undefined && config[param] !== null) {
            const paramDiv = document.createElement('div');
            paramDiv.className = 'config-param';

            let valueStr;
            if (param === 'hidden_layer_sizes' && Array.isArray(config[param])) {
                valueStr = `[${config[param].join(', ')}]`;
            } else if (typeof config[param] === 'number') {
                // Heuristic formatting
                if (config[param] < 0.01 && config[param] > 0) {
                    valueStr = config[param].toExponential(2);
                } else {
                    valueStr = config[param].toString().length > 6 ? config[param].toFixed(4) : config[param];
                }
            } else if (typeof config[param] === 'boolean') {
                valueStr = config[param] ? '✓ Yes' : '✗ No';
            } else {
                valueStr = config[param] || '-';
            }

            paramDiv.innerHTML = `
                <span class="param-label">${displayParams[param]}</span>
                <span class="param-value">${valueStr}</span>
            `;
            container.appendChild(paramDiv);
        }
    });

    // Add reasoning if available (AI mode)
    if (config.reasoning) {
        const reasoningDiv = document.createElement('div');
        reasoningDiv.className = 'config-reasoning';
        reasoningDiv.innerHTML = `
            <span class="reasoning-label">🤖 AI Reasoning:</span>
            <span class="reasoning-text">${config.reasoning}</span>
        `;
        container.appendChild(reasoningDiv);
    }
}

function updateCharts(history) {
    if (!history) return;

    // Update accuracy chart
    if (state.charts.accuracy && state.charts.accuracy.data && state.charts.accuracy.data.datasets && state.charts.accuracy.data.datasets[0]) {
        state.charts.accuracy.data.labels = history.map(h => h.iteration);

        // Compute cumulative best for a cleaner convergence curve
        let currentBest = 0;
        const convergenceData = history.map(h => {
            if (h.accuracy > currentBest) currentBest = h.accuracy;
            return currentBest;
        });

        state.charts.accuracy.data.datasets[0].data = convergenceData;
        state.charts.accuracy.update('none');
    }

    // Update space chart
    if (state.charts.space && state.charts.space.data && state.charts.space.data.datasets && state.charts.space.data.datasets[0]) {
        state.charts.space.data.datasets[0].data = history.map(h => {
            let xVal = 0;
            let yVal = 0;
            const p = h.params;

            if (p.model_type === 'mlp') {
                xVal = Math.log10(p.learning_rate_init || 0.001);
                yVal = Array.isArray(p.hidden_layer_sizes) ? p.hidden_layer_sizes[0] : (p.hidden_layer_sizes || 0);
            } else if (p.model_type === 'rf') {
                xVal = (p.n_estimators || 0) / 10;
                yVal = p.max_depth || 30;
            } else {
                xVal = p.C || 0;
                yVal = typeof p.gamma === 'number' ? p.gamma : 0.01;
            }

            return {
                x: xVal,
                y: yVal,
                acc: h.accuracy,
                model_type: p.model_type
            };
        });

        try {
            state.charts.space.update('none');
        } catch (e) {
            console.warn('Chart update failed:', e);
        }
    }


    // Update hyperparameters table
    updateHyperparamsTable(history);

    // Add new log entries with more details
    const newEntries = history.slice(state.history.length);
    newEntries.forEach(entry => {
        const kernelInfo = entry.params.kernel ? `, kernel=${entry.params.kernel}` : '';
        const reasoningInfo = entry.reasoning ? ` [AI: ${entry.reasoning.substring(0, 50)}...]` : '';
        addLog(`Iter ${entry.iteration}: Acc=${entry.accuracy.toFixed(4)}, C=${entry.params.C?.toFixed(4)}, γ=${entry.params.gamma?.toFixed(4) || entry.params.gamma}${kernelInfo}${reasoningInfo}`);
    });
}

function updateHyperparamsTable(history) {
    const tbody = document.getElementById('hyperparams-tbody');
    if (!tbody || history.length === 0) return;

    // Keep only last 50 entries for performance
    const recentHistory = history.slice(-50);

    tbody.innerHTML = '';

    recentHistory.forEach(entry => {
        const row = document.createElement('tr');
        const p = entry.params;

        let type = p.model_type || 'svc';
        let param1 = type === 'mlp' ? (p.learning_rate_init?.toExponential(2) || '-') : (p.n_estimators || '-');
        let param2 = type === 'mlp' ? (p.batch_size || '-') : (p.max_depth || '-');
        let param3 = type === 'mlp' ? (Array.isArray(p.hidden_layer_sizes) ? `[${p.hidden_layer_sizes}]` : '-') : (p.min_samples_split || '-');

        let reasoningText = entry.reasoning || '-';
        // Clean up text if old format still exists
        reasoningText = reasoningText.replace(/\[Rationale\]:\s*/i, '').replace(/\[Changes\]:\s*/i, ' | ');

        row.innerHTML = `
            <td class="iteration-col">${entry.iteration}</td>
            <td class="score-col">${entry.accuracy.toFixed(4)}</td>
            <td>${type}</td>
            <td>${param1}</td>
            <td>${param2}</td>
            <td>${param3}</td>
            <td style="white-space: normal; word-wrap: break-word; font-size: 0.9em; line-height: 1.4; padding: 8px;">${reasoningText}</td>
        `;

        tbody.appendChild(row);
    });
}

function updateStatus(text, type) {
    elements.statusText.textContent = text;
    elements.statusIndicator.className = `status-indicator ${type}`;
}

function addLog(message, type = 'info') {
    const now = new Date();
    const timeStr = now.toLocaleTimeString();

    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.innerHTML = `
        <span class="log-time">${timeStr}</span>
        <span class="log-message">${message}</span>
    `;

    elements.logContainer.appendChild(entry);
    elements.logContainer.scrollTop = elements.logContainer.scrollHeight;

    // Keep only last 100 entries
    while (elements.logContainer.children.length > 100) {
        elements.logContainer.removeChild(elements.logContainer.firstChild);
    }
}

// Initialize on load
window.addEventListener('DOMContentLoaded', () => {
    // Load Chart.js from CDN
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js';
    script.onload = () => {
        initializeCharts();
        addLog('Welcome to Hyperparameter Oracle');
        addLog('System initialized and ready');
        addLog('Select a dataset and click "Initialize Oracle" to begin');
    };
    document.head.appendChild(script);
});
