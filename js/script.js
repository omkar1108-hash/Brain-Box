function redirectToDashboard() {
    window.location.assign("/html/dashboard.html");
}

document.getElementById("saveBtn").addEventListener("click", function () {
    saveNote();
});

function saveNote(forceUpdate = false) {
    const title = document.getElementById("noteTitle").value;
    const content = document.getElementById("noteContent").value;

    if (title.trim() === "" && content.trim() === "") {
        alert("Title or content is required");
        return;
    }

    fetch("/add-note", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            title: title,
            content: content,
            force_update: forceUpdate
        })
    })
    .then(res => res.json())
    .then(data => {

        if (data.note_exists === true) {
            const ok = confirm(
                "Note already exists. Do you want to update it?"
            );
            if (ok) saveNote(true);
            return;
        }

        // SUCCESS → redirect
        redirectToDashboard();
    })
    .catch(err => {
        console.error(err);
        alert("Error saving note");
    });
}
