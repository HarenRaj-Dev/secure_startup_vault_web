function toggleAuth() {
    const subtitle = document.getElementById('auth-subtitle');
    const toggleLink = document.getElementById('toggle-msg');
    const authForm = document.getElementById('auth-form');
    const submitBtn = document.getElementById('submit-btn');
    const title = document.querySelector('.auth-header h2');
    const confirmGroup = document.getElementById('confirm-pass-group');
    const confirmInput = document.getElementById('confirm_field');

    // Check if we are currently in Login mode (default)
    const isLoginMode = submitBtn.innerText.trim() === "Login";

    if (isLoginMode) {
        // Switch to Register Mode
        if (title) title.innerText = "CREATE ACCOUNT";
        if (subtitle) subtitle.innerText = "Join the most secure vault for your startup.";

        // Update Link
        if (toggleLink) {
            toggleLink.innerHTML = 'Already have an account? <a href="javascript:void(0)" onclick="toggleAuth()">Login</a>';
        }

        // Update Form
        if (authForm) authForm.action = "/register";
        if (submitBtn) submitBtn.innerText = "Create Account";

        // Show Confirm Password
        if (confirmGroup) {
            confirmGroup.style.display = "block";
            if (confirmInput) confirmInput.setAttribute('required', 'required');
        }

    } else {
        // Switch back to Login Mode
        location.reload();
    }
}

function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const btn = event.currentTarget || event.target; // handle both click targets

    if (input.type === "password") {
        input.type = "text";
        btn.innerText = "HIDE";
    } else {
        input.type = "password";
        btn.innerText = "SHOW";
    }
}