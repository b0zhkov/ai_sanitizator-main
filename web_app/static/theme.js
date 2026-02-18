const Theme = (() => {
    const STORAGE_KEY = "sanitizator_theme";

    function _getSystemPreference() {
        return window.matchMedia("(prefers-color-scheme: light)").matches
            ? "light"
            : "dark";
    }

    function _getSavedTheme() {
        return localStorage.getItem(STORAGE_KEY);
    }

    function get() {
        return _getSavedTheme() || _getSystemPreference();
    }

    function apply(theme) {
        document.documentElement.setAttribute("data-theme", theme);
        _updateIcon(theme);
    }

    function toggle() {
        const current = get();
        const next = current === "dark" ? "light" : "dark";
        localStorage.setItem(STORAGE_KEY, next);
        apply(next);
    }

    function _updateIcon(theme) {
        const icon = document.getElementById("themeToggleIcon");
        if (!icon) return;
        icon.textContent = theme === "dark" ? "light_mode" : "dark_mode";
    }

    function init() {
        apply(get());
    }

    return { init, toggle, get, apply };
})();


Theme.init();
