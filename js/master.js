document.addEventListener("DOMContentLoaded", () => {
    fetch("../html/master.html")
        .then(res => res.text())
        .then(html => {
            document.getElementById("master-container").innerHTML = html;
            applyAuthUI();
        });
});

/* =====================================================
   AUTH UI CONTROL
   ===================================================== */
function applyAuthUI() {
    const userId = localStorage.getItem("user_id");

    const loginBtn = document.getElementById("loginBtn");
    const registerBtn = document.getElementById("registerBtn");
    const logoutBtn = document.getElementById("logoutBtn");

    const authLinks = document.querySelectorAll(".auth-only");

    if (userId) {
        // ✅ LOGGED IN
        if (loginBtn) loginBtn.style.display = "none";
        if (registerBtn) registerBtn.style.display = "none";
        if (logoutBtn) logoutBtn.style.display = "inline-block";

        authLinks.forEach(link => {
            link.style.display = "inline-block";
        });

    } else {
        // ❌ NOT LOGGED IN
        authLinks.forEach(link => {
            link.style.display = "none";
        });

        if (logoutBtn) logoutBtn.style.display = "none";
    }
}

/* =====================================================
   LOGOUT
   ===================================================== */
function logout() {
    localStorage.clear();
    window.location.href = "/login";
}
