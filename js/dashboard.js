const USER_ID = localStorage.getItem("user_id");
if (!USER_ID) {
    window.location.href = "/login";
}


let currentCategory = "All";
let protectionFilter = "all";

window.onload = () => {
    loadCategories();
    loadNotes("All");
};

/* ---------- CREATE NOTE ---------- */
function goToCreate() {
    // notes create page (index.html served by Flask)
    window.location.href = "/notes-create";
}

/* ---------- CATEGORIES ---------- */
function loadCategories() {
    fetch(`/categories?user_id=${USER_ID}`)


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
                    loadNotes(cat);
                };

                container.appendChild(btn);
            });
        });
}

/* ---------- LOAD NOTES ---------- */
function loadNotes(category = currentCategory) {
    currentCategory = category;

    fetch(`/notes?user_id=${USER_ID}&category=${currentCategory}&filter=${protectionFilter}`)

        .then(res => res.json())
        .then(data => {
            const container = document.getElementById("notesList");
            container.innerHTML = "";

            if (!data || data.length === 0) {
                container.innerHTML = "<p>No notes found</p>";
                return;
            }

            data.forEach(note => {
                const card = document.createElement("div");
                card.className = "note-card";
                card.onclick = () => openNote(note);

                const del = document.createElement("button");
                del.className = "delete-btn";
                del.innerText = "×";
                del.onclick = e => {
                    e.stopPropagation();
                    fetch(`/notes/${note.id}?user_id=${USER_ID}`, { method: "DELETE" })

                        .then(() => loadNotes(currentCategory));
                };

                const title = document.createElement("div");
                title.className = "note-title";
                title.innerText = note.title;

                const footer = document.createElement("div");
                footer.className = "note-footer";

                const created = document.createElement("span");
                created.innerText = `Created: ${formatDate(note.created_at)}`;

                const updated = document.createElement("span");
                updated.innerText = `Updated: ${formatDate(note.updated_at)}`;

                footer.append(created, updated);
                card.append(del, title, footer);
                container.appendChild(card);
            });
        });
}

/* ---------- OPEN NOTE ---------- */
function openNote(note) {
    if (!note.protected) {
        window.location.href = `/notes-edit?id=${note.id}`;
        return;
    }

    const pwd = prompt("This note is protected. Enter password:");
    if (!pwd) return;

    fetch("/verify-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            note_id: note.id,
            password: pwd
        })
    })
    .then(res => res.json())
    .then(result => {
        if (result.valid) {
            window.location.href = `/notes-edit?id=${note.id}`;
        } else {
            alert("Incorrect password");
        }
    });
}

/* ---------- PROTECTION FILTER ---------- */
function setProtectionFilter(type) {
    protectionFilter = type;

    document
        .querySelectorAll("#protectionFilters .filter-btn")
        .forEach(b => b.classList.remove("active"));

    event.target.classList.add("active");

    loadNotes(currentCategory);
}

/* ---------- DATE FORMAT ---------- */
function formatDate(dateStr) {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    return d.toLocaleString();
}
