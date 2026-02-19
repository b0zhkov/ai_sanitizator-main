const WordCount = {
    settings: {
        inputSelector: '#rawText',
        displaySelector: '#wordCountDisplay',
        wordCountId: 'wordCount',
        charCountId: 'charCount'
    },

    init() {
        const inputElement = document.querySelector(this.settings.inputSelector);
        if (!inputElement) return;

        inputElement.addEventListener('input', () => this.update());

        this.update();
    },

    update() {
        const inputElement = document.querySelector(this.settings.inputSelector);
        if (!inputElement) return;

        const text = inputElement.value || '';
        const wordCount = this.countWords(text);
        const charCount = text.length;

        const wordCountElement = document.getElementById(this.settings.wordCountId);
        const charCountElement = document.getElementById(this.settings.charCountId);

        if (wordCountElement) wordCountElement.textContent = wordCount;
        if (charCountElement) charCountElement.textContent = charCount;
    },

    countWords(text) {
        if (!text) return 0;
        return text.trim().split(/\s+/).filter(word => word.length > 0).length;
    }
};
document.addEventListener('DOMContentLoaded', () => {
    WordCount.init();
});