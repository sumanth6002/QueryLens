function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function showError(banner, message) {
    if (!banner) {
        return;
    }
    banner.hidden = false;
    banner.textContent = message;
}

function clearError(banner) {
    if (!banner) {
        return;
    }
    banner.hidden = true;
    banner.textContent = "";
}

function showInfo(banner, message) {
    if (!banner) {
        return;
    }
    banner.hidden = false;
    banner.textContent = message;
}

function clearInfo(banner) {
    if (!banner) {
        return;
    }
    banner.hidden = true;
    banner.textContent = "";
}

function setBusy(button, busy, busyLabel, idleLabel) {
    if (!button) {
        return;
    }
    button.disabled = busy;
    button.textContent = busy ? busyLabel : idleLabel;
}
