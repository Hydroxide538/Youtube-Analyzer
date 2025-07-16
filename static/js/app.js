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
        this.videoTypeSelect = document.getElementById('videoType');
        this.videoUrlInput = document.getElementById('videoUrl');
        this.videoUrlLabel = document.getElementById('videoUrlLabel');
        this.submitBtn = document.getElementById('submitBtn');
        this.toggleAdvancedBtn = document.getElementById('toggleAdvanced');
        this.advancedOptions = document.getElementById('advancedOptions');
        this.maxSegmentsSelect = document.getElementById('maxSegments');
        this.segmentLengthSelect = document.getElementById('segmentLength');
        this.aiModelSelect = document.getElementById('aiModel');
        this.modelInfo = document.getElementById('modelInfo');
        this.modelInfoText = document.getElementById('modelInfoText');
        
        // API Key elements
        this.openaiApiKeyInput = document.getElementById('openaiApiKey');
        this.anthropicApiKeyInput = document.getElementById('anthropicApiKey');
        this.testApiKeysBtn = document.getElementById('testApiKeysBtn');
        this.refreshModelsBtn = document.getElementById('refreshModelsBtn');
        this.openaiStatus = document.getElementById('openaiStatus');
        this.anthropicStatus = document.getElementById('anthropicStatus');
        
        // Provider status elements
        this.ollamaProviderStatus = document.getElementById('ollamaProviderStatus');
        this.openaiProviderStatus = document.getElementById('openaiProviderStatus');
        this.anthropicProviderStatus = document.getElementById('anthropicProviderStatus');
        
        // Authentication elements
        this.authSection = document.getElementById('authSection');
        this.usernameInput = document.getElementById('username');
        this.passwordInput = document.getElementById('password');
        
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
        
        // Video type selection
        this.videoTypeSelect.addEventListener('change', () => this.handleVideoTypeChange());
        
        // API key input listeners
        this.openaiApiKeyInput.addEventListener('input', () => this.validateApiKey('openai'));
        this.anthropicApiKeyInput.addEventListener('input', () => this.validateApiKey('anthropic'));
        
        // API key buttons
        this.testApiKeysBtn.addEventListener('click', () => this.testApiKeys());
        this.refreshModelsBtn.addEventListener('click', () => this.refreshModels());
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
        const videoType = this.videoTypeSelect.value;
        
        if (!this.isValidUrl(url, videoType)) {
            this.showError('Please enter a valid video URL.');
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
            segment_length: parseInt(this.segmentLengthSelect.value),
            video_type: this.videoTypeSelect.value,
            username: this.usernameInput.value.trim() || null,
            password: this.passwordInput.value.trim() || null
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
                
            case 'overall_summary':
                this.updateProgress(progress, message);
                // Keep summarize step active during overall summary generation
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
        const { video_title, video_duration, summaries, overall_summary, model_used } = result;
        
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
        
        // Display enhanced overall summary from backend
        if (overall_summary) {
            this.displayEnhancedOverallSummary(overall_summary);
        } else {
            // Fallback to simple summary generation
            this.generateOverallSummary(summaries, video_title);
        }
        
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
    
    displayEnhancedOverallSummary(overallSummary) {
        // Display the enhanced overall summary from the backend
        const { overall_summary, main_themes, key_takeaways } = overallSummary;
        
        // Display the main overall summary
        if (overall_summary) {
            this.overallSummaryContent.textContent = overall_summary;
        }
        
        // Display themes from backend
        if (main_themes && main_themes.length > 0) {
            this.displayThemes(main_themes);
        }
        
        // Display takeaways from backend
        if (key_takeaways && key_takeaways.length > 0) {
            this.displayTakeaways(key_takeaways);
        }
        
        this.overallSummary.style.display = 'block';
    }
    
    generateOverallSummary(summaries, videoTitle) {
        // Fallback method for when backend overall summary is not available
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
        const videoType = this.videoTypeSelect.value;
        const isValid = this.isValidUrl(url, videoType);
        
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
                
                // Update provider status from response
                if (data.providers) {
                    this.updateProviderStatusFromResponse(data.providers);
                }
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
            
            // Set all providers as unavailable
            this.updateProviderStatus(this.ollamaProviderStatus, 'unavailable', 'Ollama: Unavailable');
            this.updateProviderStatus(this.openaiProviderStatus, 'not-configured', 'OpenAI: Not configured');
            this.updateProviderStatus(this.anthropicProviderStatus, 'not-configured', 'Anthropic: Not configured');
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
    
    // Video Type Management
    handleVideoTypeChange() {
        const videoType = this.videoTypeSelect.value;
        
        // Update UI based on video type
        if (videoType === 'conference') {
            this.authSection.style.display = 'block';
            this.videoUrlLabel.textContent = 'Conference Video URL';
            this.videoUrlInput.placeholder = 'Enter conference video URL (e.g., Zoom, Teams, etc.)';
        } else if (videoType === 'youtube') {
            this.authSection.style.display = 'none';
            this.videoUrlLabel.textContent = 'YouTube Video URL';
            this.videoUrlInput.placeholder = 'https://www.youtube.com/watch?v=...';
        } else {
            this.authSection.style.display = 'none';
            this.videoUrlLabel.textContent = 'Video URL';
            this.videoUrlInput.placeholder = 'https://www.youtube.com/watch?v=... or conference URL';
        }
        
        // Clear validation styling
        this.videoUrlInput.style.borderColor = '#e1e8ed';
        
        // Re-validate current URL
        this.validateUrl();
    }
    
    isValidUrl(url, videoType) {
        if (!url) return false;
        
        switch (videoType) {
            case 'youtube':
                return this.isValidYouTubeUrl(url);
            case 'conference':
                return this.isValidConferenceUrl(url);
            case 'auto':
                return this.isValidYouTubeUrl(url) || this.isValidConferenceUrl(url);
            default:
                return false;
        }
    }
    
    isValidConferenceUrl(url) {
        // Basic URL validation for conference videos
        const conferencePatterns = [
            /^https?:\/\/.+zoom\.us\/rec\/.+/i,
            /^https?:\/\/.+teams\.microsoft\.com\/.+/i,
            /^https?:\/\/.+webex\.com\/.+/i,
            /^https?:\/\/.+gotomeeting\.com\/.+/i,
            /^https?:\/\/.+meet\.google\.com\/.+/i,
            /^https?:\/\/.+bluejeans\.com\/.+/i,
            // Generic URL pattern for other conference platforms
            /^https?:\/\/.+\.(com|org|net|edu)\/.+/i
        ];
        
        return conferencePatterns.some(pattern => pattern.test(url));
    }
    
    // API Key Management
    validateApiKey(provider) {
        const input = provider === 'openai' ? this.openaiApiKeyInput : this.anthropicApiKeyInput;
        const status = provider === 'openai' ? this.openaiStatus : this.anthropicStatus;
        const providerStatus = provider === 'openai' ? this.openaiProviderStatus : this.anthropicProviderStatus;
        
        const key = input.value.trim();
        
        if (!key) {
            this.updateApiKeyStatus(status, 'not-configured', 'Not configured');
            this.updateProviderStatus(providerStatus, 'not-configured', `${provider.charAt(0).toUpperCase() + provider.slice(1)}: Not configured`);
            return;
        }
        
        // Basic format validation
        const isValidFormat = provider === 'openai' ? 
            key.startsWith('sk-') && key.length > 20 : 
            key.startsWith('sk-ant-') && key.length > 20;
        
        if (isValidFormat) {
            this.updateApiKeyStatus(status, 'valid', 'Key format valid');
            this.updateProviderStatus(providerStatus, 'pending', `${provider.charAt(0).toUpperCase() + provider.slice(1)}: Key provided (not tested)`);
        } else {
            this.updateApiKeyStatus(status, 'invalid', 'Invalid key format');
            this.updateProviderStatus(providerStatus, 'error', `${provider.charAt(0).toUpperCase() + provider.slice(1)}: Invalid key format`);
        }
    }
    
    updateApiKeyStatus(element, status, message) {
        const icon = element.querySelector('i');
        const text = element.querySelector('span');
        
        // Reset classes
        element.classList.remove('valid', 'invalid', 'not-configured', 'testing');
        
        // Set new status
        element.classList.add(status);
        text.textContent = message;
        
        // Update icon
        switch (status) {
            case 'valid':
                icon.className = 'fas fa-check-circle';
                break;
            case 'invalid':
                icon.className = 'fas fa-exclamation-circle';
                break;
            case 'testing':
                icon.className = 'fas fa-spinner fa-spin';
                break;
            default:
                icon.className = 'fas fa-circle';
        }
    }
    
    updateProviderStatus(element, status, message) {
        const icon = element.querySelector('i');
        const text = element.querySelector('span');
        
        // Reset classes
        element.classList.remove('available', 'unavailable', 'not-configured', 'error', 'pending');
        
        // Set new status
        element.classList.add(status);
        text.textContent = message;
        
        // Update icon
        switch (status) {
            case 'available':
                icon.className = 'fas fa-check-circle';
                break;
            case 'unavailable':
            case 'error':
                icon.className = 'fas fa-times-circle';
                break;
            case 'pending':
                icon.className = 'fas fa-clock';
                break;
            default:
                icon.className = 'fas fa-circle';
        }
    }
    
    async testApiKeys() {
        const openaiKey = this.openaiApiKeyInput.value.trim();
        const anthropicKey = this.anthropicApiKeyInput.value.trim();
        
        if (!openaiKey && !anthropicKey) {
            alert('Please enter at least one API key to test.');
            return;
        }
        
        // Disable button during testing
        this.testApiKeysBtn.disabled = true;
        this.testApiKeysBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
        
        try {
            // Test keys by calling the models endpoint with the keys
            const response = await fetch('/api/models', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    openai_api_key: openaiKey || null,
                    anthropic_api_key: anthropicKey || null,
                    test_only: true
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Update provider status based on response
                if (data.providers) {
                    this.updateProviderStatusFromResponse(data.providers);
                }
                
                // Show success message
                this.showApiKeyTestResult(true, 'API keys tested successfully!');
            } else {
                throw new Error(data.detail || 'Failed to test API keys');
            }
        } catch (error) {
            console.error('Error testing API keys:', error);
            this.showApiKeyTestResult(false, error.message);
        } finally {
            // Re-enable button
            this.testApiKeysBtn.disabled = false;
            this.testApiKeysBtn.innerHTML = '<i class="fas fa-check-circle"></i> Test API Keys';
        }
    }
    
    updateProviderStatusFromResponse(providers) {
        // Update Ollama status
        if (providers.Ollama) {
            const status = providers.Ollama.available ? 'available' : 'unavailable';
            const modelCount = providers.Ollama.model_count || 0;
            const message = providers.Ollama.available ? 
                `Ollama: Available (${modelCount} models)` : 
                'Ollama: Unavailable';
            this.updateProviderStatus(this.ollamaProviderStatus, status, message);
        }
        
        // Update OpenAI status
        if (providers.OpenAI) {
            const status = providers.OpenAI.available ? 'available' : 'unavailable';
            const modelCount = providers.OpenAI.model_count || 0;
            const message = providers.OpenAI.available ? 
                `OpenAI: Available (${modelCount} models)` : 
                'OpenAI: Unavailable';
            this.updateProviderStatus(this.openaiProviderStatus, status, message);
        }
        
        // Update Anthropic status
        if (providers.Anthropic) {
            const status = providers.Anthropic.available ? 'available' : 'unavailable';
            const modelCount = providers.Anthropic.model_count || 0;
            const message = providers.Anthropic.available ? 
                `Anthropic: Available (${modelCount} models)` : 
                'Anthropic: Unavailable';
            this.updateProviderStatus(this.anthropicProviderStatus, status, message);
        }
    }
    
    showApiKeyTestResult(success, message) {
        // Create a temporary notification
        const notification = document.createElement('div');
        notification.className = `api-test-notification ${success ? 'success' : 'error'}`;
        notification.innerHTML = `
            <i class="fas fa-${success ? 'check-circle' : 'exclamation-circle'}"></i>
            <span>${message}</span>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => notification.classList.add('show'), 100);
        
        // Remove after delay
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => document.body.removeChild(notification), 300);
        }, 3000);
    }
    
    async refreshModels() {
        // Disable button during refresh
        this.refreshModelsBtn.disabled = true;
        this.refreshModelsBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
        
        try {
            // Get API keys
            const openaiKey = this.openaiApiKeyInput.value.trim();
            const anthropicKey = this.anthropicApiKeyInput.value.trim();
            
            // Load models with API keys
            await this.loadModelsWithApiKeys(openaiKey, anthropicKey);
            
            // Show success message
            this.showApiKeyTestResult(true, 'Models refreshed successfully!');
        } catch (error) {
            console.error('Error refreshing models:', error);
            this.showApiKeyTestResult(false, 'Failed to refresh models: ' + error.message);
        } finally {
            // Re-enable button
            this.refreshModelsBtn.disabled = false;
            this.refreshModelsBtn.innerHTML = '<i class="fas fa-sync"></i> Refresh Models';
        }
    }
    
    async loadModelsWithApiKeys(openaiKey, anthropicKey) {
        try {
            this.modelInfo.classList.add('loading');
            this.modelInfoText.textContent = 'Loading available models...';
            
            const requestBody = {};
            if (openaiKey) requestBody.openai_api_key = openaiKey;
            if (anthropicKey) requestBody.anthropic_api_key = anthropicKey;
            
            const response = await fetch('/api/models', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.populateModelDropdown(data.models);
                this.modelInfo.classList.remove('loading');
                this.updateModelInfo();
                
                // Update provider status
                if (data.providers) {
                    this.updateProviderStatusFromResponse(data.providers);
                }
            } else {
                throw new Error(data.detail || 'Failed to load models');
            }
        } catch (error) {
            console.error('Error loading models with API keys:', error);
            this.modelInfo.classList.remove('loading');
            this.modelInfo.classList.add('error');
            this.modelInfoText.textContent = 'Error loading models: ' + error.message;
            
            // Add default model as fallback
            this.aiModelSelect.innerHTML = '<option value="llama3.1:8b">llama3.1:8b (Default)</option>';
        }
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.youtubeSummarizer = new YouTubeSummarizer();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        console.log('Page hidden');
    } else {
        console.log('Page visible');
    }
});
