document.addEventListener('DOMContentLoaded', () => {
    const chatHistory = document.getElementById('chat-history');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const exportPdfBtn = document.getElementById('export-pdf-btn');
    const clearChatBtn = document.getElementById('clear-chat-btn');
    const memoryCount = document.getElementById('memory-count');
    const reflectionCount = document.getElementById('reflection-count');
    const metaRoute = document.getElementById('meta-route');
    const metaComplexity = document.getElementById('meta-complexity');
    const metaModel = document.getElementById('meta-model');
    const groundingList = document.getElementById('grounding-list');
    const retrievalIndicator = document.getElementById('retrieval-indicator');
    
    // User Identity Logic
    let userId = localStorage.getItem('apj_user_id');
    if (!userId) {
        userId = 'user_' + Math.random().toString(36).substring(2, 11);
        localStorage.setItem('apj_user_id', userId);
    }
    console.log(`[IDENTITY] Session active for: ${userId}`);

    // Auto-resize textarea
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = userInput.scrollHeight + 'px';
    });

    // Handle Enter to send
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);

    exportPdfBtn.addEventListener('click', exportToPDF);
    
    clearChatBtn.addEventListener('click', () => {
        if (confirm('Clear entire conversation?')) {
            chatHistory.innerHTML = '';
        }
    });

    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // Clear input
        userInput.value = '';
        userInput.style.height = 'auto';

        // Append User Message
        appendMessage('user', message);
        scrollToBottom();

        // Show loading state
        retrievalIndicator.classList.remove('hidden');
        const assistantMsgDiv = appendMessage('assistant', '');
        const assistantContent = assistantMsgDiv.querySelector('.message-content');
        assistantContent.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';

        try {
            const response = await fetch(`${window.BACKEND_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    query: message,
                    user_id: userId
                })
            });

            if (!response.ok) throw new Error('API Error');

            const data = await response.json();
            
            // Hide loading
            retrievalIndicator.classList.add('hidden');
            
            // Render response as Markdown with Sanitization
            assistantContent.innerHTML = '';
            const rawHtml = marked.parse(data.answer);
            const cleanHtml = DOMPurify.sanitize(rawHtml);
            assistantContent.innerHTML = cleanHtml;
            
            // Apply highlighting to code blocks
            assistantContent.querySelectorAll('pre').forEach((pre) => {
                const code = pre.querySelector('code');
                
                // Add copy button
                const btn = document.createElement('button');
                btn.className = 'copy-code-btn';
                btn.innerHTML = '<i class="bi bi-clipboard"></i> Copy';
                pre.appendChild(btn);
                
                btn.addEventListener('click', () => {
                    navigator.clipboard.writeText(code.innerText).then(() => {
                        btn.innerHTML = '<i class="bi bi-check2"></i> Copied';
                        btn.classList.add('copied');
                        setTimeout(() => {
                            btn.innerHTML = '<i class="bi bi-clipboard"></i> Copy';
                            btn.classList.remove('copied');
                        }, 2000);
                    });
                });
                
                if (code) hljs.highlightElement(code);
            });
            
            scrollToBottom();
            
            // Update metadata
            updateMetadata(data.metadata, data.grounding_sources);
            
            // Refresh stats
            refreshStats();

        } catch (error) {
            console.error(error);
            assistantContent.innerHTML = 'Sorry, something went wrong. Please check if the backend is running.';
            retrievalIndicator.classList.add('hidden');
        }
    }

    function appendMessage(role, content) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;
        msgDiv.innerHTML = `
            <div class="message-content">${content}</div>
        `;
        chatHistory.appendChild(msgDiv);
        return msgDiv;
    }

    async function typeWriter(element, text) {
        const words = text.split(' ');
        for (let i = 0; i < words.length; i++) {
            element.innerHTML += words[i] + ' ';
            scrollToBottom();
            // Faster typewriter
            if (i % 2 === 0) await new Promise(r => setTimeout(r, 20));
        }
    }

    function scrollToBottom() {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    async function exportToPDF() {
        const element = document.getElementById('chat-history');
        const sessionName = document.getElementById('current-session-name').textContent.trim() || 'Conversation';
        
        // Sanitize filename: remove non-alphanumeric characters except spaces and dashes
        const sanitizedName = sessionName.replace(/[^a-z0-9 -]/gi, '').trim();
        const filename = `${sanitizedName || 'APJ_AI_Export'}.pdf`;

        // Options for html2pdf
        const opt = {
            margin: 10,
            filename: filename,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2, backgroundColor: '#ffffff', useCORS: true },
            jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
        };

        // Create a clone for printing with white background and black text
        const clone = element.cloneNode(true);
        clone.style.background = 'white';
        clone.style.color = 'black';
        clone.style.padding = '20px';
        clone.querySelectorAll('.message').forEach(m => {
            m.style.color = 'black';
            m.style.marginBottom = '20px';
        });
        clone.querySelectorAll('.message.user').forEach(m => {
            m.style.background = '#f0f0f0';
            m.style.padding = '10px';
            m.style.borderRadius = '10px';
        });

        const originalIcon = exportPdfBtn.innerHTML;
        exportPdfBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
        exportPdfBtn.disabled = true;

        try {
            await html2pdf().set(opt).from(clone).save();
        } catch (e) {
            console.error("PDF Export failed", e);
            alert("Failed to generate PDF. Please try again.");
        } finally {
            exportPdfBtn.innerHTML = originalIcon;
            exportPdfBtn.disabled = false;
        }
    }

    function updateMetadata(meta, grounding) {
        if (meta) {
            metaRoute.textContent = meta.route || 'N/A';
            metaComplexity.textContent = meta.complexity_score?.toFixed(2) || '0.00';
            metaModel.textContent = meta.model || 'N/A';
            const metaProvider = document.getElementById('meta-provider');
            if (metaProvider) metaProvider.textContent = meta.provider || 'local';
        }

        if (grounding && grounding.length > 0) {
            groundingList.innerHTML = '';
            grounding.forEach(source => {
                const item = document.createElement('div');
                item.className = 'grounding-item';
                item.textContent = `ID: ${source.substring(0, 8)}...`;
                groundingList.appendChild(item);
            });
        } else {
            groundingList.innerHTML = '<div class="empty-state">No context active</div>';
        }
    }

    async function refreshStats() {
        try {
            // userId is defined in the outer scope
            
            // Fetch reflections
            const refResp = await fetch(`${window.BACKEND_URL}/reflection/list?user_id=${userId}`);
            const reflections = await refResp.json();
            reflectionCount.textContent = reflections.length;

            // Simple way to get memory count (search with empty query might work depending on implementation)
            // Or just hardcode/estimate for now if there's no direct count endpoint
            // I'll try to use a dummy search
            const memResp = await fetch(`${window.BACKEND_URL}/memory/search?query=&user_id=${userId}`);
            const memories = await memResp.json();
            memoryCount.textContent = memories.length + "+"; // Placeholder for total

        } catch (e) {
            console.warn("Could not refresh stats", e);
        }
    }

    // Initial stats fetch
    refreshStats();
});
