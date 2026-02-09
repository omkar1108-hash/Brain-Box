const USER_ID = localStorage.getItem("user_id");
if (!USER_ID) {
    window.location.href = "/login";
}

window.onload = loadGroupTasks;

function goToCreateGroup() {
    window.location.href = "/group-task-create";
}

function loadGroupTasks() {
    fetch(`/group-tasks-dashboard?user_id=${USER_ID}`)
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById("groupTasksList");
            container.innerHTML = "";

            if (!data.length) {
                container.innerHTML = "<p>No group tasks found</p>";
                return;
            }

            data.forEach(g => {
                const card = document.createElement("div");
                card.className = "note-card";
                card.style.cursor = "pointer";

                card.onclick = () => {
                    window.location.href =
                        `/group-task-edit?id=${g.group_id}`;
                };

                const title = document.createElement("div");
                title.className = "note-title";
                title.innerText = `👥 ${g.title}`;

                const meta = document.createElement("div");
                meta.className = "note-footer";
                meta.innerText =
                    `Members: ${g.member_count} | Progress: ${g.progress}%`;

                const fill = document.createElement("div");
                fill.className = "series-progress-fill";
                fill.style.height = `${g.progress}%`;

                card.append(title, meta, fill);
                container.appendChild(card);
            });
        })
        .catch(() => {
            document.getElementById("groupTasksList").innerHTML =
                "<p>Server error</p>";
        });
}
