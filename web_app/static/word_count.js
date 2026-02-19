const WordCount = {
    settings: {
        inputSelector: '#rawText',

        wordCountId: 'wordCount',
        charCountId: 'charCount'
    },

    init() {
        this.inputElement = document.querySelector(this.settings.inputSelector);
        if (!this.inputElement) return;

        this.inputElement.addEventListener('input', () => this.update());

        this.update();
    },

    update() {
        if (!this.inputElement) return;

        const text = this.inputElement.value || '';
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