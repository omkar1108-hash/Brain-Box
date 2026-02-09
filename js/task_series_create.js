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


/* =====================================================
   GLOBAL
   ===================================================== */
let advancedOpened = false;

/* =====================================================
   TOGGLE ADVANCED
   ===================================================== */
function toggleAdvanced() {
    advancedOpened = !advancedOpened;
    document.getElementById("advancedSection").style.display =
        advancedOpened ? "block" : "none";
    document.getElementById("plusIcon").innerText =
        advancedOpened ? "−" : "+";
}

/* =====================================================
   ADD TASK
   ===================================================== */
function addTask() {
    const container = document.getElementById("taskList");

    const div = document.createElement("div");
    div.className = "task-card";

    div.innerHTML = `
        <button class="remove-btn" onclick="this.parentElement.remove()">✕</button>

        <label>Task Title *</label>
        <input type="text" class="task-title" placeholder="Enter task title">

        <label>Description (optional)</label>
        <textarea class="task-desc"></textarea>

        <label>Due Date (optional)</label>
        <input type="date" class="task-due">

        <label>Priority (0 – 10)</label>
        <input type="range" class="task-priority" min="0" max="10" value="0">

        <label>Difficulty (0 – 10)</label>
        <input type="range" class="task-difficulty" min="0" max="10" value="0">

        <label>Status</label>
        <select class="task-status">
            <option value="pending">Pending</option>
            <option value="completed">Completed</option>
        </select>
    `;

    container.appendChild(div);
}

/* =====================================================
   SAVE TASK SERIES  🔐 user_id added
   ===================================================== */
async function saveSeries() {

    const seriesTitle =
        document.getElementById("seriesTitle").value.trim();

    if (!seriesTitle) {
        alert("Series title is required");
        return;
    }

    const tasks = [];
    const taskCards = document.querySelectorAll(".task-card");

    if (taskCards.length === 0) {
        alert("Add at least one task");
        return;
    }

    for (const card of taskCards) {
        const title = card.querySelector(".task-title").value.trim();

        if (!title) {
            alert("Each task must have a title");
            return;
        }

        tasks.push({
            title: title,
            description: card.querySelector(".task-desc").value.trim(),
            due_date: card.querySelector(".task-due").value || null,
            priority: parseInt(card.querySelector(".task-priority").value, 10),
            difficulty: parseInt(card.querySelector(".task-difficulty").value, 10),
            status: card.querySelector(".task-status").value
        });
    }

    const payload = {
        title: seriesTitle,
        selected_category:
            document.getElementById("categorySelect").value,
        custom_category:
            document.getElementById("customCategory").value.trim(),
        tasks: tasks
    };

    try {
        const res = await fetch("/add-task-series", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_id: USER_ID,     // 🔐 ADDED (only change)
                ...payload
            })
        });

        const data = await res.json();

        if (!res.ok) {
            alert(data.error || "Failed to save task series");
            return;
        }

        alert("✅ Task series created successfully");

        // ✅ REDIRECT TO TASK DASHBOARD
        window.location.href = "/task-dashboard";

    } catch (err) {
        console.error(err);
        alert("❌ Server not reachable");
    }
}

/* =====================================================
   BACK
   ===================================================== */
function goBack() {
    window.location.href = "/task-dashboard";
}


