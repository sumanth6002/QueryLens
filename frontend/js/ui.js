function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function showError(banner, message) {
    if (!banner) return;
    banner.hidden = false;
    banner.textContent = message;
    banner.classList.remove("banner-info", "banner-success", "banner-warning");
    banner.classList.add("banner-error");
}

function clearError(banner) {
    if (!banner) return;
    banner.hidden = true;
    banner.textContent = "";
}

function showInfo(banner, message) {
    if (!banner) return;
    banner.hidden = false;
    banner.textContent = message;
    banner.classList.remove("banner-error", "banner-success", "banner-warning");
    banner.classList.add("banner-info");
}

function showSuccess(banner, message) {
    if (!banner) return;
    banner.hidden = false;
    banner.textContent = message;
    banner.classList.remove("banner-error", "banner-info", "banner-warning");
    banner.classList.add("banner-success");
}

function clearInfo(banner) {
    if (!banner) return;
    banner.hidden = true;
    banner.textContent = "";
}

function setBusy(button, busy, busyLabel, idleLabel) {
    if (!button) return;
    button.disabled = busy;
    button.classList.toggle("is-loading", busy);
    const label = button.querySelector(".btn-label");
    const text = busy ? busyLabel : idleLabel;
    if (label) {
        label.textContent = text;
    } else {
        button.textContent = text;
    }
}

function showConfirm({ title, message, confirmLabel = "Confirm", danger = false }) {
    return new Promise((resolve) => {
        const overlay = document.createElement("div");
        overlay.className = "ql-modal-overlay";
        overlay.innerHTML = `
            <div class="ql-modal" role="dialog" aria-modal="true">
                <h3>${escapeHtml(title)}</h3>
                <p>${escapeHtml(message)}</p>
                <div class="ql-modal-actions">
                    <button type="button" class="btn btn-secondary" data-action="cancel">Cancel</button>
                    <button type="button" class="btn ${danger ? "btn-danger" : "btn-primary"}" data-action="confirm">${escapeHtml(confirmLabel)}</button>
                </div>
            </div>
        `;

        function close(result) {
            overlay.remove();
            resolve(result);
        }

        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) close(false);
        });
        overlay.querySelector('[data-action="cancel"]').addEventListener("click", () => close(false));
        overlay.querySelector('[data-action="confirm"]').addEventListener("click", () => close(true));
        document.body.appendChild(overlay);
    });
}

function formatDate(iso) {
    if (!iso) return "—";
    try {
        return new Date(iso).toLocaleDateString(undefined, {
            month: "short",
            day: "numeric",
            year: "numeric",
        });
    } catch {
        return "—";
    }
}

function renderEmptyState(container, { icon = "inbox", title, message }) {
    container.innerHTML = `
        <div class="empty-state">
            <i data-lucide="${icon}"></i>
            <h3>${escapeHtml(title)}</h3>
            <p>${escapeHtml(message)}</p>
        </div>
    `;
    if (typeof lucide !== "undefined") lucide.createIcons();
}

function renderSkeletonCards(container, count = 3) {
    container.innerHTML = Array.from({ length: count }, () =>
        '<div class="card skeleton" style="height:140px"></div>'
    ).join("");
}
