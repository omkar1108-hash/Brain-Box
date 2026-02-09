const USER_ID = localStorage.getItem("user_id");
if (!USER_ID) {
    window.location.href = "/login";
}

window.onload = () => {
    fetch(`/task-series-categories?user_id=${USER_ID}`)
        .then(res => res.json())
        .then(categories => {
            const select = document.getElementById("categorySelect");
            if (!select) return;

            categories.forEach(cat => {
                const opt = document.createElement("option");
                opt.value = cat;
                opt.textContent = cat;
                select.appendChild(opt);
            });
        })
        .catch(err => console.error("Series category load error:", err));
};

const params = new URLSearchParams(window.location.search);
const seriesId = params.get("id");

document.addEventListener("DOMContentLoaded", loadSeries);

/* ===============================
   LOAD SERIES  🔐 user_id added
   =============================== */
function loadSeries() {
    fetch(`/task-series/${seriesId}?user_id=${USER_ID}`)
        .then(res => res.json())
        .then(series => {
            seriesTitle.value = series.title;

            series.tasks.forEach(t => {
                addTask(t);
            });

            // ✅ initial progress
            updateProgressBar();
        });
}

/* ===============================
   ADD TASK ROW
   =============================== */
function addTask(task = {}) {

    const row = document.createElement("div");
    row.className = "task-row";

    row.innerHTML = `
        <input type="checkbox"
               class="task-status"
               ${task.status === "completed" ? "checked" : ""}>

        <input type="text" class="task-title" value="${task.title || ""}">
        <textarea class="task-desc">${task.description || ""}</textarea>
        <input type="date" class="task-due" value="${task.due_date || ""}">
        <input type="range" class="task-priority" min="0" max="10"
               value="${task.priority ?? 0}">
        <input type="range" class="task-difficulty" min="0" max="10"
               value="${task.difficulty ?? 0}">
        <button class="remove-btn">✕</button>
    `;

    // update progress when checkbox toggled
    row.querySelector(".task-status").onchange = updateProgressBar;

    // delete task row (UI only)
    row.querySelector(".remove-btn").onclick = () => {
        row.remove();
        updateProgressBar();
    };

    document.getElementById("taskList").appendChild(row);

    updateProgressBar();
}

/* ===============================
   BACK
   =============================== */
function goBack() {
    window.location.href = "/task-dashboard";
}

/* ===============================
   PROGRESS BAR
   =============================== */
function updateProgressBar() {
    const rows = document.querySelectorAll(".task-row");
    const total = rows.length;

    if (total === 0) {
        progressBar.style.width = "0%";
        progressText.innerText = "0%";
        return;
    }

    let completed = 0;
    rows.forEach(row => {
        if (row.querySelector(".task-status").checked) {
            completed++;
        }
    });

    const percent = Math.round((completed / total) * 100);

    progressBar.style.width = percent + "%";
    progressText.innerText = percent + "%";
}

/* ===============================
   UPDATE SERIES  🔐 user_id added
   =============================== */
function updateSeries() {
    const tasks = [];

    document.querySelectorAll(".task-row").forEach(row => {
        tasks.push({
            title: row.querySelector(".task-title").value.trim(),
            description: row.querySelector(".task-desc").value.trim(),
            due_date: row.querySelector(".task-due").value || null,
            priority: parseInt(row.querySelector(".task-priority").value, 10),
            difficulty: parseInt(row.querySelector(".task-difficulty").value, 10),
            status: row.querySelector(".task-status").checked
                ? "completed"
                : "pending"
        });
    });

    fetch("/update-task-series", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user_id: USER_ID,      // 🔐 ADDED
            id: seriesId,          // 🔑 MUST be "id"
            title: seriesTitle.value.trim(),
            tasks: tasks
        })
    })
    .then(res => {
        if (!res.ok) throw new Error("Update failed");
        return res.json();
    })
    .then(() => {
        window.location.replace("/task-dashboard");
    })
    .catch(err => {
        console.error(err);
        alert("❌ Failed to update task series");
    });
}
