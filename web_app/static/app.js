let _originalText = '';
let _rewrittenText = '';

const STRENGTH_MAP = ['light', 'medium', 'aggressive'];
const STRENGTH_COLORS = {
    light: { bg: 'rgba(34, 197, 94, 0.15)', fg: '#4ade80' },
    medium: { bg: 'rgba(234, 179, 8, 0.15)', fg: '#facc15' },
    aggressive: { bg: 'rgba(239, 68, 68, 0.15)', fg: '#f87171' }
};

function updateStrengthLabel(val) {
    const name = STRENGTH_MAP[val];
    const label = document.getElementById('strengthLabel');
    const colors = STRENGTH_COLORS[name];
    label.textContent = name.charAt(0).toUpperCase() + name.slice(1);
    label.style.background = colors.bg;
    label.style.color = colors.fg;
}

function getStrength() {
    return STRENGTH_MAP[document.getElementById('strengthSlider').value];
}

const fileInput = document.getElementById('fileInput');

fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    document.getElementById('loading').style.display = 'block';

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorElem = await response.json();
            throw new Error(errorElem.detail || 'Upload failed');
        }

        const data = await response.json();
        document.getElementById('rawText').value = data.content;
        document.getElementById('rawText').dispatchEvent(new Event('input'));

    } catch (err) {
        alert('Error uploading file: ' + err.message);
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
});

async function processText(action) {
    const text = document.getElementById('rawText').value;
    if (!text) {
        alert('Please enter some text first.');
        return;
    }

    _originalText = text;

    document.getElementById('loading').style.display = 'block';
    document.getElementById('input-panel').classList.add('opacity-50', 'pointer-events-none');

    const formData = new FormData();
    formData.append('action', action);
    formData.append('text', text);
    formData.append('strength', getStrength());

    try {
        const response = await fetch('/api/process', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorElem = await response.json();
            throw new Error(errorElem.detail || 'Processing failed');
        }

        if (action === 'rewrite') {
            document.getElementById('results-panel').classList.remove('hidden');
            document.getElementById('input-panel').classList.add('hidden');

            document.getElementById('cleanResult').value = 'Sanitizing...';
            document.getElementById('finalResult').value = '';
            document.getElementById('aiScore').classList.add('hidden');
            document.getElementById('changesLog').innerHTML = '<div class="text-slate-500 italic">Processing...</div>';

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');

                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const msg = JSON.parse(line);
                        handleStreamEvent(msg);
                    } catch (e) {
                        console.error('Error parsing stream line', e);
                    }
                }
            }

            if (buffer.trim()) {
                try {
                    const msg = JSON.parse(buffer);
                    handleStreamEvent(msg);
                } catch (e) {
                    console.error('Error parsing final stream line', e);
                }
            }

        } else {
            const data = await response.json();
            History.addSessionEntry(action, text, data.clean_text);
            showResults(data, action);
        }

    } catch (err) {
        alert('Error processing text: ' + err.message);
        if (document.getElementById('results-panel').classList.contains('hidden')) {
            document.getElementById('input-panel').classList.remove('opacity-50', 'pointer-events-none');
        }
    } finally {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('input-panel').classList.remove('opacity-50', 'pointer-events-none');
    }
}

async function handleStreamEvent(msg) {
    if (msg.type === 'error') {
        alert("⚠️ " + msg.data);
        // Reset UI state to allow user to see what happened or try sanitization
        document.getElementById('loading').style.display = 'none';
        document.getElementById('input-panel').classList.remove('opacity-50', 'pointer-events-none');
        // If we were in rewrite mode but failed, maybe show input panel again?
        // But wait, if stream started, we hid input panel.
        document.getElementById('results-panel').classList.add('hidden');
        document.getElementById('input-panel').classList.remove('hidden');
        return;
    }

    if (msg.type === 'stage') {
        if (msg.data.step === 'clean') {
            document.getElementById('cleanResult').value = msg.data.clean_text;
        } else if (msg.data.step === 'analyzed') {
            document.getElementById('changesLog').innerHTML = '<div class="text-amber-400 animate-pulse flex items-center gap-2"><span class="loader h-3 w-3 border-t-amber-400"></span> Rewriting with AI logic...</div>';
        } else if (msg.data.step === 'humanizing') {
            document.getElementById('changesLog').innerHTML = '<div class="text-purple-400 animate-pulse flex items-center gap-2"><span class="loader h-3 w-3 border-t-purple-400"></span> Humanizing text patterns...</div>';
        } else if (msg.data.step === 'verifying') {
            document.getElementById('changesLog').innerHTML = '<div class="text-blue-400 animate-pulse flex items-center gap-2"><span class="loader h-3 w-3 border-t-blue-400"></span> Verifying improvements...</div>';
        }
    } else if (msg.type === 'chunk') {
        const finalResult = document.getElementById('finalResult');
        finalResult.value += msg.data;
        finalResult.scrollTop = finalResult.scrollHeight;
    } else if (msg.type === 'done') {
        const data = msg.data;
        History.addSessionEntry('rewrite', _originalText, data.rewritten_text || data.clean_text);
        showResults(data, 'rewrite');
    } else if (msg.type === 'ai_score') {
        // Late event: AI score arrived after results were already shown
        const score = msg.data.score;
        const scoreEl = document.getElementById('aiScore');
        const getScoreClass = (s) => s >= 7 ? 'text-red-400' : (s >= 4 ? 'text-amber-400' : 'text-emerald-400');
        const getBorderClass = (s) => s >= 7 ? 'border-red-500/30' : (s >= 4 ? 'border-amber-500/30' : 'border-emerald-500/30');

        scoreEl.innerHTML = `
                    <span class="text-slate-400 font-medium mr-2">Original AI Score:</span>
                    <span class="${getScoreClass(score)}">${score}/10</span>
                `;
        scoreEl.className = `bg-slate-900/80 backdrop-blur-md border ${getBorderClass(score)} rounded-full px-6 py-2 text-sm font-bold shadow-lg inline-flex items-center justify-center transition-all duration-500`;
    } else if (msg.type === 'error') {
        console.error(msg.data);
    }
}

function showResults(data, action) {
    document.getElementById('results-panel').classList.remove('hidden');
    document.getElementById('input-panel').classList.add('hidden');

    document.getElementById('cleanResult').value = data.clean_text;

    if (action === 'rewrite') {
        _rewrittenText = data.rewritten_text;
        document.getElementById('finalResult').value = data.rewritten_text;

        // Show AI score badge in "calculating" state — actual score arrives via ai_score event
        const scoreEl = document.getElementById('aiScore');
        scoreEl.classList.remove('hidden');
        scoreEl.innerHTML = `
                    <span class="text-slate-400 font-medium mr-2">Original AI Score:</span>
                    <span class="text-slate-500 animate-pulse flex items-center gap-2">
                        <span class="loader h-3 w-3 border-t-slate-400"></span> Calculating...
                    </span>
                `;
        scoreEl.className = `bg-slate-900/80 backdrop-blur-md border border-slate-700/30 rounded-full px-6 py-2 text-sm font-bold shadow-lg inline-flex items-center justify-center`;

        if (data.rewritten_metrics) {
            renderMetrics(data.rewritten_metrics);
            renderParaAnalysis(data.clean_text, data.rewritten_text, data.rewritten_metrics);
        }

        buildDiffView(data.clean_text, data.rewritten_text);

    } else {
        document.getElementById('finalResult').value = data.clean_text;
        document.getElementById('aiScore').classList.add('hidden');
        document.getElementById('metricsPanel').classList.add('hidden');
        document.getElementById('paraAnalysisPanel').classList.add('hidden');
    }

    const logDiv = document.getElementById('changesLog');
    logDiv.innerHTML = '';

    if (data.changes && data.changes.length > 0) {
        data.changes.forEach((c, i) => {
            const div = document.createElement('div');
            div.className = 'py-1 border-b border-slate-800 last:border-0';
            div.innerHTML = `<span class="text-slate-600 mr-2">${i + 1}.</span> ${c.description}`;
            logDiv.appendChild(div);
        });
    } else {
        logDiv.textContent = 'No changes detected.';
    }
}

function renderMetrics(metrics) {
    const panel = document.getElementById('metricsPanel');
    const grid = document.getElementById('metricsGrid');
    panel.classList.remove('hidden');
    grid.innerHTML = '';

    const items = [];

    const sv = metrics.sentence_variance || {};
    if (sv.category) {
        const good = sv.category === 'burstive';
        const ok = sv.category === 'moderate';
        items.push({ label: 'Sentence Variety', value: sv.category, good: good, ok: ok });
    }

    const ap = metrics.ai_phrases || {};
    if (ap.count !== undefined) {
        items.push({ label: 'AI Phrases', value: ap.count === 0 ? 'None found' : ap.count + ' found', good: ap.count === 0, ok: ap.count <= 2 });
    }

    const hd = metrics.hedging || {};
    if (hd.filler_density !== undefined) {
        const low = hd.filler_density < 0.02;
        items.push({ label: 'Hedging Density', value: low ? 'Low' : 'Elevated', good: low, ok: hd.filler_density < 0.04 });
    }

    const vf = metrics.verb_frequency || {};
    if (vf.ai_verb_density !== undefined) {
        const low = vf.ai_verb_density < 0.1;
        items.push({ label: 'AI Verbs', value: low ? 'Low' : 'Elevated', good: low, ok: vf.ai_verb_density < 0.2 });
    }

    const rep = metrics.repetition || {};
    if (rep.count !== undefined) {
        items.push({ label: 'Repetition', value: rep.count === 0 ? 'None' : rep.count + ' phrases', good: rep.count === 0, ok: rep.count <= 2 });
    }

    const pp = metrics.punctuation_profile || {};
    if (pp.structure_ratio !== undefined) {
        const balanced = pp.structure_ratio < 0.7;
        items.push({ label: 'Punctuation', value: balanced ? 'Varied' : 'Rigid', good: balanced, ok: pp.structure_ratio < 0.85 });
    }

    items.forEach(item => {
        const colorClass = item.good ? 'text-emerald-400 border-emerald-500/20 bg-emerald-500/5' : (item.ok ? 'text-amber-400 border-amber-500/20 bg-amber-500/5' : 'text-red-400 border-red-500/20 bg-red-500/5');
        const icon = item.good ? 'check_circle' : (item.ok ? 'warning' : 'error');
        const div = document.createElement('div');
        div.className = `rounded-xl border px-3 py-2.5 ${colorClass}`;
        div.innerHTML = `
                    <div class="flex items-center gap-1.5 mb-1">
                        <span class="material-symbols-outlined text-[14px]">${icon}</span>
                        <span class="text-[10px] uppercase tracking-wider font-semibold text-slate-400">${item.label}</span>
                    </div>
                    <span class="text-sm font-medium">${item.value}</span>
                `;
        grid.appendChild(div);
    });
}

// Per-Paragraph Analysis (Step 7)
function renderParaAnalysis(originalText, rewrittenText, metrics) {
    const panel = document.getElementById('paraAnalysisPanel');
    const grid = document.getElementById('paraAnalysisGrid');
    panel.classList.remove('hidden');
    grid.innerHTML = '';

    const paragraphs = rewrittenText.split(/\n\n+/).filter(p => p.trim().length > 0);
    if (paragraphs.length <= 1) {
        panel.classList.add('hidden');
        return;
    }

    paragraphs.forEach((para, i) => {
        const wordCount = para.split(/\s+/).length;
        const sentences = para.split(/(?<=[.!?])\s+/).filter(s => s.trim());
        const avgSentLen = sentences.length > 0 ? Math.round(wordCount / sentences.length) : wordCount;

        const hasAiPhrase = (metrics.ai_phrases?.phrases || []).some(p => para.toLowerCase().includes(p));
        const sentLengths = sentences.map(s => s.split(/\s+/).length);
        const variance = sentLengths.length > 1 ?
            Math.round(sentLengths.reduce((sum, len) => sum + Math.pow(len - avgSentLen, 2), 0) / sentLengths.length) : 0;

        let score = 'good';
        let scoreLabel = 'Natural';
        let scoreColor = 'emerald';
        if (hasAiPhrase) { score = 'bad'; scoreLabel = 'AI Phrase'; scoreColor = 'red'; }
        else if (variance < 5 && sentences.length > 2) { score = 'warn'; scoreLabel = 'Uniform'; scoreColor = 'amber'; }
        else if (avgSentLen > 25) { score = 'warn'; scoreLabel = 'Long sentences'; scoreColor = 'amber'; }

        const div = document.createElement('div');
        div.className = `para-score flex items-start gap-3 p-3 rounded-xl border border-${scoreColor}-500/20 bg-${scoreColor}-500/5`;
        div.innerHTML = `
                    <div class="flex-shrink-0 w-7 h-7 rounded-full bg-${scoreColor}-500/20 flex items-center justify-center text-${scoreColor}-400 text-xs font-bold">${i + 1}</div>
                    <div class="flex-grow min-w-0">
                        <p class="text-xs text-slate-400 truncate mb-1">${para.substring(0, 80)}${para.length > 80 ? '...' : ''}</p>
                        <div class="flex gap-3 text-[10px] text-slate-500">
                            <span>${wordCount} words</span>
                            <span>${sentences.length} sentences</span>
                            <span>Avg: ${avgSentLen} w/s</span>
                        </div>
                    </div>
                    <span class="flex-shrink-0 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-${scoreColor}-500/15 text-${scoreColor}-400">${scoreLabel}</span>
                `;
        grid.appendChild(div);
    });
}

// Diff View (Step 4)
function buildDiffView(original, rewritten) {
    const diffEl = document.getElementById('diffView');

    const origWords = original.split(/(\s+)/);
    const newWords = rewritten.split(/(\s+)/);

    const origSet = new Set(origWords.filter(w => w.trim()));
    const newSet = new Set(newWords.filter(w => w.trim()));

    let html = '<div class="mb-3 pb-2 border-b border-white/5">';
    html += '<span class="text-[10px] uppercase tracking-wider font-semibold text-slate-500">Original → Rewritten differences</span>';
    html += '</div>';

    html += '<div class="mb-4"><span class="text-[10px] uppercase tracking-wider font-semibold text-slate-600 mr-3">Original:</span>';
    origWords.forEach(word => {
        if (!word.trim()) { html += word; return; }
        if (!newSet.has(word)) {
            html += `<span class="diff-removed">${word}</span>`;
        } else {
            html += word;
        }
    });
    html += '</div>';

    html += '<div><span class="text-[10px] uppercase tracking-wider font-semibold text-slate-600 mr-3">Rewritten:</span>';
    newWords.forEach(word => {
        if (!word.trim()) { html += word; return; }
        if (!origSet.has(word)) {
            html += `<span class="diff-added">${word}</span>`;
        } else {
            html += word;
        }
    });
    html += '</div>';

    diffEl.innerHTML = html;
}

// Tab Switching
function switchTab(tab) {
    const textEl = document.getElementById('finalResult');
    const diffEl = document.getElementById('diffView');
    const tabText = document.getElementById('tabText');
    const tabDiff = document.getElementById('tabDiff');

    if (tab === 'text') {
        textEl.classList.remove('hidden');
        diffEl.classList.add('hidden');
        tabText.className = tabText.className.replace('tab-inactive', 'tab-active');
        tabDiff.className = tabDiff.className.replace('tab-active', 'tab-inactive');
    } else {
        textEl.classList.add('hidden');
        diffEl.classList.remove('hidden');
        tabDiff.className = tabDiff.className.replace('tab-inactive', 'tab-active');
        tabText.className = tabText.className.replace('tab-active', 'tab-inactive');
    }
}

function reset() {
    document.getElementById('results-panel').classList.add('hidden');
    document.getElementById('input-panel').classList.remove('hidden');
    document.getElementById('rawText').value = '';
    document.getElementById('rawText').dispatchEvent(new Event('input'));
    document.getElementById('fileInput').value = '';
    document.getElementById('paraAnalysisPanel').classList.add('hidden');
    switchTab('text');
    _originalText = '';
    _rewrittenText = '';
}

function clearText() {
    document.getElementById('rawText').value = '';
    document.getElementById('rawText').dispatchEvent(new Event('input'));
}

async function copyResult() {
    const text = document.getElementById('finalResult').value;
    if (!text) return;

    try {
        await navigator.clipboard.writeText(text);
        const btn = document.getElementById('copyBtn');
        const originalHTML = btn.innerHTML;
        btn.innerHTML = `<span class="material-symbols-outlined text-[14px]">check</span> Copied`;
        setTimeout(() => btn.innerHTML = originalHTML, 2000);
    } catch (err) {
        console.error('Failed to copy:', err);
    }
}