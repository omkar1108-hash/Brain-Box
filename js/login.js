function login() {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const error = document.getElementById("error");

    error.textContent = "";

    fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            localStorage.setItem("user_id", data.user_id);
            window.location.href = "/notes-dashboard";
        } else {
            error.textContent = data.error;
        }
    })
    .catch(() => error.textContent = "Server error");
}
