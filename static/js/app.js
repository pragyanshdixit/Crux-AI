/**
 * Crux AI — Frontend Application Logic
 * Manages state, visual stepper telemetry, intelligence rendering,
 * interactive RAG chat session, and client-side Groq Cloud API key storage.
 */

(function () {
    'use strict';

    // State
    const state = {
        sessionId: null,
        data: null,
        isProcessing: false,
        chatHistory: []
    };

    // Dynamic backend URL resolver (Supports standalone Render or Vercel+Render hybrid)
    function getApiUrl(endpoint) {
        const base = (window.CRUX_BACKEND_URL || localStorage.getItem('crux_backend_url') || '').replace(/\/$/, '');
        return `${base}${endpoint}`;
    }

    // DOM Elements
    const elements = {
        processForm: document.getElementById('processForm'),
        videoUrl: document.getElementById('videoUrl'),
        autoCleanup: document.getElementById('autoCleanup'),
        submitBtn: document.getElementById('submitBtn'),
        pasteBtn: document.getElementById('pasteBtn'),
        heroSection: document.getElementById('heroSection'),
        progressSection: document.getElementById('progressSection'),
        dashboardSection: document.getElementById('dashboardSection'),
        progressStepTitle: document.getElementById('progressStepTitle'),
        progressStepDesc: document.getElementById('progressStepDesc'),
        displayTitle: document.getElementById('displayTitle'),
        statWords: document.getElementById('statWords'),
        statTime: document.getElementById('statTime'),
        statChunks: document.getElementById('statChunks'),
        diskCleanedStat: document.getElementById('diskCleanedStat'),
        copyAllBtn: document.getElementById('copyAllBtn'),
        newVideoBtn: document.getElementById('newVideoBtn'),
        purgeBtn: document.getElementById('purgeBtn'),
        summaryContent: document.getElementById('summaryContent'),
        actionContent: document.getElementById('actionContent'),
        decisionsContent: document.getElementById('decisionsContent'),
        questionsContent: document.getElementById('questionsContent'),
        transcriptContent: document.getElementById('transcriptContent'),
        actionPill: document.getElementById('actionPill'),
        chatForm: document.getElementById('chatForm'),
        chatInput: document.getElementById('chatInput'),
        chatMessages: document.getElementById('chatMessages'),
        clearChatBtn: document.getElementById('clearChatBtn'),
        toastContainer: document.getElementById('toastContainer'),
        tabBtns: document.querySelectorAll('.tab-btn'),
        tabPanels: document.querySelectorAll('.tab-panel'),
        sampleChips: document.querySelectorAll('.sample-chip'),
        apiKeyModalBtn: document.getElementById('apiKeyModalBtn'),
        apiKeyModal: document.getElementById('apiKeyModal'),
        closeApiKeyModalBtn: document.getElementById('closeApiKeyModalBtn'),
        apiKeyInput: document.getElementById('apiKeyInput'),
        toggleKeyVisibilityBtn: document.getElementById('toggleKeyVisibilityBtn'),
        eyeIcon: document.getElementById('eyeIcon'),
        clearApiKeyBtn: document.getElementById('clearApiKeyBtn'),
        verifyApiKeyBtn: document.getElementById('verifyApiKeyBtn'),
        saveApiKeyBtn: document.getElementById('saveApiKeyBtn'),
        keyValidationStatus: document.getElementById('keyValidationStatus'),
        apiKeyStatusText: document.getElementById('apiKeyStatusText'),
        apiKeyIndicatorDot: document.getElementById('apiKeyIndicatorDot')
    };

    // Initialize Event Listeners
    function init() {
        // Form Submit
        elements.processForm.addEventListener('submit', handleProcessSubmit);

        // Paste button
        elements.pasteBtn.addEventListener('click', handlePaste);

        // Sample chips
        elements.sampleChips.forEach(chip => {
            chip.addEventListener('click', (e) => {
                const url = chip.getAttribute('data-url');
                if (url) {
                    elements.videoUrl.value = url;
                    elements.videoUrl.focus();
                }
            });
        });

        // Tab Switching
        elements.tabBtns.forEach(btn => {
            btn.addEventListener('click', () => switchTab(btn.getAttribute('data-tab')));
        });

        // Copy buttons
        document.querySelectorAll('[data-copy]').forEach(btn => {
            btn.addEventListener('click', () => {
                const targetId = btn.getAttribute('data-copy');
                const targetEl = document.getElementById(targetId);
                if (targetEl) {
                    copyToClipboard(targetEl.innerText, "Section copied to clipboard!");
                }
            });
        });

        // Copy Full Report
        elements.copyAllBtn.addEventListener('click', copyFullReport);

        // New Video Reset
        elements.newVideoBtn.addEventListener('click', resetView);

        // Purge Cache
        elements.purgeBtn.addEventListener('click', handlePurgeStorage);

        // Chat Form
        elements.chatForm.addEventListener('submit', handleChatSubmit);

        // Clear Chat
        elements.clearChatBtn.addEventListener('click', clearChat);

        // API Key Modal Listeners
        if (elements.apiKeyModalBtn) {
            elements.apiKeyModalBtn.addEventListener('click', openApiKeyModal);
        }
        if (elements.closeApiKeyModalBtn) {
            elements.closeApiKeyModalBtn.addEventListener('click', closeApiKeyModal);
        }
        if (elements.apiKeyModal) {
            elements.apiKeyModal.addEventListener('click', (e) => {
                if (e.target === elements.apiKeyModal) closeApiKeyModal();
            });
        }
        if (elements.saveApiKeyBtn) {
            elements.saveApiKeyBtn.addEventListener('click', saveApiKey);
        }
        if (elements.clearApiKeyBtn) {
            elements.clearApiKeyBtn.addEventListener('click', clearApiKey);
        }
        if (elements.verifyApiKeyBtn) {
            elements.verifyApiKeyBtn.addEventListener('click', verifyApiKey);
        }
        if (elements.toggleKeyVisibilityBtn) {
            elements.toggleKeyVisibilityBtn.addEventListener('click', toggleKeyVisibility);
        }

        // Initialize API key status badge on page load
        updateApiKeyUI();

        // Suggested Prompt Chips
        document.addEventListener('click', (e) => {
            const chip = e.target.closest('.prompt-chip');
            if (chip) {
                const prompt = chip.getAttribute('data-prompt');
                if (prompt) {
                    elements.chatInput.value = prompt;
                    elements.chatForm.dispatchEvent(new Event('submit'));
                }
            }
        });
    }

    // Handle Paste from Clipboard
    async function handlePaste() {
        try {
            const text = await navigator.clipboard.readText();
            if (text) {
                elements.videoUrl.value = text.trim();
                showToast("Pasted from clipboard", "info");
            }
        } catch (err) {
            elements.videoUrl.focus();
            showToast("Please press Ctrl+V to paste", "info");
        }
    }

    // Step Simulator for Visual Stepper (Accelerated for Groq LPU pipeline)
    let stepperInterval = null;
    function startStepper() {
        const steps = [
            { num: 1, title: "Downloading Audio Stream...", desc: "Solving YouTube JS bot challenges & fetching audio" },
            { num: 2, title: "Audio Preprocessing...", desc: "Validating stream size and preparing lightweight audio payload" },
            { num: 3, title: "Groq Whisper LPU Transcription...", desc: "Ultra-fast hardware-accelerated speech-to-text (~1-2 seconds)" },
            { num: 4, title: "Single-Pass AI Intelligence...", desc: "Synthesizing executive summaries, action items, and decisions in 1 pass" },
            { num: 5, title: "Building Vector Store...", desc: "Indexing transcription into ChromaDB for interactive RAG Q&A" }
        ];

        let currentIdx = 0;
        updateStepUI(steps[currentIdx]);

        stepperInterval = setInterval(() => {
            if (currentIdx < steps.length - 1) {
                currentIdx++;
                updateStepUI(steps[currentIdx]);
            }
        }, 1800);
    }

    function stopStepper() {
        if (stepperInterval) clearInterval(stepperInterval);
    }

    function updateStepUI(step) {
        elements.progressStepTitle.textContent = step.title;
        elements.progressStepDesc.textContent = step.desc;

        for (let i = 1; i <= 5; i++) {
            const stepEl = document.getElementById(`step${i}`);
            const lineEl = document.getElementById(`line${i}`);
            const statusEl = stepEl.querySelector('.step-status');

            if (i < step.num) {
                stepEl.className = 'step done';
                statusEl.textContent = 'Completed';
                if (lineEl) lineEl.className = 'step-line done';
            } else if (i === step.num) {
                stepEl.className = 'step active';
                statusEl.textContent = 'In Progress';
                if (lineEl) lineEl.className = 'step-line';
            } else {
                stepEl.className = 'step';
                statusEl.textContent = 'Waiting';
                if (lineEl) lineEl.className = 'step-line';
            }
        }
    }

    // Process Video Form Submit
    async function handleProcessSubmit(e) {
        e.preventDefault();
        const url = elements.videoUrl.value.trim();
        if (!url) return;

        state.isProcessing = true;
        elements.submitBtn.disabled = true;
        elements.heroSection.classList.add('hidden');
        elements.dashboardSection.classList.add('hidden');
        elements.progressSection.classList.remove('hidden');

        startStepper();

        try {
            const userApiKey = getStoredApiKey();
            const response = await fetch(getApiUrl('/api/process'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: url,
                    auto_cleanup: elements.autoCleanup.checked,
                    api_key: userApiKey || null
                })
            });

            const data = await response.json();
            stopStepper();

            if (!response.ok) {
                throw new Error(data.detail || "Failed to process video");
            }

            state.sessionId = data.session_id;
            state.data = data;

            renderDashboard(data);
            showToast("Video analyzed successfully!", "success");

        } catch (err) {
            stopStepper();
            showToast(err.message, "error");
            elements.progressSection.classList.add('hidden');
            elements.heroSection.classList.remove('hidden');
        } finally {
            state.isProcessing = false;
            elements.submitBtn.disabled = false;
        }
    }

    // Render Dashboard with Processed Results
    function renderDashboard(data) {
        elements.progressSection.classList.add('hidden');
        elements.dashboardSection.classList.remove('hidden');

        elements.displayTitle.textContent = data.title || "Video Analysis";
        elements.statWords.textContent = data.word_count?.toLocaleString() || "0";
        elements.statTime.textContent = data.processing_time || "0";
        elements.statChunks.textContent = data.chunk_count || "0";

        if (data.audio_cleaned) {
            elements.diskCleanedStat.classList.remove('hidden');
        } else {
            elements.diskCleanedStat.classList.add('hidden');
        }

        // Render Markdown Sections
        elements.summaryContent.innerHTML = renderMarkdown(data.summary);
        elements.actionContent.innerHTML = renderInteractiveTasks(data.actionable_items);
        elements.decisionsContent.innerHTML = renderMarkdown(data.decisions);
        elements.questionsContent.innerHTML = renderMarkdown(data.questions);
        elements.transcriptContent.textContent = data.transcription || "No transcript available.";

        // Count action tasks
        const taskCheckboxes = elements.actionContent.querySelectorAll('.task-check');
        elements.actionPill.textContent = taskCheckboxes.length || "0";

        // Bind interactive task clicks
        elements.actionContent.querySelectorAll('.task-item').forEach(item => {
            const check = item.querySelector('.task-check');
            item.addEventListener('click', (e) => {
                if (e.target !== check) check.checked = !check.checked;
                item.classList.toggle('completed', check.checked);
            });
        });

        // Set default tab
        switchTab('tabSummary');

        // Scroll to dashboard
        elements.dashboardSection.scrollIntoView({ behavior: 'smooth' });
    }

    // Interactive Action Items Formatter
    function renderInteractiveTasks(markdownText) {
        if (!markdownText) return "<p>No actionable items identified.</p>";

        const lines = markdownText.split('\n');
        let html = '';
        let inTable = false;
        let tableRows = [];

        for (let line of lines) {
            const trimmed = line.trim();
            // Check for numbered task lists
            const numMatch = trimmed.match(/^(\d+[\.\)]|\-|\*)\s+(.*)/);
            if (numMatch && !trimmed.startsWith('|')) {
                const text = numMatch[2];
                html += `
                    <div class="task-item">
                        <input type="checkbox" class="task-check">
                        <div class="task-content">
                            <span class="task-text">${formatInlineMarkdown(text)}</span>
                        </div>
                    </div>
                `;
            } else {
                html += renderMarkdownLine(line);
            }
        }
        return html;
    }

    // Markdown Parser (supports headers, bold, italics, tables, code, lists)
    function renderMarkdown(text) {
        if (!text) return "<p>No content available.</p>";

        const lines = text.split('\n');
        let html = '';
        let tableLines = [];
        let inTable = false;

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const trimmed = line.trim();

            if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
                inTable = true;
                tableLines.push(trimmed);
            } else {
                if (inTable) {
                    html += parseMarkdownTable(tableLines);
                    tableLines = [];
                    inTable = false;
                }
                html += renderMarkdownLine(line);
            }
        }

        if (inTable && tableLines.length > 0) {
            html += parseMarkdownTable(tableLines);
        }

        return html;
    }

    function renderMarkdownLine(line) {
        const trimmed = line.trim();
        if (!trimmed) return '<br>';

        if (trimmed.startsWith('### ')) {
            return `<h3>${formatInlineMarkdown(trimmed.substring(4))}</h3>`;
        }
        if (trimmed.startsWith('## ')) {
            return `<h2>${formatInlineMarkdown(trimmed.substring(3))}</h2>`;
        }
        if (trimmed.startsWith('# ')) {
            return `<h1>${formatInlineMarkdown(trimmed.substring(2))}</h1>`;
        }
        if (trimmed === '---') {
            return `<hr style="border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 20px 0;">`;
        }
        if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
            return `<li style="margin-left: 20px;">${formatInlineMarkdown(trimmed.substring(2))}</li>`;
        }

        return `<p>${formatInlineMarkdown(trimmed)}</p>`;
    }

    function parseMarkdownTable(rows) {
        if (rows.length < 2) return '';
        let html = '<table>';

        // Headers
        const headerCells = rows[0].split('|').slice(1, -1).map(c => c.trim());
        html += '<thead><tr>';
        headerCells.forEach(cell => {
            html += `<th>${formatInlineMarkdown(cell)}</th>`;
        });
        html += '</tr></thead><tbody>';

        // Skip separator row (row 1 with dashes)
        for (let i = 2; i < rows.length; i++) {
            const cells = rows[i].split('|').slice(1, -1).map(c => c.trim());
            html += '<tr>';
            cells.forEach(cell => {
                html += `<td>${formatInlineMarkdown(cell)}</td>`;
            });
            html += '</tr>';
        }

        html += '</tbody></table>';
        return html;
    }

    function formatInlineMarkdown(str) {
        return str
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`([^`]+)`/g, '<code style="background: rgba(255,255,255,0.08); padding: 2px 5px; border-radius: 4px; font-family: var(--font-mono); font-size: 12px;">$1</code>')
            .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" style="color: #818cf8; text-decoration: underline;">$1</a>');
    }

    // Tab Switching
    function switchTab(tabId) {
        elements.tabBtns.forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
        });

        elements.tabPanels.forEach(panel => {
            panel.classList.toggle('active', panel.id === tabId);
        });
    }

    // Handle Chat Submit
    async function handleChatSubmit(e) {
        e.preventDefault();
        const question = elements.chatInput.value.trim();
        if (!question || !state.sessionId) return;

        // Append user bubble
        appendChatBubble('user', question);
        elements.chatInput.value = '';

        // Add thinking bubble
        const thinkingId = appendChatBubble('ai', '<span style="color: var(--text-dim);">Analyzing video context...</span>');

        try {
            const userApiKey = getStoredApiKey();
            const response = await fetch(getApiUrl('/api/chat'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: state.sessionId,
                    message: question,
                    api_key: userApiKey || null
                })
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || "RAG chat failed");
            }

            // Replace thinking message with answer
            const bubbleEl = document.getElementById(thinkingId);
            if (bubbleEl) {
                bubbleEl.innerHTML = renderMarkdown(data.answer);
            }

        } catch (err) {
            const bubbleEl = document.getElementById(thinkingId);
            if (bubbleEl) {
                bubbleEl.innerHTML = `<span style="color: var(--rose);">Error: ${err.message}</span>`;
            }
        }
    }

    function appendChatBubble(role, contentHtml) {
        const id = 'msg_' + Math.random().toString(36).substring(2, 9);
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-msg ${role}-msg`;
        msgDiv.innerHTML = `
            <div class="msg-avatar">${role === 'user' ? 'YOU' : 'AI'}</div>
            <div class="msg-bubble" id="${id}">${contentHtml}</div>
        `;

        elements.chatMessages.appendChild(msgDiv);
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
        return id;
    }

    function clearChat() {
        elements.chatMessages.innerHTML = `
            <div class="chat-msg ai-msg">
                <div class="msg-avatar">AI</div>
                <div class="msg-bubble">
                    <p>Chat cleared. Ask any new question about the video!</p>
                </div>
            </div>
        `;
    }

    // Copy to Clipboard
    async function copyToClipboard(text, successMsg = "Copied to clipboard!") {
        try {
            await navigator.clipboard.writeText(text);
            showToast(successMsg, "success");
        } catch (err) {
            showToast("Failed to copy", "error");
        }
    }

    function copyFullReport() {
        if (!state.data) return;
        const report = `
# ${state.data.title}
Analysis generated by Crux AI

## Executive Summary
${state.data.summary}

## Actionable Items
${state.data.actionable_items}

## Key Decisions
${state.data.decisions}

## Questions Explored
${state.data.questions}
        `.trim();

        copyToClipboard(report, "Full executive report copied to clipboard!");
    }

    // Purge Temporary Audio Files on Server
    async function handlePurgeStorage() {
        elements.purgeBtn.disabled = true;
        try {
            const res = await fetch(getApiUrl('/api/purge-downloads'), { method: 'POST' });
            const data = await res.json();
            showToast("Temporary audio cache cleared from server.", "success");
        } catch (err) {
            showToast("Failed to clear cache", "error");
        } finally {
            elements.purgeBtn.disabled = false;
        }
    }

    // API Key Storage & Helpers
    function getStoredApiKey() {
        return (localStorage.getItem('crux_groq_api_key') || '').trim();
    }

    function updateApiKeyUI() {
        const key = getStoredApiKey();
        if (key) {
            if (elements.apiKeyStatusText) elements.apiKeyStatusText.textContent = 'Custom Key';
            if (elements.apiKeyIndicatorDot) elements.apiKeyIndicatorDot.classList.add('active');
            if (elements.apiKeyInput) elements.apiKeyInput.value = key;
        } else {
            if (elements.apiKeyStatusText) elements.apiKeyStatusText.textContent = 'API Key';
            if (elements.apiKeyIndicatorDot) elements.apiKeyIndicatorDot.classList.remove('active');
            if (elements.apiKeyInput) elements.apiKeyInput.value = '';
        }
    }

    function openApiKeyModal() {
        updateApiKeyUI();
        if (elements.keyValidationStatus) {
            elements.keyValidationStatus.className = 'key-validation-status hidden';
            elements.keyValidationStatus.textContent = '';
        }
        if (elements.apiKeyModal) elements.apiKeyModal.classList.remove('hidden');
        if (elements.apiKeyInput) elements.apiKeyInput.focus();
    }

    function closeApiKeyModal() {
        if (elements.apiKeyModal) elements.apiKeyModal.classList.add('hidden');
    }

    function saveApiKey() {
        const key = elements.apiKeyInput.value.trim();
        if (key) {
            localStorage.setItem('crux_groq_api_key', key);
            showToast("Groq API key saved in browser!", "success");
        } else {
            localStorage.removeItem('crux_groq_api_key');
            showToast("API key removed. Using server default.", "info");
        }
        updateApiKeyUI();
        closeApiKeyModal();
    }

    function clearApiKey() {
        localStorage.removeItem('crux_groq_api_key');
        if (elements.apiKeyInput) elements.apiKeyInput.value = '';
        updateApiKeyUI();
        if (elements.keyValidationStatus) {
            elements.keyValidationStatus.className = 'key-validation-status hidden';
        }
        showToast("Custom API key removed.", "info");
    }

    async function verifyApiKey() {
        const key = elements.apiKeyInput.value.trim();
        if (!key) {
            elements.keyValidationStatus.className = 'key-validation-status error';
            elements.keyValidationStatus.textContent = 'Please enter an API key to test.';
            return;
        }

        elements.verifyApiKeyBtn.disabled = true;
        elements.keyValidationStatus.className = 'key-validation-status';
        elements.keyValidationStatus.textContent = 'Verifying key with Groq Cloud...';

        try {
            const res = await fetch(getApiUrl('/api/verify-key'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: key })
            });
            const data = await res.json();
            if (res.ok && data.valid) {
                elements.keyValidationStatus.className = 'key-validation-status success';
                elements.keyValidationStatus.textContent = '✓ Groq API key is valid and connected!';
            } else {
                elements.keyValidationStatus.className = 'key-validation-status error';
                elements.keyValidationStatus.textContent = '✗ ' + (data.message || 'Key verification failed');
            }
        } catch (err) {
            elements.keyValidationStatus.className = 'key-validation-status error';
            elements.keyValidationStatus.textContent = '✗ Network error verifying key';
        } finally {
            elements.verifyApiKeyBtn.disabled = false;
        }
    }

    function toggleKeyVisibility() {
        const isPwd = elements.apiKeyInput.type === 'password';
        elements.apiKeyInput.type = isPwd ? 'text' : 'password';
    }

    // Reset View
    function resetView() {
        state.data = null;
        state.sessionId = null;
        elements.videoUrl.value = '';
        elements.dashboardSection.classList.add('hidden');
        elements.progressSection.classList.add('hidden');
        elements.heroSection.classList.remove('hidden');
        elements.videoUrl.focus();
        clearChat();
    }

    // Toast Notification System
    function showToast(message, type = "info") {
        const toast = document.createElement('div');
        toast.className = 'toast';
        
        let icon = 'ℹ️';
        if (type === 'success') icon = '✓';
        if (type === 'error') icon = '⚠️';

        toast.innerHTML = `<span style="font-weight: 700; color: ${type === 'success' ? '#10b981' : type === 'error' ? '#f43f5e' : '#818cf8'};">${icon}</span> <span>${message}</span>`;
        elements.toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }

    // Boot
    document.addEventListener('DOMContentLoaded', init);
})();
