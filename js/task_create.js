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


/* =====================================================
   GLOBAL
   ===================================================== */
let advancedOpened = false;

/* =====================================================
   TOGGLE ADVANCED SECTION
   ===================================================== */
function toggleAdvanced() {
    const section = document.getElementById("advancedSection");
    const icon = document.getElementById("plusIcon");

    advancedOpened = !advancedOpened;

    section.style.display = advancedOpened ? "block" : "none";
    icon.textContent = advancedOpened ? "−" : "+";
}

/* =====================================================
   REMINDER TOGGLE
   ===================================================== */
document.addEventListener("change", e => {
    if (e.target.id === "reminderCheck") {
        document.getElementById("reminderBox").style.display =
            e.target.checked ? "block" : "none";
    }
});

/* =====================================================
   SAVE TASK  🔐 user_id added
   ===================================================== */
async function saveTask() {

    const title = document.getElementById("taskTitle").value.trim();
    if (!title) {
        alert("Task title is required");
        return;
    }

    const taskData = {
        title: title,
        status: document.getElementById("taskStatus")?.value || "pending"
    };

    if (advancedOpened) {
        taskData.description =
            document.getElementById("taskDescription")?.value.trim() || "";

        taskData.selected_category =
            document.getElementById("categorySelect")?.value || "Auto";

        taskData.custom_category =
            document.getElementById("customCategory")?.value.trim() || "";

        taskData.due_date =
            document.getElementById("dueDate")?.value || null;

        taskData.priority =
            parseInt(document.getElementById("priority")?.value || 0, 10);

        taskData.difficulty =
            parseInt(document.getElementById("difficulty")?.value || 0, 10);

        if (document.getElementById("reminderCheck")?.checked) {
            taskData.reminder_time =
                document.getElementById("reminderTime")?.value || null;

            taskData.reminder_type =
                document.getElementById("reminderType")?.value || "email";
        }
    }

    try {
        const res = await fetch("/add-task", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_id: USER_ID,      // 🔐 ADDED (only change)
                ...taskData
            })
        });

        const result = await res.json();

        if (!res.ok) {
            if (res.status === 409) {
                alert("⚠️ Task already exists");
            } else {
                alert(result.error || "Failed to save task");
            }
            return;
        }

        // ✅ SUCCESS MESSAGE
        alert("✅ Task saved successfully!");

        // ✅ REDIRECT TO TASK DASHBOARD
        setTimeout(() => {
            window.location.replace("/task-dashboard");
        }, 0);

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
