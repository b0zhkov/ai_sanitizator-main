/**
 * OCR module — image upload, preview, paste handling, and textarea locking.
 *
 * Provides the bridge between image input (button / camera / Ctrl+V paste)
 * and the existing text-processing pipeline.
 */

const OCR = {
    _objectUrl: null,
    _loading: false,

    async handleFile(file) {
        if (!file || !file.type.startsWith('image/')) return;

        const allowed = ['image/png', 'image/jpeg', 'image/webp'];
        if (!allowed.includes(file.type)) {
            alert('Unsupported image type. Please use PNG, JPEG, or WebP.');
            return;
        }

        this.setPreview(file);
        this.setLoading(true);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/ocr', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorBody = await response.text();
                let errorMsg = 'OCR failed';
                try { const parsed = JSON.parse(errorBody); errorMsg = parsed.detail || errorMsg; } catch (_) { errorMsg = errorBody || errorMsg; }
                throw new Error(errorMsg);
            }

            const data = await response.json();
            const textarea = document.getElementById('rawText');
            textarea.value = data.content;
            textarea.dispatchEvent(new Event('input'));

            if (!data.content) {
                this._showWarning('No text detected in the image.');
            }
        } catch (err) {
            alert('Error extracting text: ' + err.message);
            this.clearPreview();
        } finally {
            this.setLoading(false);
        }
    },

    setPreview(file) {
        if (this._objectUrl) URL.revokeObjectURL(this._objectUrl);

        this._objectUrl = URL.createObjectURL(file);

        const img = document.getElementById('ocrPreviewImg');
        const name = document.getElementById('ocrPreviewName');
        const container = document.getElementById('ocrPreview');

        img.src = this._objectUrl;
        name.textContent = file.name || 'Pasted image';
        container.classList.remove('hidden');

        this.lockTextarea();
    },

    clearPreview() {
        if (this._objectUrl) {
            URL.revokeObjectURL(this._objectUrl);
            this._objectUrl = null;
        }

        const container = document.getElementById('ocrPreview');
        const img = document.getElementById('ocrPreviewImg');

        if (container) container.classList.add('hidden');
        if (img) img.src = '';

        this.unlockTextarea();

        const input = document.getElementById('ocrFileInput');
        if (input) input.value = '';
    },

    lockTextarea() {
        const ta = document.getElementById('rawText');
        if (!ta) return;
        ta.readOnly = true;
        ta.classList.add('textarea-locked');
    },

    unlockTextarea() {
        const ta = document.getElementById('rawText');
        if (!ta) return;
        ta.readOnly = false;
        ta.classList.remove('textarea-locked');
    },

    setLoading(on) {
        this._loading = on;

        const status = document.getElementById('ocrStatus');
        if (status) status.classList.toggle('hidden', !on);

        document.querySelectorAll('#input-panel button[onclick^="processText"]')
            .forEach(btn => {
                btn.disabled = on;
                btn.classList.toggle('opacity-50', on);
                btn.classList.toggle('pointer-events-none', on);
            });
    },

    _showWarning(message) {
        const status = document.getElementById('ocrStatus');
        if (!status) return;
        status.classList.remove('hidden');
        status.innerHTML = `
            <span class="material-symbols-outlined text-amber-400 text-[18px]">warning</span>
            <span class="text-xs text-amber-400 font-medium">${message}</span>
        `;
        setTimeout(() => status.classList.add('hidden'), 4000);
    },
};


document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('ocrFileInput');
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) OCR.handleFile(file);
        });
    }

    // --- Ctrl+V paste handler (Phase 5) ---
    document.addEventListener('paste', (e) => {
        const items = e.clipboardData && e.clipboardData.items;
        if (!items) return;

        for (const item of items) {
            if (item.type.startsWith('image/')) {
                e.preventDefault();
                const file = item.getAsFile();
                if (file) OCR.handleFile(file);
                return;
            }
        }
    });
});
