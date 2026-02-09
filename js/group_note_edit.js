const USER_ID = localStorage.getItem("user_id");
if (!USER_ID) {
    window.location.href = "/login";
}

const params = new URLSearchParams(window.location.search);
const noteId = params.get("id");

window.selectedElement = null;

document.addEventListener("DOMContentLoaded", () => {
    loadGroupNote();
});

/* =====================================================
   LOAD GROUP NOTE
   ===================================================== */

   function applyBlockPermissions(blocks) {
    document.querySelectorAll(".locked-block").forEach(block => {
        const owner = block.dataset.blockOwner;
        const editableBy = block.dataset.editableBy || "";

        const allowedUsers = editableBy.split(",").map(x => x.trim());

        if (owner !== USER_ID && !allowedUsers.includes(USER_ID)) {
            block.contentEditable = "false";
        }
    });
}

function loadGroupNote() {
    fetch(`/group-note/${noteId}?user_id=${USER_ID}`)
        .then(res => res.json())
        .then(note => {
            noteTitle.value = note.title;
            content.innerHTML = note.content;
            applyBlockPermissions(note.blocks || []);


            timestamps.innerText =
                `Created: ${note.created_at} | Updated: ${note.updated_at}`;
        });
}


document.addEventListener("contextmenu", e => {
    const block = e.target.closest(".locked-block");
    if (!block) return;

    if (block.dataset.blockOwner !== USER_ID) return;

    e.preventDefault();

    const action = prompt(
        "1 = Delete block\n2 = Set allowed users (comma user_ids)"
    );

    if (action === "1") {
        block.remove();
    }

    if (action === "2") {
        const ids = prompt("Enter allowed user IDs (comma separated)");
        if (ids !== null) {
            block.dataset.editableBy = ids;
        }
    }
});

/* =====================================================
   SAVE GROUP NOTE
   ===================================================== */
function saveGroupNote() {
    const blocks = [];

    document.querySelectorAll(".locked-block").forEach(block => {
        blocks.push({
            content: block.innerHTML,
            created_by: block.dataset.blockOwner,
            editable_by: block.dataset.editableBy
        });
    });

    fetch(`/group-note/${noteId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user_id: USER_ID,
            title: noteTitle.value,
            content: content.innerHTML,
            blocks: blocks
        })
    })
    .then(() => alert("Saved"));
    window.location.href = "/group-dashboard";
}


/* =====================================================
   BACK
   ===================================================== */
function goBack() {
    window.location.href = "/group-dashboard";
}


// ===============================
// SHARED EDITOR CORE
// ===============================
window.selectedElement = null;

/* ---------- IMAGE UPLOAD ---------- */
function triggerImageUpload() {
    document.getElementById("imageInput").click();
}

document.addEventListener("change", function (e) {
    if (e.target.id !== "imageInput") return;

    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = e2 => insertImageAtCursor(e2.target.result);
    reader.readAsDataURL(file);
    e.target.value = "";
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
    content.querySelectorAll(".image-wrapper")
        .forEach(w => alignWrapper(w, direction));
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

/* ---------- CLEAR SELECTION ---------- */
function clearSelections() {
    document.querySelectorAll(".selected-image")
        .forEach(el => el.classList.remove("selected-image"));
}

/* ---------- TEXT FORMATTING ---------- */
const editorState = { bold: false, italic: false, underline: false };

function toggleFormat(type) {
    editorState[type] = !editorState[type];
}

document.addEventListener("beforeinput", e => {
    if (e.target.id !== "content") return;
    if (
        e.inputType !== "insertText" &&
        e.inputType !== "insertLineBreak"
    ) return;

    e.preventDefault();

    const sel = window.getSelection();
    if (!sel.rangeCount) return;

    const range = sel.getRangeAt(0);
    const span = document.createElement("span");

    if (editorState.bold) span.style.fontWeight = "bold";
    if (editorState.italic) span.style.fontStyle = "italic";
    if (editorState.underline) span.style.textDecoration = "underline";

    span.textContent = e.data || "\n";
    range.insertNode(span);
    range.setStartAfter(span);
    range.collapse(true);

    sel.removeAllRanges();
    sel.addRange(range);
});

/* ---------- FONT SIZE ---------- */
function changeTextSize(size) {
    if (!size || window.selectedElement) return;
    content.style.fontSize = size + "px";
}

function onFontSizeDropdownChange(selectEl) {
    if (!selectEl.value) return;
    changeTextSize(selectEl.value);
    selectEl.value = "";
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

function insertLockedBlock() {
    const sel = window.getSelection();
    const block = document.createElement("div");

    block.className = "locked-block";
    block.contentEditable = "true";
    block.dataset.blockOwner = USER_ID;
    block.dataset.editableBy = USER_ID; // owner by default
    block.innerHTML = "<p>Locked block content...</p>";

    if (!sel.rangeCount) {
        content.appendChild(block);
        return;
    }

    const range = sel.getRangeAt(0);
    range.collapse(false);
    range.insertNode(block);

    // move cursor inside block
    range.setStart(block, 0);
    sel.removeAllRanges();
    sel.addRange(range);
}

