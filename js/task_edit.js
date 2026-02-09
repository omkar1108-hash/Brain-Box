const USER_ID = localStorage.getItem("user_id");
if (!USER_ID) {
    window.location.href = "/login";
}

window.onload = () => {
    fetch(`/task-categories?user_id=${USER_ID}`)
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
        .catch(err => console.error("Category load error:", err));
};


const params = new URLSearchParams(window.location.search);
const taskId = params.get("id");

document.addEventListener("DOMContentLoaded", loadTask);

/* ===============================
   LOAD TASK  🔐 user_id added
   =============================== */
function loadTask() {
    fetch(`/tasks/${taskId}?user_id=${USER_ID}`)
        .then(res => res.json())
        .then(task => {
            taskTitle.value = task.title;
            taskDescription.value = task.description || "";
            taskStatus.value = task.status;
            dueDate.value = task.due_date || "";

            priority.value = task.priority || 0;
            priorityValue.innerText = priority.value;

            difficulty.value = task.difficulty || 0;
            difficultyValue.innerText = difficulty.value;
        });
}

/* ===============================
   UPDATE TASK  🔐 user_id added
   =============================== */
function updateTask() {

    const payload = {
        id: taskId,
        title: taskTitle.value.trim(),
        description: taskDescription.value.trim(),
        status: taskStatus.value,
        due_date: dueDate.value || null,
        priority: parseInt(priority.value, 10),
        difficulty: parseInt(difficulty.value, 10),
        selected_category: categorySelect.value,
        custom_category: customCategory.value.trim()
    };

    fetch("/update-task", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user_id: USER_ID,   // 🔐 ADDED
            ...payload
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
        alert("❌ Failed to update task");
    });
}

/* ===============================
   DELETE TASK  🔐 user_id added
   =============================== */
function deleteTask() {
    if (!confirm("Delete this task?")) return;

    fetch("/delete-task", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user_id: USER_ID,   // 🔐 ADDED
            id: taskId
        })
    })
    .then(() => window.location.href = "/task-dashboard");
}

/* ===============================
   BACK
   =============================== */
function goBack() {
    window.location.href = "/task-dashboard";
}
