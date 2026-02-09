const USER_ID = localStorage.getItem("user_id");
if (!USER_ID) {
    window.location.href = "/login";
}

function createGroupNote() {
    const title = document.getElementById("title").value.trim();
    const content = document.getElementById("content").value.trim();
    const membersRaw = document.getElementById("members").value.trim();

    if (!title) {
        alert("Title is required");
        return;
    }

    const members = membersRaw
        ? membersRaw.split(",").map(e => e.trim()).filter(Boolean)
        : [];

    fetch("/create-group-note", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user_id: USER_ID,
            title: title,
            content: content,
            members: members
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        window.location.href = "/group-dashboard";
    })
    .catch(err => {
        console.error(err);
        alert("Failed to create group note");
    });
}

function goBack() {
    window.location.href = "/group-dashboard";
}
