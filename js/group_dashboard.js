const USER_ID = localStorage.getItem("user_id");
if (!USER_ID) {
    window.location.href = "/login";
}

window.onload = () => {
    loadGroupNotes();
};

/* ---------- CREATE GROUP NOTE ---------- */
function goToCreateGroupNote() {
    window.location.href = "/group-note-create";
}

/* ---------- LOAD GROUP NOTES ---------- */
function loadGroupNotes() {
    fetch(`/group-notes?user_id=${USER_ID}`)
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById("groupNotesList");
            container.innerHTML = "";

            if (!data || data.length === 0) {
                container.innerHTML = "<p>No group notes found</p>";
                return;
            }

            data.forEach(note => {
                const card = document.createElement("div");
                card.className = "note-card";
                card.onclick = () => openGroupNote(note.id);

                const title = document.createElement("div");
                title.className = "note-title";
                title.innerText = note.title;

                const footer = document.createElement("div");
                footer.className = "note-footer";

                const created = document.createElement("span");
                created.innerText = `Created: ${formatDate(note.created_at)}`;

                const role = document.createElement("span");
                role.innerText = `Role: ${note.role}`;

                footer.append(created, role);
                card.append(title, footer);
                container.appendChild(card);
            });
        });
}

/* ---------- OPEN GROUP NOTE ---------- */
function openGroupNote(id) {
    window.location.href = `/group-note-edit?id=${id}`;
}

/* ---------- DATE FORMAT ---------- */
function formatDate(dateStr) {
    if (!dateStr) return "";
    return new Date(dateStr).toLocaleString();
}
