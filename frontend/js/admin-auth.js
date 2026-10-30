const ADMIN_API = "http://127.0.0.1:5000/api";


async function adminApi(endpoint, options = {}) {

    const config = {
        credentials: "include",
        ...options
    };

    if (
        config.body &&
        typeof config.body === "object" &&
        !(config.body instanceof FormData)
    ) {
        config.headers = {
            ...(config.headers || {}),
            "Content-Type": "application/json"
        };

        config.body = JSON.stringify(config.body);
    }

    const response = await fetch(
        ADMIN_API + endpoint,
        config
    );

    let data = {};

    try {
        data = await response.json();
    } catch {
        data = {};
    }

    if (!response.ok) {
        throw new Error(
            data.message || "Request failed."
        );
    }

    return data;
}


function adminToast(message, type = "success") {

    document.querySelector(".toast")?.remove();

    const toast = document.createElement("div");

    toast.className =
        "toast" +
        (type === "error" ? " error" : "");

    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(
        () => toast.remove(),
        3500
    );
}


document.addEventListener(
    "DOMContentLoaded",
    async () => {

        const form =
            document.getElementById(
                "adminLoginForm"
            );

        if (!form) {
            return;
        }


        /*
            Already logged in as admin?
        */

        try {

            const me =
                await adminApi(
                    "/auth/me"
                );

            if (
                me.user &&
                me.user.role === "admin"
            ) {

                window.location.href =
                    "admin-dashboard.html";

                return;
            }

        } catch {
            // Not logged in
        }


        /*
            ADMIN LOGIN
        */

        form.addEventListener(
            "submit",
            async (event) => {

                event.preventDefault();


                const formData =
                    new FormData(form);


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


                if (!email) {

                    adminToast(
                        "Please enter admin email.",
                        "error"
                    );

                    return;
                }


                if (!password) {

                    adminToast(
                        "Please enter admin password.",
                        "error"
                    );

                    return;
                }


                const button =
                    form.querySelector(
                        "button[type='submit']"
                    );


                button.disabled =
                    true;


                button.textContent =
                    "Logging in...";


                try {

                    const data =
                        await adminApi(
                            "/auth/login",
                            {
                                method: "POST",

                                body: {
                                    email: email,
                                    password: password
                                }
                            }
                        );


                    /*
                        Only admin allowed.
                    */

                    if (
                        !data.user ||
                        data.user.role !== "admin"
                    ) {

                        try {

                            await adminApi(
                                "/auth/logout",
                                {
                                    method: "POST"
                                }
                            );

                        } catch {}

                        throw new Error(
                            "This account is not an administrator."
                        );
                    }


                    localStorage.setItem(
                        "LOCALBIZ_USER",
                        JSON.stringify(
                            data.user
                        )
                    );


                    window.location.href =
                        "admin-dashboard.html";


                } catch (error) {

                    console.error(
                        "ADMIN LOGIN ERROR:",
                        error
                    );


                    adminToast(
                        error.message ||
                        "Admin login failed.",
                        "error"
                    );


                    button.disabled =
                        false;


                    button.textContent =
                        "Login as Admin";

                }

            }
        );

    }
);