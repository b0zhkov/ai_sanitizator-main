const SessionHistory = (() => {
    const STORAGE_KEY = "sanitizator_session_history";

    function _load() {
        try {
            const raw = sessionStorage.getItem(STORAGE_KEY);
            return raw ? JSON.parse(raw) : [];
        } catch {
            return [];
        }
    }

    function _save(entries) {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
    }

    function add(actionType, inputText, outputText) {
        const entries = _load();
        entries.unshift({
            action_type: actionType,
            input_text: inputText,
            output_text: outputText,
            created_at: new Date().toISOString(),
        });

        if (entries.length > 50) entries.length = 50;

        _save(entries);
    }

    function getAll() {
        return _load();
    }

    function clear() {
        sessionStorage.removeItem(STORAGE_KEY);
    }

    return { add, getAll, clear };
})();


const History = (() => {
    let _isOpen = false;

    function init() {
        renderPanel();
    }

    function toggle() {
        _isOpen = !_isOpen;
        const panel = document.getElementById("historyPanel");

        if (_isOpen) {
            panel.classList.remove("translate-x-full");
            panel.classList.add("translate-x-0");
            renderPanel();
        } else {
            panel.classList.remove("translate-x-0");
            panel.classList.add("translate-x-full");
        }
    }

    function close() {
        _isOpen = false;
        const panel = document.getElementById("historyPanel");
        panel.classList.remove("translate-x-0");
        panel.classList.add("translate-x-full");
    }

    async function renderPanel() {
        const list = document.getElementById("historyList");
        const emptyState = document.getElementById("historyEmpty");
        let entries = [];

        if (Auth.isLoggedIn()) {
            try {
                entries = await _fetchFromServer();
            } catch {
                entries = SessionHistory.getAll();
            }
        } else {
            entries = SessionHistory.getAll();
        }

        list.innerHTML = "";

        if (entries.length === 0) {
            emptyState.classList.remove("hidden");
            return;
        }

        emptyState.classList.add("hidden");

        entries.forEach((entry) => {
            const card = _buildCard(entry);
            list.appendChild(card);
        });
    }

    function _buildCard(entry) {
        const div = document.createElement("div");
        div.className =
            "p-3 rounded-xl border border-theme-divider bg-theme-navbar hover:bg-white/10 transition-colors cursor-pointer group";

        const isRewrite = entry.action_type === "rewrite";
        const badgeColor = isRewrite ? "blue" : "amber";
        const badgeLabel = isRewrite ? "Rewrite" : "Clean";

        const preview =
            entry.input_text.length > 80
                ? entry.input_text.substring(0, 80) + "..."
                : entry.input_text;

        const timeStr = _formatTime(entry.created_at);

        div.innerHTML = `
            <div class="flex items-center justify-between mb-2">
                <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-${badgeColor}-500/15 text-${badgeColor}-400">${badgeLabel}</span>
                <div class="flex items-center gap-2">
                    <span class="text-[10px] text-theme-muted">${timeStr}</span>
                    ${entry.id ? `<button class="hidden group-hover:block text-theme-muted hover:text-red-400 transition-colors" onclick="event.stopPropagation(); History.deleteEntry(${entry.id})">
                        <span class="material-symbols-outlined text-[14px]">close</span>
                    </button>` : ""}
                </div>
            </div>
            <p class="text-xs text-theme-secondary leading-relaxed">${_escapeHtml(preview)}</p>
        `;

        div.onclick = () => _loadEntry(entry);
        return div;
    }

    function _loadEntry(entry) {
        const rawText = document.getElementById("rawText");
        rawText.value = entry.input_text;

        const resultsPanel = document.getElementById("results-panel");
        const inputPanel = document.getElementById("input-panel");

        if (!resultsPanel.classList.contains("hidden")) {
            inputPanel.classList.remove("hidden");
            resultsPanel.classList.add("hidden");
        }

        close();
    }

    function _formatTime(isoString) {
        if (!isoString) return "";
        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now - date;
        const diffMin = Math.floor(diffMs / 60000);

        if (diffMin < 1) return "Just now";
        if (diffMin < 60) return `${diffMin}m ago`;

        const diffHrs = Math.floor(diffMin / 60);
        if (diffHrs < 24) return `${diffHrs}h ago`;

        return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    }

    function _escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    async function _fetchFromServer() {
        const response = await fetch("/api/history", {
            headers: Auth.authHeaders(),
        });

        if (!response.ok) throw new Error("Failed to fetch history");
        return await response.json();
    }

    async function deleteEntry(entryId) {
        try {
            await fetch(`/api/history/${entryId}`, {
                method: "DELETE",
                headers: Auth.authHeaders(),
            });
            renderPanel();
        } catch (err) {
            console.error("Failed to delete entry:", err);
        }
    }

    function addSessionEntry(actionType, inputText, outputText) {
        SessionHistory.add(actionType, inputText, outputText);

        if (_isOpen) renderPanel();
    }

    async function onLogin() {
        const sessionEntries = SessionHistory.getAll();

        if (sessionEntries.length > 0) {
            try {
                await fetch("/api/history/bulk", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        ...Auth.authHeaders(),
                    },
                    body: JSON.stringify(sessionEntries),
                });
                SessionHistory.clear();
            } catch (err) {
                console.error("Failed to upload session history:", err);
            }
        }

        if (_isOpen) renderPanel();
    }

    function onLogout() {
        SessionHistory.clear();
        if (_isOpen) renderPanel();
    }

    return { init, toggle, close, renderPanel, deleteEntry, addSessionEntry, onLogin, onLogout };
})();


document.addEventListener("DOMContentLoaded", () => History.init());
