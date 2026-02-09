const USER_ID = localStorage.getItem("user_id");
if (!USER_ID) {
    window.location.href = "/login";
}

/* =====================================================
   GLOBAL STATE
   ===================================================== */
let currentCategory = "All";
let currentStatus = "all";

/* =====================================================
   ON LOAD
   ===================================================== */
window.onload = () => {
    loadTaskCategories();
    loadTasks("All");
};

/* =====================================================
   NAVIGATION
   ===================================================== */
function goToCreateTask() {
    window.location.href = "/task-create";
}

function goToCreateSeries() {
    window.location.href = "/task-series-create";
}

/* =====================================================
   CATEGORY FILTERS
   ===================================================== */
function loadTaskCategories() {
    fetch(`/task-categories?user_id=${USER_ID}`)
    
        .then(res => res.json())
        .then(categories => {
            const container = document.getElementById("categoryButtons");
            container.innerHTML = "";

            categories.forEach(cat => {
                const btn = document.createElement("button");
                btn.innerText = cat;
                btn.classList.add("filter-btn");
                if (cat === "All") btn.classList.add("active");

                btn.onclick = () => {
                    document
                        .querySelectorAll("#categoryButtons .filter-btn")
                        .forEach(b => b.classList.remove("active"));

                    btn.classList.add("active");
                    currentCategory = cat;
                    loadTasks(cat);
                };

                container.appendChild(btn);
            });
        })
        .catch(() => {
            document.getElementById("categoryButtons").innerHTML =
                "<p>Failed to load categories</p>";
        });
}

/* =====================================================
   STATUS FILTERS
   ===================================================== */
function setStatusFilter(status) {
    currentStatus = status;

    document
        .querySelectorAll("#statusFilters .filter-btn")
        .forEach(b => b.classList.remove("active"));

    event.target.classList.add("active");

    loadTasks(currentCategory);
}

/* =====================================================
   LOAD TASKS  🔐 user_id added
   ===================================================== */
function loadTasks(category = currentCategory) {
    currentCategory = category;

    fetch(`/tasks-dashboard?user_id=${USER_ID}&category=${currentCategory}&status=${currentStatus}`)
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById("tasksList");
            container.innerHTML = "";

            if (!data || data.length === 0) {
                container.innerHTML = "<p>No tasks found</p>";
                return;
            }

            data.forEach(task => {
                const card = document.createElement("div");
                card.className = "note-card";
                card.style.position = "relative";
                card.style.cursor = "pointer";

                card.onclick = (e) => {
                    if (
                        e.target.classList.contains("task-check") ||
                        e.target.classList.contains("delete-btn")
                    ) return;

                    if (task.type === "task") {
                        window.location.href = `/task-edit?id=${task.id}`;
                    } else {
                        window.location.href = `/task-series-edit?id=${task.id}`;
                    }
                };

                const title = document.createElement("div");
                title.className = "note-title";
                title.innerText =
                    task.type === "series"
                        ? `📂 ${task.title}`
                        : `📝 ${task.title}`;

                const meta = document.createElement("div");
                meta.className = "note-footer";

                const left = document.createElement("span");
                left.innerText = `Category: ${task.category || "General"}`;

                const right = document.createElement("span");
                right.innerText =
                    task.due_date
                        ? `Due: ${formatDate(task.due_date)}`
                        : `Status: ${task.status}`;

                meta.append(left, right);

                const badges = document.createElement("div");
                badges.style.marginTop = "6px";
                badges.style.fontSize = "13px";
                badges.style.color = "#555";
                badges.innerText =
                    `Priority: ${task.priority} | Difficulty: ${task.difficulty}`;

                card.append(title, meta, badges);

                if (task.type === "series") {
                    const fill = document.createElement("div");
                    fill.className = "series-progress-fill";
                    fill.style.height = `${task.progress}%`;
                    card.appendChild(fill);
                }

                if (task.type === "task") {
                    const check = document.createElement("input");
                    check.type = "checkbox";
                    check.className = "task-check";
                    check.checked = task.status === "completed";

                    check.onclick = (e) => {
                        e.stopPropagation();
                        updateTaskStatus(
                            task.id,
                            check.checked ? "completed" : "pending"
                        );
                    };

                    card.appendChild(check);
                }

                const delBtn = document.createElement("button");
                delBtn.innerText = "🗑";
                delBtn.className = "delete-btn";

                delBtn.onclick = (e) => {
                    e.stopPropagation();
                    if (!confirm("Delete this item?")) return;
                    deleteItem(task.id, task.type);
                };

                card.appendChild(delBtn);
                container.appendChild(card);
            });
        })
        .catch(() => {
            document.getElementById("tasksList").innerHTML =
                "<p>Server not reachable</p>";
        });
}

/* =====================================================
   DATE FORMAT
   ===================================================== */
function formatDate(dateStr) {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    return d.toLocaleDateString() + " " + d.toLocaleTimeString();
}

/* =====================================================
   UPDATE TASK STATUS  🔐 user_id added
   ===================================================== */
function updateTaskStatus(id, status) {
    fetch("/update-task-status", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user_id: USER_ID,
            id,
            status
        })
    }).then(() => loadTasks());
}

/* =====================================================
   DELETE TASK / SERIES  🔐 user_id added
   ===================================================== */
function deleteItem(id, type) {
    const url =
        type === "task"
            ? "/delete-task"
            : "/delete-task-series";

    fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user_id: USER_ID,
            id
        })
    }).then(() => loadTasks());
}
