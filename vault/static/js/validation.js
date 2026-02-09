document.addEventListener('DOMContentLoaded', function() {
    const authForm = document.getElementById('auth-form');
    const emailInput = document.getElementById('email_field');
    const passwordInput = document.getElementById('pass_field');
    const submitBtn = document.getElementById('submit-btn');

    if (authForm) {
        authForm.addEventListener('submit', function(event) {
            // Only validate on Register mode
            if (submitBtn.innerText.toLowerCase().includes('register') || submitBtn.innerText.toLowerCase().includes('create account')) {
                let isValid = true;
                let errorMsg = "";

                // Email Validation
                const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
                if (!emailRegex.test(emailInput.value)) {
                    isValid = false;
                    errorMsg += "Invalid email format.\n";
                }

                // Password Validation
                // 8 chars, letter + number
                const pass = passwordInput.value;
                if (pass.length < 8) {
                    isValid = false;
                    errorMsg += "Password must be at least 8 characters.\n";
                }
                if (!/[a-zA-Z]/.test(pass) || !/[0-9]/.test(pass)) {
                    isValid = false;
                    errorMsg += "Password must contain both letters and numbers.\n";
                }

                if (!isValid) {
                    event.preventDefault();
                    alert(errorMsg); // Simple alert for now, or use a custom UI element
                }
            }
        });
    }
});
