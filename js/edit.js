const USER_ID = localStorage.getItem("user_id");
if (!USER_ID) {
    window.location.href = "/login";
}

const params = new URLSearchParams(window.location.search);
const noteId = params.get("id");

let wasProtected = false;
window.selectedElement = null;

document.addEventListener("DOMContentLoaded", () => {
    loadNote();
});

/* ---------- LOAD CATEGORIES ---------- */
function loadCategories(selectedCategory = "Auto") {
    fetch(`/categories?user_id=${USER_ID}`)
        .then(res => res.json())
        .then(categories => {
            const select = document.getElementById("categorySelect");

            select.innerHTML =
                '<option value="Auto">Auto (Recommended)</option>';

            categories.forEach(cat => {
                if (cat !== "All") {
                    const opt = document.createElement("option");
                    opt.value = cat;
                    opt.textContent = cat;

                    if (cat === selectedCategory) {
                        opt.selected = true;
                    }

                    select.appendChild(opt);
                }
            });
        });
}

/* ---------- LOAD NOTE ---------- */
function loadNote() {
    fetch(`/notes/${noteId}?user_id=${USER_ID}`)
        .then(res => res.json())
        .then(note => {
            noteTitle.value = note.title;
            content.innerHTML = note.content;

            timestamps.innerText =
                `Created: ${note.created_at} | Last Updated: ${note.updated_at}`;

            wasProtected = note.protected;

            if (note.protected) {
                protectCheck.checked = true;
                addPasswordBox.style.display = "none";
                changePasswordBox.style.display = "block";
            } else {
                protectCheck.checked = false;
                addPasswordBox.style.display = "block";
                changePasswordBox.style.display = "none";
            }

            loadCategories(note.category);
        });
}

/* ---------- PROTECTION TOGGLE ---------- */
protectCheck.onchange = () => {

    if (!protectCheck.checked && wasProtected) {
        const pwd = prompt("Enter current password to remove protection:");
        if (!pwd) {
            protectCheck.checked = true;
            return;
        }

        fetch("/verify-password", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                note_id: noteId,
                password: pwd
            })
        })
        .then(res => res.json())
        .then(result => {
            if (!result.valid) {
                alert("Incorrect password");
                protectCheck.checked = true;
            } else {
                wasProtected = false;
                addPasswordBox.style.display = "none";
                changePasswordBox.style.display = "none";
                submitUpdate("");
            }
        });
        return;
    }

    if (protectCheck.checked && !wasProtected) {
        addPasswordBox.style.display = "block";
        changePasswordBox.style.display = "none";
    }
};

/* ---------- SAVE ---------- */
function saveNote() {

    if (protectCheck.checked && wasProtected) {
        verifyAndChangePassword();
        return;
    }

    if (protectCheck.checked && !wasProtected) {
        if (!newPassword.value) {
            alert("Password cannot be empty");
            return;
        }
        submitUpdate(newPassword.value);
        return;
    }

    submitUpdate("");
}

/* ---------- VERIFY & CHANGE PASSWORD ---------- */
function verifyAndChangePassword() {
    if (!oldPassword.value || !changePassword.value) {
        alert("Both old and new password required");
        return;
    }

    fetch("/verify-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            note_id: noteId,
            password: oldPassword.value
        })
    })
    .then(res => res.json())
    .then(result => {
        if (!result.valid) {
            alert("Incorrect old password");
            return;
        }
        submitUpdate(changePassword.value);
    });
}

/* ---------- UPDATE (🔐 user_id added) ---------- */
function submitUpdate(password) {

    const selectedCategory =
        document.getElementById("categorySelect")?.value || "Auto";

    const customCategory =
        document.getElementById("customCategory")?.value.trim() || "";

    fetch("/add-note", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user_id: USER_ID,          // 🔐 ADDED (only change)
            title: noteTitle.value,
            content: content.innerHTML,
            password: password,
            force_update: true,
            selected_category: selectedCategory,
            custom_category: customCategory
        })
    })
    .then(() => window.location.href = "/notes-dashboard")
    .catch(err => {
        console.error("UPDATE ERROR:", err);
        alert("Failed to update note");
    });
}

/* ---------- DELETE (🔐 user_id added) ---------- */
function deleteNote() {
    if (!confirm("Delete this note?")) return;

    fetch(`/notes/${noteId}?user_id=${USER_ID}`, {   // 🔐 ADDED
        method: "DELETE"
    })
    .then(() => window.location.href = "/notes-dashboard");
}

/* ---------- BACK ---------- */
function goBack() {
    window.location.href = "/notes-dashboard";
}

/* ---------- IMAGE UPLOAD ---------- */
function triggerImageUpload() {
    document.getElementById("imageInput").click();
}

document.getElementById("imageInput").addEventListener("change", function () {
    const file = this.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = e => insertImageAtCursor(e.target.result);
    reader.readAsDataURL(file);
    this.value = "";
});

/* ---------- INSERT IMAGE ---------- */
function insertImageAtCursor(base64) {

    const wrapper = document.createElement("span");
    wrapper.className = "image-wrapper";
    wrapper.style.width = "150px";

    const img = document.createElement("img");
    img.src = base64;
    wrapper.appendChild(img);

    wrapper.onclick = e => {
        e.stopPropagation();
        clearSelections();
        wrapper.classList.add("selected-image");
        window.selectedElement = wrapper;
    };

    const sel = window.getSelection();
    if (!sel.rangeCount) {
        content.appendChild(wrapper);
        content.appendChild(document.createTextNode("\u200B"));
        return;
    }

    const range = sel.getRangeAt(0);
    range.deleteContents();

    range.insertNode(wrapper);
    range.insertNode(document.createTextNode("\u200B"));

    range.setStartAfter(wrapper);
    range.setEndAfter(wrapper);

    sel.removeAllRanges();
    sel.addRange(range);
}

/* ---------- ALIGNMENT ---------- */
function alignSelected(direction) {

    if (window.selectedElement) {
        alignWrapper(window.selectedElement, direction);
        return;
    }

    const sel = window.getSelection();

    if (sel && sel.rangeCount && !sel.isCollapsed) {
        const range = sel.getRangeAt(0);
        const wrapper = document.createElement("div");
        wrapper.style.textAlign = direction;
        range.surroundContents(wrapper);
        sel.removeAllRanges();
        return;
    }

    content.style.textAlign = direction;

    content.querySelectorAll(".image-wrapper").forEach(w => {
        alignWrapper(w, direction);
    });
}

function alignWrapper(wrapper, direction) {
    if (direction === "left") {
        wrapper.style.marginLeft = "0";
        wrapper.style.marginRight = "auto";
    } else if (direction === "center") {
        wrapper.style.marginLeft = "auto";
        wrapper.style.marginRight = "auto";
    } else {
        wrapper.style.marginLeft = "auto";
        wrapper.style.marginRight = "0";
    }
}

/* ---------- PDF DOWNLOAD (UNCHANGED) ---------- */
async function downloadPDF() {
    const { jsPDF } = window.jspdf;

    const titleText = noteTitle.value || "Untitled Note";
    const contentDiv = document.getElementById("content");

    const pdfWrapper = document.createElement("div");
    pdfWrapper.style.width = "800px";
    pdfWrapper.style.padding = "20px";
    pdfWrapper.style.fontFamily = "Arial";

    const titleEl = document.createElement("h2");
    titleEl.innerText = titleText;
    titleEl.style.textAlign = "center";
    titleEl.style.marginBottom = "20px";

    const contentClone = contentDiv.cloneNode(true);

    pdfWrapper.appendChild(titleEl);
    pdfWrapper.appendChild(contentClone);

    document.body.appendChild(pdfWrapper);

    const canvas = await html2canvas(pdfWrapper, { scale: 2, useCORS: true });
    const imgData = canvas.toDataURL("image/png");

    const pdf = new jsPDF("p", "mm", "a4");
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = (canvas.height * pdfWidth) / canvas.width;

    pdf.addImage(imgData, "PNG", 0, 0, pdfWidth, pdfHeight);
    pdf.save(`${titleText}.pdf`);

    document.body.removeChild(pdfWrapper);
}
