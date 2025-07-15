class YouTubeSummarizer {
    constructor() {
        this.websocket = null;
        this.currentVideoData = null;
        this.isProcessing = false;
        
        this.initializeElements();
        this.bindEvents();
        this.initializeWebSocket();
        this.loadAvailableModels();
    }
    
    initializeElements() {
        // Form elements
        this.videoForm = document.getElementById('videoForm');
        this.videoUrlInput = document.getElementById('videoUrl');
        this.submitBtn = document.getElementById('submitBtn');
        this.toggleAdvancedBtn = document.getElementById('toggleAdvanced');
        this.advancedOptions = document.getElementById('advancedOptions');
        this.maxSegmentsSelect = document.getElementById('maxSegments');
        this.segmentLengthSelect = document.getElementById('segmentLength');
        this.aiModelSelect = document.getElementById('aiModel');
        this.modelInfo = document.getElementById('modelInfo');
        this.modelInfoText = document.getElementById('modelInfoText');
        
        // Progress elements
        this.progressSection = document.getElementById('progressSection');
        this.progressTitle = document.getElementById('progressTitle');
        this.progressPercent = document.getElementById('progressPercent');
        this.progressFill = document.getElementById('progressFill');
        this.progressMessage = document.getElementById('progressMessage');
        
        // Progress steps
        this.stepDownload = document.getElementById('step-download');
        this.stepAudio = document.getElementById('step-audio');
        this.stepTranscribe = document.getElementById('step-transcribe');
        this.stepAnalyze = document.getElementById('step-analyze');
        this.stepSummarize = document.getElementById('step-summarize');
        
        // Results elements
        this.resultsSection = document.getElementById('resultsSection');
        this.videoTitle = document.getElementById('videoTitle');
        this.videoDuration = document.getElementById('videoDuration');
        this.segmentCount = document.getElementById('segmentCount');
        this.overallSummary = document.getElementById('overallSummary');
        this.overallSummaryContent = document.getElementById('overallSummaryContent');
        this.mainThemes = document.getElementById('mainThemes');
        this.themesList = document.getElementById('themesList');
        this.keyTakeaways = document.getElementById('keyTakeaways');
        this.takeawaysList = document.getElementById('takeawaysList');
        this.segmentsList = document.getElementById('segmentsList');
        
        // Export elements
        this.exportTextBtn = document.getElementById('exportText');
        this.exportJsonBtn = document.getElementById('exportJson');
        
        // Error elements
        this.errorSection = document.getElementById('errorSection');
        this.errorMessage = document.getElementById('errorMessage');
        this.retryBtn = document.getElementById('retryBtn');
        
        // Loading overlay
        this.loadingOverlay = document.getElementById('loadingOverlay');
    }
    
    bindEvents() {
        // Form submission
        this.videoForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
        
        // Advanced options toggle
        this.toggleAdvancedBtn.addEventListener('click', () => this.toggleAdvancedOptions());
        
        // Export buttons
        this.exportTextBtn.addEventListener('click', () => this.exportAsText());
        this.exportJsonBtn.addEventListener('click', () => this.exportAsJson());
        
        // Retry button
        this.retryBtn.addEventListener('click', () => this.retryProcessing());
        
        // URL input validation
        this.videoUrlInput.addEventListener('input', () => this.validateUrl());
        
        // Model selection
        this.aiModelSelect.addEventListener('change', () => this.updateModelInfo());
    }
    
    initializeWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.hideLoadingOverlay();
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                if (this.isProcessing) {
                    this.showError('Connection lost. Please refresh the page and try again.');
                }
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.showError('Failed to connect to the processing service. Please check if the server is running.');
            };
            
        } catch (error) {
            console.error('Failed to initialize WebSocket:', error);
            this.showError('Failed to initialize connection. Please refresh the page.');
        }
    }
    
    handleFormSubmit(e) {
        e.preventDefault();
        
        if (this.isProcessing) {
            return;
        }
        
        const url = this.videoUrlInput.value.trim();
        if (!this.isValidYouTubeUrl(url)) {
            this.showError('Please enter a valid YouTube URL.');
            return;
        }
        
        this.startProcessing(url);
    }
    
    startProcessing(url) {
        this.isProcessing = true;
        this.currentVideoData = null;
        
        // Hide other sections and show progress
        this.hideAllSections();
        this.showProgressSection();
        
        // Disable form
        this.submitBtn.disabled = true;
        this.submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        
        // Reset progress
        this.resetProgress();
        
        // Send processing request via WebSocket
        const requestData = {
            action: 'process_video',
            url: url,
            model: this.aiModelSelect.value || 'llama3.1:8b',
            max_segments: parseInt(this.maxSegmentsSelect.value),
            segment_length: parseInt(this.segmentLengthSelect.value)
        };
        
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(requestData));
        } else {
            this.showError('Connection not available. Please refresh the page and try again.');
            this.resetForm();
        }
    }
    
    handleWebSocketMessage(data) {
        const { status, message, progress, result } = data;
        
        switch (status) {
            case 'downloading':
                this.updateProgress(progress, message);
                this.setActiveStep('download');
                break;
                
            case 'processing_audio':
                this.updateProgress(progress, message);
                this.setActiveStep('audio');
                this.setStepCompleted('download');
                break;
                
            case 'transcribing':
                this.updateProgress(progress, message);
                this.setActiveStep('transcribe');
                this.setStepCompleted('audio');
                break;
                
            case 'analyzing':
                this.updateProgress(progress, message);
                this.setActiveStep('analyze');
                this.setStepCompleted('transcribe');
                break;
                
            case 'summarizing':
                this.updateProgress(progress, message);
                this.setActiveStep('summarize');
                this.setStepCompleted('analyze');
                break;
                
            case 'completed':
                this.updateProgress(100, message);
                this.setStepCompleted('summarize');
                this.handleProcessingComplete(result);
                break;
                
            case 'error':
                this.showError(message);
                this.resetForm();
                break;
                
            default:
                console.log('Unknown status:', status);
        }
    }
    
    handleProcessingComplete(result) {
        this.currentVideoData = result;
        this.isProcessing = false;
        
        // Hide progress and show results
        setTimeout(() => {
            this.hideProgressSection();
            this.displayResults(result);
            this.resetForm();
        }, 1000);
    }
    
    displayResults(result) {
        const { video_title, video_duration, summaries, model_used } = result;
        
        // Set video info
        this.videoTitle.textContent = video_title || 'Video Summary';
        this.videoDuration.textContent = this.formatDuration(video_duration);
        this.segmentCount.textContent = `${summaries.length} key segments`;
        
        // Display model used badge
        const modelUsedElement = document.getElementById('modelUsed');
        if (modelUsedElement && model_used) {
            modelUsedElement.textContent = `Model: ${model_used}`;
        }
        
        // Display segment summaries
        this.displaySegmentSummaries(summaries);
        
        // Generate and display overall summary
        this.generateOverallSummary(summaries, video_title);
        
        // Show results section
        this.showResultsSection();
    }
    
    displaySegmentSummaries(summaries) {
        this.segmentsList.innerHTML = '';
        
        summaries.forEach((segment, index) => {
            const segmentCard = this.createSegmentCard(segment, index + 1);
            this.segmentsList.appendChild(segmentCard);
        });
    }
    
    createSegmentCard(segment, index) {
        const card = document.createElement('div');
        card.className = 'segment-card fade-in';
        
        const importanceScore = Math.round(segment.importance_score * 100);
        const confidenceScore = Math.round(segment.confidence * 100);
        
        card.innerHTML = `
            <div class="segment-header">
                <div class="segment-timestamp">${segment.timestamp}</div>
                <div class="segment-score">
                    <i class="fas fa-star"></i>
                    ${importanceScore}% importance
                </div>
            </div>
            
            <div class="segment-summary">
                ${segment.summary}
            </div>
            
            ${segment.key_points && segment.key_points.length > 0 ? `
                <div class="segment-keypoints">
                    <h5>Key Points:</h5>
                    <ul>
                        ${segment.key_points.map(point => `<li>${point}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            <div class="segment-transcript">
                <h5>Original Transcript</h5>
                <p>${segment.original_transcript}</p>
            </div>
        `;
        
        return card;
    }
    
    generateOverallSummary(summaries, videoTitle) {
        // For now, create a simple overall summary
        // In a full implementation, this could call the backend for a comprehensive summary
        
        const totalDuration = summaries.reduce((sum, segment) => sum + segment.duration, 0);
        const avgImportance = summaries.reduce((sum, segment) => sum + segment.importance_score, 0) / summaries.length;
        
        const overallText = `This ${this.formatDuration(totalDuration)} video contains ${summaries.length} key segments covering the main topics and insights. The analysis identified the most important content with an average relevance score of ${Math.round(avgImportance * 100)}%.`;
        
        this.overallSummaryContent.textContent = overallText;
        
        // Extract themes and takeaways from key points
        const allKeyPoints = summaries.flatMap(s => s.key_points || []);
        if (allKeyPoints.length > 0) {
            // Simple theme extraction (in production, this could be more sophisticated)
            const themes = this.extractThemes(allKeyPoints);
            const takeaways = allKeyPoints.slice(0, 5); // Top 5 key points as takeaways
            
            if (themes.length > 0) {
                this.displayThemes(themes);
            }
            
            if (takeaways.length > 0) {
                this.displayTakeaways(takeaways);
            }
        }
        
        this.overallSummary.style.display = 'block';
    }
    
    extractThemes(keyPoints) {
        // Simple theme extraction based on common words
        const commonWords = ['technology', 'business', 'education', 'health', 'science', 'development', 'strategy', 'innovation', 'management', 'design'];
        const themes = [];
        
        commonWords.forEach(word => {
            const relevantPoints = keyPoints.filter(point => 
                point.toLowerCase().includes(word)
            );
            
            if (relevantPoints.length > 0) {
                themes.push(word.charAt(0).toUpperCase() + word.slice(1));
            }
        });
        
        return themes.slice(0, 4); // Limit to 4 themes
    }
    
    displayThemes(themes) {
        this.themesList.innerHTML = '';
        themes.forEach(theme => {
            const li = document.createElement('li');
            li.textContent = theme;
            this.themesList.appendChild(li);
        });
        this.mainThemes.style.display = 'block';
    }
    
    displayTakeaways(takeaways) {
        this.takeawaysList.innerHTML = '';
        takeaways.forEach(takeaway => {
            const li = document.createElement('li');
            li.textContent = takeaway;
            this.takeawaysList.appendChild(li);
        });
        this.keyTakeaways.style.display = 'block';
    }
    
    // UI Helper Methods
    updateProgress(percentage, message) {
        this.progressPercent.textContent = `${percentage}%`;
        this.progressFill.style.width = `${percentage}%`;
        this.progressMessage.textContent = message;
    }
    
    resetProgress() {
        this.updateProgress(0, 'Initializing...');
        this.resetAllSteps();
    }
    
    resetAllSteps() {
        const steps = [this.stepDownload, this.stepAudio, this.stepTranscribe, this.stepAnalyze, this.stepSummarize];
        steps.forEach(step => {
            step.classList.remove('active', 'completed');
        });
    }
    
    setActiveStep(stepName) {
        this.resetAllSteps();
        const stepElement = document.getElementById(`step-${stepName}`);
        if (stepElement) {
            stepElement.classList.add('active');
        }
    }
    
    setStepCompleted(stepName) {
        const stepElement = document.getElementById(`step-${stepName}`);
        if (stepElement) {
            stepElement.classList.remove('active');
            stepElement.classList.add('completed');
        }
    }
    
    hideAllSections() {
        this.progressSection.style.display = 'none';
        this.resultsSection.style.display = 'none';
        this.errorSection.style.display = 'none';
    }
    
    showProgressSection() {
        this.hideAllSections();
        this.progressSection.style.display = 'block';
        this.progressSection.classList.add('fade-in');
    }
    
    hideProgressSection() {
        this.progressSection.style.display = 'none';
    }
    
    showResultsSection() {
        this.hideAllSections();
        this.resultsSection.style.display = 'block';
        this.resultsSection.classList.add('fade-in');
    }
    
    showError(message) {
        this.hideAllSections();
        this.errorMessage.textContent = message;
        this.errorSection.style.display = 'block';
        this.errorSection.classList.add('fade-in');
        this.isProcessing = false;
    }
    
    showLoadingOverlay() {
        this.loadingOverlay.style.display = 'flex';
    }
    
    hideLoadingOverlay() {
        this.loadingOverlay.style.display = 'none';
    }
    
    resetForm() {
        this.isProcessing = false;
        this.submitBtn.disabled = false;
        this.submitBtn.innerHTML = '<i class="fas fa-play"></i> Analyze Video';
    }
    
    toggleAdvancedOptions() {
        this.advancedOptions.classList.toggle('show');
        const icon = this.toggleAdvancedBtn.querySelector('i');
        
        if (this.advancedOptions.classList.contains('show')) {
            icon.className = 'fas fa-chevron-up';
        } else {
            icon.className = 'fas fa-cog';
        }
    }
    
    validateUrl() {
        const url = this.videoUrlInput.value.trim();
        const isValid = this.isValidYouTubeUrl(url);
        
        if (url && !isValid) {
            this.videoUrlInput.style.borderColor = '#dc3545';
        } else {
            this.videoUrlInput.style.borderColor = '#e1e8ed';
        }
        
        return isValid;
    }
    
    isValidYouTubeUrl(url) {
        const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)\/(watch\?v=|embed\/|v\/|.+\?v=)?([^&=%\?]{11})/;
        return youtubeRegex.test(url);
    }
    
    formatDuration(seconds) {
        if (!seconds) return '0:00';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    }
    
    retryProcessing() {
        if (this.videoUrlInput.value.trim()) {
            this.startProcessing(this.videoUrlInput.value.trim());
        } else {
            this.hideAllSections();
        }
    }
    
    // Model Management
    async loadAvailableModels() {
        try {
            this.modelInfo.classList.add('loading');
            this.modelInfoText.textContent = 'Loading available models...';
            
            const response = await fetch('/api/models');
            const data = await response.json();
            
            if (response.ok) {
                this.populateModelDropdown(data.models);
                this.modelInfo.classList.remove('loading');
                this.updateModelInfo();
            } else {
                throw new Error(data.detail || 'Failed to load models');
            }
        } catch (error) {
            console.error('Error loading models:', error);
            this.modelInfo.classList.remove('loading');
            this.modelInfo.classList.add('error');
            this.modelInfoText.textContent = 'Error loading models. Please check if Ollama is running.';
            
            // Add default model as fallback
            this.aiModelSelect.innerHTML = '<option value="llama3.1:8b">llama3.1:8b (Default)</option>';
        }
    }
    
    populateModelDropdown(models) {
        this.aiModelSelect.innerHTML = '';
        
        if (models.length === 0) {
            this.aiModelSelect.innerHTML = '<option value="">No models available</option>';
            return;
        }
        
        models.forEach((model, index) => {
            const option = document.createElement('option');
            option.value = model.name;
            option.textContent = model.display_name;
            option.dataset.size = model.size;
            option.dataset.modified = model.modified;
            
            // Select the first model by default
            if (index === 0) {
                option.selected = true;
            }
            
            this.aiModelSelect.appendChild(option);
        });
    }
    
    updateModelInfo() {
        const selectedOption = this.aiModelSelect.selectedOptions[0];
        
        if (!selectedOption || !selectedOption.value) {
            this.modelInfoText.textContent = 'No model selected';
            return;
        }
        
        const modelName = selectedOption.value;
        const modelSize = selectedOption.dataset.size || 'Unknown size';
        const modelModified = selectedOption.dataset.modified || '';
        
        let infoText = `Model: ${modelName} | Size: ${modelSize}`;
        if (modelModified) {
            infoText += ` | Modified: ${modelModified}`;
        }
        
        this.modelInfoText.textContent = infoText;
        this.modelInfo.classList.remove('error', 'loading');
    }
    
    // Export Functions
    exportAsText() {
        if (!this.currentVideoData) {
            alert('No data to export');
            return;
        }
        
        const { video_title, video_duration, summaries } = this.currentVideoData;
        let textContent = `YouTube Video Summary\n`;
        textContent += `========================\n\n`;
        textContent += `Title: ${video_title}\n`;
        textContent += `Duration: ${this.formatDuration(video_duration)}\n`;
        textContent += `Key Segments: ${summaries.length}\n\n`;
        
        textContent += `SEGMENT SUMMARIES\n`;
        textContent += `=================\n\n`;
        
        summaries.forEach((segment, index) => {
            textContent += `${index + 1}. ${segment.timestamp}\n`;
            textContent += `Summary: ${segment.summary}\n`;
            
            if (segment.key_points && segment.key_points.length > 0) {
                textContent += `Key Points:\n`;
                segment.key_points.forEach(point => {
                    textContent += `  • ${point}\n`;
                });
            }
            
            textContent += `\nOriginal Transcript:\n"${segment.original_transcript}"\n\n`;
            textContent += `${'='.repeat(50)}\n\n`;
        });
        
        this.downloadFile(textContent, `${video_title || 'video'}_summary.txt`, 'text/plain');
    }
    
    exportAsJson() {
        if (!this.currentVideoData) {
            alert('No data to export');
            return;
        }
        
        const jsonContent = JSON.stringify(this.currentVideoData, null, 2);
        const fileName = `${this.currentVideoData.video_title || 'video'}_summary.json`;
        this.downloadFile(jsonContent, fileName, 'application/json');
    }
    
    downloadFile(content, fileName, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new YouTubeSummarizer();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        console.log('Page hidden');
    } else {
        console.log('Page visible');
    }
});
