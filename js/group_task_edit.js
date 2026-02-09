const USER_ID = localStorage.getItem("user_id");
if (!USER_ID) window.location.href = "/login";

const groupId = new URLSearchParams(window.location.search).get("id");

let MY_ROLE = "";
let MEMBERS = [];
let TASKS = [];

document.addEventListener("DOMContentLoaded", loadGroup);

/* ===============================
   LOAD GROUP
   =============================== */
async function loadGroup() {
    const res = await fetch(`/group-task/${groupId}?user_id=${USER_ID}`);
    const data = await res.json();

    MY_ROLE = data.my_role;
    MEMBERS = data.members;
    TASKS = data.tasks;

    groupTitle.value = data.title;

    renderMembers();
    renderTasks();

    if (MY_ROLE !== "creator") {
        document.getElementById("addMemberBtn").style.display = "none";
    }

    updateProgress();
}

/* ===============================
   MEMBERS
   =============================== */
function renderMembers() {
    memberList.innerHTML = "";

    MEMBERS.forEach(m => {
        const div = document.createElement("div");
        div.className = "member-row";
        div.innerHTML = `<span>${m.name}</span>`;

        if (MY_ROLE === "creator" && m.role !== "creator") {
            const btn = document.createElement("button");
            btn.innerText = "Remove";
            btn.onclick = () => removeMember(m.id);
            div.appendChild(btn);
        }

        memberList.appendChild(div);
    });
}

function addMember() {
    const name = prompt("Enter username or email");
    if (!name) return;

    fetch("/group-task-add-member", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user_id: USER_ID,
            group_id: groupId,
            member: name
        })
    }).then(() => loadGroup());
}

/* ===============================
   TASKS
   =============================== */
function renderTasks() {
    taskList.innerHTML = "";

    TASKS.forEach(t => {
        const row = document.createElement("div");
        row.className = "task-row";

        const canComplete =
            MY_ROLE === "creator" ||
            (t.assigned_to !== null &&
             String(t.assigned_to) === String(USER_ID));

        row.innerHTML = `
            <input type="checkbox"
                ${t.status === "completed" ? "checked" : ""}
                ${canComplete ? "" : "disabled"}
                onchange="toggleStatus(${t.task_id}, this.checked)">

            <input type="text" value="${t.title}" disabled>

            <textarea disabled>${t.description || ""}</textarea>

            <select class="assign"></select>
        `;

        const select = row.querySelector(".assign");
        populateAssign(select, t.assigned_to);

        // assignment change allowed for all members
        if (MY_ROLE === "creator") {
            select.onchange = () =>
                updateAssignment(t.task_id, select.value);
        } else {
            select.disabled = true;
        }

        // delete only for creator
        if (MY_ROLE === "creator") {
            const del = document.createElement("button");
            del.className = "remove-btn";
            del.innerText = "✕";
            del.onclick = () => deleteTask(t.task_id);
            row.appendChild(del);
        }

        taskList.appendChild(row);
    });

    updateProgress();
}

function toggleStatus(taskId, checked) {
    fetch("/group-task-toggle-status", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user_id: USER_ID,
            task_id: taskId,
            status: checked ? "completed" : "pending"
        })
    }).then(res => {
        if (!res.ok) {
            alert("You are not allowed to complete this task");
            loadGroup();
        } else {
            loadGroup();
        }
    });
}


function updateAssignment(taskId, value) {
    fetch("/group-task-update-assign", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user_id: USER_ID,
            task_id: taskId,
            assigned_to: value
        })
    }).then(res => {
        if (!res.ok) {
            alert("Failed to update assignment");
            loadGroup();
        }
    });
}


function addTask() {
    const title = prompt("Task title");
    if (!title) return;

    fetch("/group-task-add-task", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user_id: USER_ID,
            group_id: groupId,
            title: title
        })
    }).then(() => loadGroup());
}

/* ===============================
   ASSIGN DROPDOWN
   =============================== */
function populateAssign(select, current) {
    select.innerHTML = "";

    const all = new Option("All", "ALL");
    select.add(all);

    MEMBERS.forEach(m => {
        const opt = new Option(m.name, m.id);
        select.add(opt);
    });

    if (current === null) {
        select.value = "ALL";
    } else {
        select.value = String(current);
    }
}

/* ===============================
   DELETE TASK (creator only)
   =============================== */
function deleteTask(taskId) {
    fetch("/group-task-delete-task", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user_id: USER_ID,
            task_id: taskId
        })
    }).then(() => loadGroup());
}

/* ===============================
   PROGRESS
   =============================== */
function updateProgress() {
    if (!document.getElementById("progressBar") ||
        !document.getElementById("progressText")) {
        return; // prevent JS crash
    }

    const total = TASKS.length;
    const completed = TASKS.filter(t => t.status === "completed").length;

    const percent = total ? Math.round((completed / total) * 100) : 0;
    progressBar.style.width = percent + "%";
    progressText.innerText = percent + "%";
}


function goBack() {
    window.location.href = "/group-task-dashboard";
}
