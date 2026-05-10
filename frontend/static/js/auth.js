document.addEventListener('DOMContentLoaded', () => {
    const authForm = document.getElementById('auth-form');
    const authModeToggle = document.getElementById('auth-mode-toggle');
    const authTitle = document.getElementById('auth-title');
    const authSubtitle = document.getElementById('auth-subtitle');
    const signupFields = document.getElementById('signup-fields');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');
    const authAlert = document.getElementById('auth-alert');
    const footerText = document.getElementById('footer-text');

    let isLoginMode = true;

    authModeToggle.addEventListener('click', () => {
        isLoginMode = !isLoginMode;
        
        if (isLoginMode) {
            authTitle.innerText = "Welcome Back";
            authSubtitle.innerText = "Enter your credentials to access the workspace.";
            signupFields.style.display = "none";
            btnText.innerText = "Sign In";
            footerText.innerText = "Don't have an account?";
            authModeToggle.innerText = "Create Account";
            document.getElementById('email').required = false;
        } else {
            authTitle.innerText = "Create Account";
            authSubtitle.innerText = "Join the cognitive workspace and start building.";
            signupFields.style.display = "block";
            btnText.innerText = "Get Started";
            footerText.innerText = "Already have an account?";
            authModeToggle.innerText = "Sign In instead";
            document.getElementById('email').required = true;
        }
        authAlert.style.display = "none";
    });

    authForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const email = document.getElementById('email').value;

        // UI Loading State
        btnText.style.display = "none";
        btnSpinner.style.display = "block";
        submitBtn.disabled = true;
        authAlert.style.display = "none";

        try {
            if (isLoginMode) {
                // Login Flow
                const formData = new FormData();
                formData.append('username', username);
                formData.append('password', password);

                const response = await fetch(`${window.BACKEND_URL}/auth/login`, {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    localStorage.setItem('apj_auth_token', data.access_token);
                    localStorage.setItem('apj_username', data.username);
                    window.location.href = "/";
                } else {
                    const error = await response.json();
                    let message = "Invalid username or password";
                    if (error.detail) {
                        if (Array.isArray(error.detail)) {
                            message = error.detail.map(err => err.msg).join(", ");
                        } else {
                            message = error.detail;
                        }
                    }
                    showAlert(message);
                }
            } else {
                // Signup Flow
                const response = await fetch(`${window.BACKEND_URL}/auth/signup`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email, password })
                });

                if (response.ok) {
                    // Auto-login after signup
                    isLoginMode = true;
                    authModeToggle.click();
                    showAlert("Account created! Please sign in.", "success");
                } else {
                    const error = await response.json();
                    let message = "Failed to create account";
                    if (error.detail) {
                        if (Array.isArray(error.detail)) {
                            message = error.detail.map(err => err.msg).join(", ");
                        } else {
                            message = error.detail;
                        }
                    }
                    showAlert(message);
                }
            }
        } catch (error) {
            console.error(error);
            showAlert("Connection error. Is the backend running?");
        } finally {
            btnText.style.display = "block";
            btnSpinner.style.display = "none";
            submitBtn.disabled = false;
        }
    });

    function showAlert(message, type = "error") {
        authAlert.innerText = message;
        authAlert.style.display = "block";
        if (type === "success") {
            authAlert.style.background = "rgba(16, 185, 129, 0.1)";
            authAlert.style.borderColor = "rgba(16, 185, 129, 0.2)";
            authAlert.style.color = "#34d399";
        } else {
            authAlert.style.background = "rgba(239, 68, 68, 0.1)";
            authAlert.style.borderColor = "rgba(239, 68, 68, 0.2)";
            authAlert.style.color = "#f87171";
        }
    }
});
