document.addEventListener("DOMContentLoaded", () => {

    // =====================================================
    // REGISTRATION STATE
    // =====================================================

    let registrationEmail = "";


    // =====================================================
    // PASSWORD RESET STATE
    // =====================================================

    let resetEmail = "";


    // =====================================================
    // NORMAL LOGIN
    // Customer / Business Owner only
    // =====================================================

    const loginForm =
        document.getElementById("loginForm");


    if (loginForm) {

        loginForm.addEventListener(
            "submit",
            async (event) => {

                event.preventDefault();


                const formData =
                    new FormData(loginForm);


                const email =
                    (formData.get("email") || "")
                        .trim()
                        .toLowerCase();


                const password =
                    formData.get("password") || "";


                const button =
                    loginForm.querySelector(
                        "button[type='submit']"
                    );


                if (!email) {

                    showMessage(
                        "Please enter your email.",
                        "error"
                    );

                    return;

                }


                if (!password) {

                    showMessage(
                        "Please enter your password.",
                        "error"
                    );

                    return;

                }


                button.disabled = true;

                button.textContent =
                    "Logging in...";


                try {

                    const data =
                        await api(
                            "/auth/login",
                            {
                                method: "POST",

                                body: {
                                    email: email,
                                    password: password
                                }
                            }
                        );


                    // =====================================
                    // ADMIN BLOCK
                    // =====================================

                    if (
                        data.user &&
                        data.user.role === "admin"
                    ) {

                        try {

                            await api(
                                "/auth/logout",
                                {
                                    method: "POST"
                                }
                            );

                        } catch {
                            // Ignore logout cleanup error
                        }


                        throw new Error(
                            "Admin accounts must use Administrator Login."
                        );

                    }


                    // =====================================
                    // SAVE USER
                    // =====================================

                    localStorage.setItem(
                        "LOCALBIZ_USER",
                        JSON.stringify(
                            data.user
                        )
                    );


                    showMessage(
                        "Login successful."
                    );


                    // =====================================
                    // REDIRECT
                    // =====================================

                    setTimeout(
                        () => {

                            if (
                                data.user.role ===
                                "business_owner"
                            ) {

                                window.location.href =
                                    "owner-dashboard.html";

                            } else {

                                window.location.href =
                                    "index.html";

                            }

                        },
                        500
                    );


                } catch (error) {

                    console.error(
                        "LOGIN ERROR:",
                        error
                    );


                    showMessage(
                        error.message ||
                        "Login failed.",
                        "error"
                    );


                    button.disabled =
                        false;


                    button.textContent =
                        "Login";

                }

            }
        );

    }


    // =====================================================
    // REGISTER
    // Step 1:
    // Send OTP
    // =====================================================

    const registerForm =
        document.getElementById(
            "registerForm"
        );


    const otpForm =
        document.getElementById(
            "otpForm"
        );


    if (registerForm) {

        registerForm.addEventListener(
            "submit",
            async (event) => {

                event.preventDefault();


                const formData =
                    new FormData(
                        registerForm
                    );


                const name =
                    (
                        formData.get(
                            "name"
                        ) || ""
                    ).trim();


                const phone =
                    (
                        formData.get(
                            "phone"
                        ) || ""
                    ).trim();


                const email =
                    (
                        formData.get(
                            "email"
                        ) || ""
                    )
                    .trim()
                    .toLowerCase();


                const password =
                    formData.get(
                        "password"
                    ) || "";


                const confirmPassword =
                    formData.get(
                        "confirmPassword"
                    ) || "";


                const role =
                    formData.get(
                        "role"
                    ) || "user";


                const button =
                    registerForm.querySelector(
                        "button[type='submit']"
                    );


                // =====================================
                // VALIDATION
                // =====================================

                if (!name) {

                    showMessage(
                        "Please enter your name.",
                        "error"
                    );

                    return;

                }


                if (!email) {

                    showMessage(
                        "Please enter your email.",
                        "error"
                    );

                    return;

                }


                if (
                    password.length < 6
                ) {

                    showMessage(
                        "Password must be at least 6 characters.",
                        "error"
                    );

                    return;

                }


                if (
                    password !==
                    confirmPassword
                ) {

                    showMessage(
                        "Passwords do not match.",
                        "error"
                    );

                    return;

                }


                // =====================================
                // SEND OTP
                // =====================================

                button.disabled =
                    true;


                button.textContent =
                    "Sending OTP...";


                try {

                    console.log(
                        "Sending registration request:",
                        email
                    );


                    const data =
                        await api(
                            "/auth/register",
                            {
                                method: "POST",

                                body: {

                                    name:
                                        name,

                                    phone:
                                        phone,

                                    email:
                                        email,

                                    password:
                                        password,

                                    role:
                                        role

                                }
                            }
                        );


                    console.log(
                        "Registration response:",
                        data
                    );


                    registrationEmail =
                        data.email ||
                        email;


                    // =====================================
                    // HIDE REGISTER
                    // SHOW OTP
                    // =====================================

                    registerForm.classList.add(
                        "hidden"
                    );


                    if (otpForm) {

                        otpForm.classList.remove(
                            "hidden"
                        );

                    }


                    const otpInput =
                        document.getElementById(
                            "registrationOtp"
                        );


                    if (otpInput) {

                        otpInput.value = "";

                        otpInput.focus();

                    }


                    showMessage(
                        "Verification OTP sent to your email."
                    );


                } catch (error) {

                    console.error(
                        "REGISTRATION ERROR:",
                        error
                    );


                    if (
                        error.message ===
                        "Failed to fetch"
                    ) {

                        showMessage(
                            "Cannot connect to backend. Make sure Flask is running on port 5000.",
                            "error"
                        );

                    } else {

                        showMessage(
                            error.message ||
                            "Unable to send verification OTP.",
                            "error"
                        );

                    }

                } finally {

                    button.disabled =
                        false;


                    button.textContent =
                        "Send Verification OTP";

                }

            }
        );

    }


    // =====================================================
    // VERIFY REGISTRATION OTP
    // Step 2:
    // Only after OTP verification user is created
    // =====================================================

    if (otpForm) {

        otpForm.addEventListener(
            "submit",
            async (event) => {

                event.preventDefault();


                const otpInput =
                    document.getElementById(
                        "registrationOtp"
                    );


                const otp =
                    (
                        otpInput?.value ||
                        ""
                    ).trim();


                if (
                    !registrationEmail
                ) {

                    showMessage(
                        "Registration session expired. Please register again.",
                        "error"
                    );

                    return;

                }


                if (
                    !/^\d{6}$/.test(
                        otp
                    )
                ) {

                    showMessage(
                        "Please enter a valid 6-digit OTP.",
                        "error"
                    );

                    return;

                }


                const button =
                    otpForm.querySelector(
                        "button[type='submit']"
                    );


                button.disabled =
                    true;


                button.textContent =
                    "Verifying...";


                try {

                    const data =
                        await api(
                            "/auth/verify-registration",
                            {
                                method: "POST",

                                body: {

                                    email:
                                        registrationEmail,

                                    otp:
                                        otp

                                }
                            }
                        );


                    // =====================================
                    // ACCOUNT CREATED
                    // =====================================

                    localStorage.setItem(
                        "LOCALBIZ_USER",
                        JSON.stringify(
                            data.user
                        )
                    );


                    showMessage(
                        "Email verified and account created successfully."
                    );


                    // =====================================
                    // REDIRECT
                    // =====================================

                    setTimeout(
                        () => {

                            if (
                                data.user.role ===
                                "business_owner"
                            ) {

                                window.location.href =
                                    "owner-dashboard.html";

                            } else {

                                window.location.href =
                                    "index.html";

                            }

                        },
                        700
                    );


                } catch (error) {

                    console.error(
                        "OTP VERIFICATION ERROR:",
                        error
                    );


                    showMessage(
                        error.message ||
                        "OTP verification failed.",
                        "error"
                    );


                    button.disabled =
                        false;


                    button.textContent =
                        "Verify Email & Create Account";

                }

            }
        );

    }


    // =====================================================
    // CHANGE EMAIL
    // =====================================================

    const changeEmailBtn =
        document.getElementById(
            "changeEmailBtn"
        );


    if (changeEmailBtn) {

        changeEmailBtn.addEventListener(
            "click",
            () => {

                registrationEmail =
                    "";


                if (otpForm) {

                    otpForm.classList.add(
                        "hidden"
                    );

                }


                if (registerForm) {

                    registerForm.classList.remove(
                        "hidden"
                    );

                }


                const otpInput =
                    document.getElementById(
                        "registrationOtp"
                    );


                if (otpInput) {

                    otpInput.value = "";

                }

            }
        );

    }


    // =====================================================
    // FORGOT PASSWORD
    // Step 1:
    // Send reset OTP
    // =====================================================

    const forgotForm =
        document.getElementById(
            "forgotForm"
        );


    const resetForm =
        document.getElementById(
            "resetForm"
        );


    if (forgotForm) {

        forgotForm.addEventListener(
            "submit",
            async (event) => {

                event.preventDefault();


                const formData =
                    new FormData(
                        forgotForm
                    );


                resetEmail =
                    (
                        formData.get(
                            "email"
                        ) || ""
                    )
                    .trim()
                    .toLowerCase();


                if (!resetEmail) {

                    showMessage(
                        "Please enter your email.",
                        "error"
                    );

                    return;

                }


                const button =
                    forgotForm.querySelector(
                        "button[type='submit']"
                    );


                button.disabled =
                    true;


                button.textContent =
                    "Sending OTP...";


                try {

                    await api(
                        "/auth/forgot-password",
                        {
                            method: "POST",

                            body: {

                                email:
                                    resetEmail

                            }

                        }
                    );


                    forgotForm.classList.add(
                        "hidden"
                    );


                    if (resetForm) {

                        resetForm.classList.remove(
                            "hidden"
                        );

                    }


                    const otp =
                        resetForm?.querySelector(
                            "input[name='otp']"
                        );


                    if (otp) {

                        otp.focus();

                    }


                    showMessage(
                        "Password reset OTP sent to your email."
                    );


                } catch (error) {

                    console.error(
                        "FORGOT PASSWORD ERROR:",
                        error
                    );


                    showMessage(
                        error.message ||
                        "Unable to send reset OTP.",
                        "error"
                    );


                } finally {

                    button.disabled =
                        false;


                    button.textContent =
                        "Send OTP";

                }

            }
        );

    }


    // =====================================================
    // RESET PASSWORD
    // Step 2:
    // Verify OTP + change password
    // =====================================================

    if (resetForm) {

        resetForm.addEventListener(
            "submit",
            async (event) => {

                event.preventDefault();


                const formData =
                    new FormData(
                        resetForm
                    );


                const otp =
                    (
                        formData.get(
                            "otp"
                        ) || ""
                    ).trim();


                const newPassword =
                    formData.get(
                        "new_password"
                    ) || "";


                const confirmPassword =
                    formData.get(
                        "confirm_password"
                    ) || "";


                if (!resetEmail) {

                    showMessage(
                        "Please request a password reset OTP first.",
                        "error"
                    );

                    return;

                }


                if (
                    !/^\d{6}$/.test(
                        otp
                    )
                ) {

                    showMessage(
                        "Please enter a valid 6-digit OTP.",
                        "error"
                    );

                    return;

                }


                if (
                    newPassword.length < 6
                ) {

                    showMessage(
                        "Password must be at least 6 characters.",
                        "error"
                    );

                    return;

                }


                if (
                    newPassword !==
                    confirmPassword
                ) {

                    showMessage(
                        "Passwords do not match.",
                        "error"
                    );

                    return;

                }


                const button =
                    resetForm.querySelector(
                        "button[type='submit']"
                    );


                button.disabled =
                    true;


                button.textContent =
                    "Resetting...";


                try {

                    await api(
                        "/auth/reset-password",
                        {
                            method: "POST",

                            body: {

                                email:
                                    resetEmail,

                                otp:
                                    otp,

                                new_password:
                                    newPassword

                            }

                        }
                    );


                    showMessage(
                        "Password reset successfully."
                    );


                    setTimeout(
                        () => {

                            window.location.href =
                                "login.html";

                        },
                        800
                    );


                } catch (error) {

                    console.error(
                        "PASSWORD RESET ERROR:",
                        error
                    );


                    showMessage(
                        error.message ||
                        "Password reset failed.",
                        "error"
                    );


                } finally {

                    button.disabled =
                        false;


                    button.textContent =
                        "Reset Password";

                }

            }
        );

    }

});