const Auth = (() => {
    const TOKEN_KEY = "sanitizator_token";
    const EMAIL_KEY = "sanitizator_email";

    function getToken() {
        return localStorage.getItem(TOKEN_KEY);
    }

    function getEmail() {
        return localStorage.getItem(EMAIL_KEY);
    }

    function isLoggedIn() {
        return !!getToken();
    }

    function _saveSession(token, email) {
        localStorage.setItem(TOKEN_KEY, token);
        localStorage.setItem(EMAIL_KEY, email);
    }

    function _clearSession() {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(EMAIL_KEY);
    }

    function authHeaders() {
        const token = getToken();
        if (!token) return {};
        return { Authorization: `Bearer ${token}` };
    }

    async function register(email, password) {
        const response = await fetch("/api/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Registration failed");
        }

        _saveSession(data.token, data.email);
        return data;
    }

    async function login(email, password) {
        const response = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Login failed");
        }

        _saveSession(data.token, data.email);
        return data;
    }

    function logout() {
        _clearSession();
    }

    return { getToken, getEmail, isLoggedIn, authHeaders, register, login, logout };
})();


const AuthUI = (() => {
    let _modal = null;
    let _isRegisterMode = false;

    function init() {
        _modal = document.getElementById("authModal");
        _updateNavbar();
    }

    function _updateNavbar() {
        const authBtn = document.getElementById("authNavBtn");
        const authLabel = document.getElementById("authNavLabel");
        const logoutBtn = document.getElementById("logoutBtn");

        if (Auth.isLoggedIn()) {
            authLabel.textContent = Auth.getEmail();
            authBtn.onclick = null;
            logoutBtn.classList.remove("hidden");
        } else {
            authLabel.textContent = "Sign In";
            authBtn.onclick = () => openModal();
            logoutBtn.classList.add("hidden");
        }
    }

    function openModal() {
        _isRegisterMode = false;
        _resetForm();
        _modal.classList.remove("hidden");
    }

    function closeModal() {
        _modal.classList.add("hidden");
        _clearError();
    }

    function toggleMode() {
        _isRegisterMode = !_isRegisterMode;
        _resetForm();
    }

    function _resetForm() {
        const title = document.getElementById("authModalTitle");
        const submitBtn = document.getElementById("authSubmitBtn");
        const toggleText = document.getElementById("authToggleText");

        title.textContent = _isRegisterMode ? "Create Account" : "Welcome Back";
        submitBtn.textContent = _isRegisterMode ? "Register" : "Sign In";
        toggleText.innerHTML = _isRegisterMode
            ? 'Already have an account? <button class="text-blue-400 hover:text-blue-300 font-medium" onclick="AuthUI.toggleMode()">Sign In</button>'
            : 'No account? <button class="text-blue-400 hover:text-blue-300 font-medium" onclick="AuthUI.toggleMode()">Register</button>';

        document.getElementById("authEmail").value = "";
        document.getElementById("authPassword").value = "";
        _clearError();
    }

    function _showError(message) {
        const el = document.getElementById("authError");
        el.textContent = message;
        el.classList.remove("hidden");
    }

    function _clearError() {
        const el = document.getElementById("authError");
        el.textContent = "";
        el.classList.add("hidden");
    }

    async function handleSubmit() {
        const email = document.getElementById("authEmail").value.trim();
        const password = document.getElementById("authPassword").value;

        if (!email || !password) {
            _showError("Please fill in all fields");
            return;
        }

        const submitBtn = document.getElementById("authSubmitBtn");
        submitBtn.disabled = true;
        submitBtn.textContent = "Please wait...";

        try {
            if (_isRegisterMode) {
                await Auth.register(email, password);
            } else {
                await Auth.login(email, password);
            }

            closeModal();
            _updateNavbar();
            await History.onLogin();
        } catch (err) {
            _showError(err.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = _isRegisterMode ? "Register" : "Sign In";
        }
    }

    function handleLogout() {
        Auth.logout();
        _updateNavbar();
        History.onLogout();
    }

    return { init, openModal, closeModal, toggleMode, handleSubmit, handleLogout };
})();


document.addEventListener("DOMContentLoaded", () => AuthUI.init());
