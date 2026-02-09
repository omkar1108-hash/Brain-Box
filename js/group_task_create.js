/* =====================================================
   AUTH
   ===================================================== */
const USER_ID = localStorage.getItem("user_id");
if (!USER_ID) {
    window.location.href = "/login";
}

/* =====================================================
   DOM REFERENCES (SAFE)
   ===================================================== */
const advancedSection = document.getElementById("advancedSection");
const plusIcon = document.getElementById("plusIcon");
const memberList = document.getElementById("memberList");
const taskList = document.getElementById("taskList");
const groupTitleInput = document.getElementById("groupTitle");

/* =====================================================
   GLOBAL STATE
   ===================================================== */
let advancedOpened = false;

/* =====================================================
   TOGGLE ADVANCED (same as task series)
   ===================================================== */
function toggleAdvanced() {
    advancedOpened = !advancedOpened;
    advancedSection.style.display = advancedOpened ? "block" : "none";
    plusIcon.innerText = advancedOpened ? "−" : "+";
}

/* =====================================================
   MEMBERS
   ===================================================== */
function addMember() {
    const div = document.createElement("div");

    div.innerHTML = `
        <input type="text"
               class="member-input"
               placeholder="username or email"
               oninput="refreshAllAssignDropdowns()">
        <button type="button"
                onclick="this.parentElement.remove();
                         refreshAllAssignDropdowns()">✕</button>
    `;

    memberList.appendChild(div);
}

/* =====================================================
   REFRESH ASSIGN DROPDOWNS
   ===================================================== */
function refreshAllAssignDropdowns() {
    document.querySelectorAll(".task-assign")
        .forEach(select => populateAssignDropdown(select));
}

/* =====================================================
   TASKS
   ===================================================== */
function addTask() {
    const div = document.createElement("div");
    div.className = "task-card";

    div.innerHTML = `
        <button class="remove-btn"
                type="button"
                onclick="this.parentElement.remove()">✕</button>

        <label>Task Title *</label>
        <input type="text" class="task-title">

        <label>Description</label>
        <textarea class="task-desc"></textarea>

        <label>Assign To *</label>
        <select class="task-assign"></select>
    `;

    taskList.appendChild(div);
    populateAssignDropdown(div.querySelector(".task-assign"));
}

/* =====================================================
   POPULATE ASSIGN DROPDOWN
   ===================================================== */
function populateAssignDropdown(select) {
    select.innerHTML = "";

    /* ALL OPTION */
    const allOpt = document.createElement("option");
    allOpt.value = "ALL";
    allOpt.innerText = "All (Anyone can complete)";
    select.appendChild(allOpt);

    /* CREATOR */
    const selfOpt = document.createElement("option");
    selfOpt.value = USER_ID;
    selfOpt.innerText = "Me";
    select.appendChild(selfOpt);

    /* MEMBERS */
    document.querySelectorAll(".member-input").forEach(input => {
        const val = input.value.trim();
        if (!val) return;

        const opt = document.createElement("option");
        opt.value = val;              // username or email
        opt.innerText = val;
        select.appendChild(opt);
    });
}

/* =====================================================
   CREATE GROUP (SAVE)
   ===================================================== */
async function createGroup() {
    const groupTitle = groupTitleInput.value.trim();
    if (!groupTitle) {
        alert("Group title is required");
        return;
    }

    /* MEMBERS */
    const members = [];
    document.querySelectorAll(".member-input").forEach(input => {
        const v = input.value.trim();
        if (v) members.push(v);
    });

    /* TASKS */
    const tasks = [];
    document.querySelectorAll(".task-card").forEach(card => {
        const taskTitle = card.querySelector(".task-title").value.trim();
        const assignVal = card.querySelector(".task-assign").value;

        if (!taskTitle) return;

        tasks.push({
            title: taskTitle,
            description:
                card.querySelector(".task-desc").value.trim(),
            assigned_to: assignVal   // ALL | user_id | username/email
        });
    });

    if (!tasks.length) {
        alert("Add at least one task");
        return;
    }

    /* API CALL */
    try {
        const res = await fetch("/create-group-task", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_id: USER_ID,
                title: groupTitle,
                members: members,
                tasks: tasks
            })
        });

        const data = await res.json();

        if (!res.ok) {
            alert(data.error || "Failed to create group task");
            return;
        }

        window.location.href = "/group-task-dashboard";

    } catch (err) {
        console.error(err);
        alert("Server not reachable");
    }
}

/* =====================================================
   BACK
   ===================================================== */
function goBack() {
    window.location.href = "/group-task-dashboard";
}
