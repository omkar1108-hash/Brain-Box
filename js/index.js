const USER_ID = localStorage.getItem("user_id");
if (!USER_ID) {
    window.location.href = "/login";
}

window.onload = () => {
    fetch(`/categories?user_id=${USER_ID}`)

        .then(res => res.json())
        .then(categories => {
            const select = document.getElementById("categorySelect");
            if (!select) return;

            categories.forEach(cat => {
                if (cat !== "All") {
                    const opt = document.createElement("option");
                    opt.value = cat;
                    opt.textContent = cat;
                    select.appendChild(opt);
                }
            });
        });
};

/* =====================================================
   GLOBAL
   ===================================================== */
window.selectedElement = null;

const typingBIUState = {
    bold: false,
    italic: false,
    underline: false
};

/* =====================================================
   SAVE NOTE
   ===================================================== */
function saveNote() {
    if (document.getElementById("protectCheck").checked) {
        document.getElementById("passwordPopup").style.display = "block";
        return;
    }
    submit(false, "");
}

function confirmPassword() {
    const pwd = document.getElementById("password").value.trim();
    if (!pwd) {
        alert("Password cannot be empty");
        return;
    }
    document.getElementById("passwordPopup").style.display = "none";
    submit(false, pwd);
}

function submit(forceUpdate, password) {

    password = typeof password === "string" ? password : "";

    const title = document.getElementById("title").value.trim();
    const contentHTML = document.getElementById("content").innerHTML.trim();

    const selectedCategory =
        document.getElementById("categorySelect")?.value || "Auto";

    const customCategory =
        document.getElementById("customCategory")?.value.trim() || "";

    if (!title && (!contentHTML || contentHTML === "<br>")) {
        alert("Title or content required");
        return;
    }

    fetch("/add-note", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            user_id: USER_ID,
            title: title,
            content: contentHTML,
            password: password,
            force_update: forceUpdate,
            selected_category: selectedCategory,
            custom_category: customCategory
        })
    })
    .then(res => {
        if (!res.ok) {
            throw new Error("Server error");
        }
        return res.json();
    })
    .then(data => {

        if (data.note_exists) {
            alert("This title already exists.");
            return;
        }

        if (data.error) {
            alert(data.error);
            return;
        }

        // ✅ SUCCESS → DASHBOARD
        window.location.href = "/notes-dashboard";
    })
    .catch(err => {
        console.error("SAVE ERROR:", err);
        alert("Failed to save note");
    });
}

/* ---------- BACK ---------- */
function goBack() {
    window.location.href = "/notes-dashboard";
}

/* =====================================================
   IMAGE INSERTION
   ===================================================== */
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

function insertImageAtCursor(base64) {

    const content = document.getElementById("content");

    const wrapper = document.createElement("span");
    wrapper.className = "image-wrapper";
    wrapper.contentEditable = "false";
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
    if (sel && sel.rangeCount && content.contains(sel.anchorNode)) {
        const range = sel.getRangeAt(0);
        range.deleteContents();
        range.insertNode(wrapper);
        range.insertNode(document.createTextNode("\u200B"));
        range.setStartAfter(wrapper);
        sel.removeAllRanges();
        sel.addRange(range);
    } else {
        content.appendChild(wrapper);
        content.appendChild(document.createTextNode("\u200B"));
    }
}

/* =====================================================
   SELECTION HANDLING
   ===================================================== */
document.getElementById("content").addEventListener("click", () => {
    clearSelections();
    window.selectedElement = null;
});

function clearSelections() {
    document.querySelectorAll(".selected-image").forEach(el =>
        el.classList.remove("selected-image")
    );
}

/* =====================================================
   ALIGNMENT
   ===================================================== */
function alignImage(wrapper, direction) {
    wrapper.style.display = "block";
    wrapper.style.marginLeft = direction === "right" ? "auto" : "0";
    wrapper.style.marginRight = direction === "left" ? "auto" : "0";
    if (direction === "center") {
        wrapper.style.marginLeft = "auto";
        wrapper.style.marginRight = "auto";
    }
}

function alignSelected(direction) {

    const content = document.getElementById("content");

    if (window.selectedElement) {
        alignImage(window.selectedElement, direction);
        return;
    }

    const sel = window.getSelection();
    if (sel && sel.rangeCount && !sel.isCollapsed && content.contains(sel.anchorNode)) {
        const range = sel.getRangeAt(0);
        const frag = range.extractContents();
        const span = document.createElement("span");
        span.style.textAlign = direction;
        span.appendChild(frag);
        range.insertNode(span);
        sel.removeAllRanges();
        return;
    }

    content.style.textAlign = direction;
}

/* =====================================================
   FORMAT HELPERS (UNCHANGED)
   ===================================================== */
function removeStyleSpans(root, prop) {
    root.querySelectorAll("span").forEach(span => {
        if (span.style && span.style[prop]) {
            while (span.firstChild) {
                span.parentNode.insertBefore(span.firstChild, span);
            }
            span.remove();
        }
    });
}

function isAllStyled(fragment, prop, value) {

    const walker = document.createTreeWalker(
        fragment,
        NodeFilter.SHOW_TEXT,
        null
    );

    let node;
    let found = false;

    while ((node = walker.nextNode())) {
        found = true;

        const parent = node.parentElement;
        if (!parent || !hasExplicitStyle(parent, prop, value)) {
            return false;
        }
    }
    return found;
}

/* =====================================================
   TEXT FORMATTING (UNCHANGED)
   ===================================================== */
const editorState = {
    bold: false,
    italic: false,
    underline: false
};

function toggleFormat(type) {

    if (window.selectedElement) return;

    editorState[type] = !editorState[type];

    const btn = document.querySelector(`[data-format="${type}"]`);
    if (btn) btn.classList.toggle("active", editorState[type]);
}

document.getElementById("content").addEventListener(
    "beforeinput",
    applyTypingFormat
);

function applyTypingFormat(e) {

    if (
        e.inputType !== "insertText" &&
        e.inputType !== "insertLineBreak"
    ) return;

    if (window.selectedElement) return;

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
}

/* =====================================================
   FONT SIZE (UNCHANGED)
   ===================================================== */
function changeTextSize(size) {

    if (!size || window.selectedElement) return;
    size = parseInt(size, 10);
    if (isNaN(size) || size < 8 || size > 72) return;

    const content = document.getElementById("content");
    const sel = window.getSelection();

    if (!sel.isCollapsed && content.contains(sel.anchorNode)) {
        const range = sel.getRangeAt(0);
        const frag = range.extractContents();
        const allSame = isAllStyled(frag, "fontSize", size + "px");
        removeStyleSpans(frag, "fontSize");

        if (!allSame) {
            const span = document.createElement("span");
            span.style.fontSize = size + "px";
            span.appendChild(frag);
            range.insertNode(span);
        } else {
            range.insertNode(frag);
        }
        sel.removeAllRanges();
        return;
    }

    content.style.fontSize = size + "px";
}

function onFontSizeDropdownChange(selectEl) {
    if (!selectEl.value) return;
    changeTextSize(selectEl.value);
    selectEl.value = "";
}
