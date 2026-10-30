const API = (
    localStorage.getItem("LOCALBIZ_API") ||
    "http://127.0.0.1:5000/api"
).replace(/\/$/, "");


/* =========================================================
   API REQUEST
========================================================= */

async function api(path, options = {}) {

    const config = {
        credentials: "include",
        ...options
    };

    config.headers = {
        ...(options.headers || {})
    };

    if (
        config.body &&
        typeof config.body === "object" &&
        !(config.body instanceof FormData)
    ) {

        config.headers["Content-Type"] = "application/json";

        config.body = JSON.stringify(config.body);
    }


    const response = await fetch(
        API + path,
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
            data.message || "Request failed"
        );

    }


    return data;
}


/* =========================================================
   TOAST MESSAGE
========================================================= */

function showMessage(message, type = "success") {

    const oldToast =
        document.querySelector(".toast");

    if (oldToast) {
        oldToast.remove();
    }


    const toast =
        document.createElement("div");

    toast.className =
        "toast" +
        (type === "error" ? " error" : "");


    toast.textContent =
        message;


    document.body.appendChild(toast);


    setTimeout(() => {

        toast.remove();

    }, 3500);
}


/* =========================================================
   HTML ESCAPE
========================================================= */

function esc(value) {

    return String(value ?? "")
        .replace(/[&<>"']/g, char => {

            return {

                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;"

            }[char];

        });

}


/* =========================================================
   RATING FORMAT
========================================================= */

function money(value) {

    return Number(value || 0)
        .toFixed(1);

}


/* =========================================================
   LOGOUT
========================================================= */

async function logout() {

    try {

        await api(
            "/auth/logout",
            {
                method: "POST"
            }
        );

    } catch (error) {

        console.log(error);

    }


    /*
        Force navbar to logged-out state
    */

    localStorage.removeItem(
        "LOCALBIZ_USER"
    );


    window.location.href =
        "login.html";
}


/* =========================================================
   GET DASHBOARD URL
========================================================= */

function getDashboardURL(role) {

    if (role === "admin") {

        return "admin-dashboard.html";

    }

    if (role === "business_owner") {

        return "owner-dashboard.html";

    }

    return "index.html";
}


/* =========================================================
   UPDATE NAVBAR
========================================================= */

async function updateNavbar() {

    const navActions =
        document.querySelector(".nav-actions");


    /*
        Some pages don't have normal navbar actions.
    */

    if (!navActions) {

        return;

    }


    /*
        Check current login session
    */

    try {

        const response =
            await api("/auth/me");


        if (
            !response ||
            !response.user
        ) {

            /*
                User is NOT logged in
            */

            showLoggedOutNavbar();

            return;

        }


        /*
            User IS logged in
        */

        const user =
            response.user;


        /*
            Save small copy locally
            for UI only.
        */

        localStorage.setItem(
            "LOCALBIZ_USER",
            JSON.stringify(user)
        );


        showLoggedInNavbar(user);


    } catch (error) {

        /*
            401 means user isn't logged in.

            Don't show an error toast here because
            this request runs on every public page.
        */

        showLoggedOutNavbar();

    }

}


/* =========================================================
   LOGGED OUT NAVBAR
========================================================= */

function showLoggedOutNavbar() {

    const navActions =
        document.querySelector(".nav-actions");


    if (!navActions) {

        return;

    }


    navActions.innerHTML = `

        <a
            class="btn btn-outline"
            href="login.html"
        >
            Login
        </a>

        <a
            class="btn btn-primary"
            href="register.html"
        >
            Register
        </a>

    `;


}


/* =========================================================
   LOGGED IN NAVBAR
========================================================= */

function showLoggedInNavbar(user) {

    const navActions =
        document.querySelector(".nav-actions");


    if (!navActions) {

        return;

    }


    const dashboardURL =
        getDashboardURL(user.role);


    navActions.innerHTML = `

        <span
            class="nav-user"
            style="
                font-weight:700;
                color:#334155;
                display:flex;
                align-items:center;
                gap:8px;
            "
        >
            👋 ${esc(user.name)}
        </span>

        <a
            class="btn btn-outline"
            href="${dashboardURL}"
        >
            Dashboard
        </a>

        <button
            class="btn btn-primary"
            id="dynamicLogoutBtn"
            type="button"
        >
            Logout
        </button>

    `;


    const logoutButton =
        document.getElementById(
            "dynamicLogoutBtn"
        );


    if (logoutButton) {

        logoutButton.addEventListener(
            "click",
            async () => {

                logoutButton.disabled =
                    true;

                logoutButton.textContent =
                    "Logging out...";


                await logout();

            }
        );

    }

}


/* =========================================================
   CURRENT PAGE LOGOUT BUTTON
========================================================= */

function setupStaticLogoutButtons() {

    document
        .querySelectorAll("[data-logout]")
        .forEach(button => {

            button.addEventListener(
                "click",
                event => {

                    event.preventDefault();

                    logout();

                }
            );

        });

}


/* =========================================================
   YEAR
========================================================= */

function setupYear() {

    document
        .querySelectorAll("[data-year]")
        .forEach(element => {

            element.textContent =
                new Date()
                    .getFullYear();

        });

}


/* =========================================================
   PAGE LOAD
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    async () => {

        setupYear();

        setupStaticLogoutButtons();

        /*
            Automatically detect logged-in user
            and change navbar.
        */

        await updateNavbar();

    }
);


/* =========================================================
   GLOBAL EXPORTS
========================================================= */

window.API =
    API;

window.api =
    api;

window.showMessage =
    showMessage;

window.esc =
    esc;

window.money =
    money;

window.logout =
    logout;

window.updateNavbar =
    updateNavbar;