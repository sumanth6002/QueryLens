const WORKSPACE_STORAGE_KEY = "querylens_workspace_id";

let workspacesCache = [];
let selectedWorkspaceId = null;

function formatRelativeTime(iso) {
    if (!iso) return "—";
    const then = new Date(iso).getTime();
    if (Number.isNaN(then)) return "—";

    const diffMs = Date.now() - then;
    const mins = Math.floor(diffMs / 60000);

    if (mins < 1) return "just now";
    if (mins < 60) return `${mins} min ago`;

    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours} hr ago`;

    const days = Math.floor(hours / 24);
    if (days < 7) return `${days} day${days === 1 ? "" : "s"} ago`;

    return formatDate(iso);
}

function countRelationships(tables) {
    return tables.reduce((sum, table) => sum + (table.foreign_keys?.length || 0), 0);
}

function workspaceUrl(path, workspaceId) {
    if (!workspaceId) return path;
    const separator = path.includes("?") ? "&" : "?";
    return `${path}${separator}workspace=${workspaceId}`;
}

function getSelectedWorkspaceId() {
    return selectedWorkspaceId || localStorage.getItem(WORKSPACE_STORAGE_KEY) || "";
}

function setSelectedWorkspaceId(id) {
    selectedWorkspaceId = id ? String(id) : "";
    if (selectedWorkspaceId) {
        localStorage.setItem(WORKSPACE_STORAGE_KEY, selectedWorkspaceId);
    } else {
        localStorage.removeItem(WORKSPACE_STORAGE_KEY);
    }
}

async function loadWorkspaceStats(workspace) {
    try {
        const schema = await fetchSchema(workspace.id);
        const tables = schema.schema_data?.tables || [];
        return {
            tableCount: tables.length,
            relationshipCount: countRelationships(tables),
            updatedAt: schema.updated_at || workspace.updated_at,
        };
    } catch {
        return {
            tableCount: 0,
            relationshipCount: 0,
            updatedAt: workspace.updated_at,
        };
    }
}

function updateQuickActionLinks(workspaceId) {
    const links = {
        "action-new-table": "pages/schema-builder.html",
        "action-schema-builder": "pages/schema-builder.html",
        "action-er-diagram": "pages/er-diagram.html",
        "action-explain": "pages/explain.html",
    };

    Object.entries(links).forEach(([id, path]) => {
        const el = document.getElementById(id);
        if (el) el.href = workspaceUrl(path, workspaceId);
    });
}

function populateWorkspaceSelect(workspaces) {
    const select = document.getElementById("dashboard-workspace-select");
    if (!select) return;

    const previous = getSelectedWorkspaceId();
    select.innerHTML = '<option value="">Select workspace</option>';

    workspaces.forEach((workspace) => {
        const option = document.createElement("option");
        option.value = workspace.id;
        option.textContent = workspace.name;
        select.appendChild(option);
    });

    if (previous && workspaces.some((ws) => String(ws.id) === String(previous))) {
        select.value = previous;
    } else if (workspaces.length === 1) {
        select.value = String(workspaces[0].id);
    }

    setSelectedWorkspaceId(select.value);
}

async function renderCurrentWorkspace(workspace, stats) {
    const panel = document.getElementById("current-workspace-panel");
    const empty = document.getElementById("current-workspace-empty");

    if (!workspace) {
        panel.hidden = true;
        empty.hidden = false;
        updateQuickActionLinks(null);
        renderActivity(null);
        return;
    }

    panel.hidden = false;
    empty.hidden = true;

    document.getElementById("current-workspace-name").textContent = workspace.name;
    document.getElementById("current-workspace-updated").textContent =
        `Updated ${formatRelativeTime(stats.updatedAt)}`;
    document.getElementById("stat-tables").textContent = stats.tableCount;
    document.getElementById("stat-relationships").textContent = stats.relationshipCount;
    document.getElementById("stat-modified").textContent = formatRelativeTime(stats.updatedAt);

    updateQuickActionLinks(workspace.id);
    await renderActivity(workspace.id);
}

function renderGettingStarted(hasWorkspaces) {
    const section = document.getElementById("getting-started");
    if (section) section.hidden = hasWorkspaces;
}

function renderCompactWorkspaceList(workspaces, statsList) {
    const list = document.getElementById("workspace-list");
    if (!list) return;

    list.innerHTML = "";

    if (!workspaces.length) {
        list.innerHTML = `
            <div class="dash-ws-empty">
                <i data-lucide="folder-open"></i>
                <h3>No workspaces yet</h3>
                <p>Create your first workspace above to start building schemas.</p>
            </div>
        `;
        if (typeof lucide !== "undefined") lucide.createIcons();
        return;
    }

    const sorted = workspaces
        .map((ws, index) => ({ workspace: ws, stats: statsList[index] }))
        .sort((a, b) => new Date(b.stats.updatedAt) - new Date(a.stats.updatedAt));

    sorted.forEach(({ workspace, stats }) => {
        const card = document.createElement("article");
        card.className = "dash-ws-card";
        card.innerHTML = `
            <div class="dash-ws-card-main">
                <h3>${escapeHtml(workspace.name)}</h3>
                <p>${stats.tableCount} table${stats.tableCount === 1 ? "" : "s"} · ${formatRelativeTime(stats.updatedAt)}</p>
            </div>
            <div class="dash-ws-card-actions">
                <a href="${workspaceUrl("pages/schema-builder.html", workspace.id)}" class="btn btn-small btn-primary">Open</a>
                <button type="button" class="btn btn-icon btn-secondary workspace-delete" title="Delete">
                    <i data-lucide="trash-2"></i>
                </button>
            </div>
        `;

        card.querySelector(".workspace-delete").addEventListener("click", async () => {
            const confirmed = await showConfirm({
                title: "Delete workspace",
                message: `Delete "${workspace.name}"? This cannot be undone.`,
                confirmLabel: "Delete",
                danger: true,
            });
            if (!confirmed) return;

            try {
                await deleteWorkspace(workspace.id);
                if (String(getSelectedWorkspaceId()) === String(workspace.id)) {
                    setSelectedWorkspaceId("");
                }
                await refreshDashboard();
            } catch (error) {
                const status = document.getElementById("workspace-status");
                status.textContent = error.message;
                status.classList.add("is-error");
            }
        });

        list.appendChild(card);
    });

    if (typeof lucide !== "undefined") lucide.createIcons();
}

async function renderActivity(workspaceId) {
    const container = document.getElementById("activity-list");
    if (!container) return;

    if (!workspaceId) {
        container.innerHTML = `
            <div class="dash-activity-empty">
                <i data-lucide="clock"></i>
                <span>No recent activity.</span>
            </div>
        `;
        if (typeof lucide !== "undefined") lucide.createIcons();
        return;
    }

    container.innerHTML = `<div class="dash-activity-empty"><span>Loading…</span></div>`;

    try {
        const [normData, indexData] = await Promise.all([
            fetchNormalizationReports(workspaceId).catch(() => ({ reports: [] })),
            fetchIndexRecommendations(workspaceId).catch(() => ({ recommendations: [] })),
        ]);

        const activities = [];

        (normData.reports || []).forEach((report) => {
            activities.push({
                type: "Normalization report",
                detail: `Report #${report.id}`,
                time: report.created_at,
            });
        });

        (indexData.recommendations || []).forEach((rec) => {
            activities.push({
                type: "Index recommendation",
                detail: `Recommendation #${rec.id}`,
                time: rec.created_at,
            });
        });

        activities.sort((a, b) => new Date(b.time) - new Date(a.time));
        const recent = activities.slice(0, 6);

        if (!recent.length) {
            container.innerHTML = `
                <div class="dash-activity-empty">
                    <i data-lucide="clock"></i>
                    <span>No recent activity.</span>
                </div>
            `;
        } else {
            container.innerHTML = recent.map((item) => `
                <div class="dash-activity-item">
                    <strong>${escapeHtml(item.type)}</strong>
                    <span>${escapeHtml(item.detail)} · ${formatRelativeTime(item.time)}</span>
                </div>
            `).join("");
        }

        if (typeof lucide !== "undefined") lucide.createIcons();
    } catch {
        container.innerHTML = `
            <div class="dash-activity-empty">
                <i data-lucide="clock"></i>
                <span>No recent activity.</span>
            </div>
        `;
        if (typeof lucide !== "undefined") lucide.createIcons();
    }
}

async function refreshDashboard() {
    const list = document.getElementById("workspace-list");
    if (list) {
        renderSkeletonCards(list, 3);
    }

    try {
        const data = await fetchWorkspaces();
        workspacesCache = data.workspaces ?? [];

        populateWorkspaceSelect(workspacesCache);
        renderGettingStarted(workspacesCache.length > 0);

        const statsList = await Promise.all(workspacesCache.map((ws) => loadWorkspaceStats(ws)));
        renderCompactWorkspaceList(workspacesCache, statsList);

        const selectedId = getSelectedWorkspaceId();
        const selectedWorkspace = workspacesCache.find((ws) => String(ws.id) === String(selectedId));
        const selectedStats = selectedWorkspace
            ? statsList[workspacesCache.indexOf(selectedWorkspace)]
            : null;

        await renderCurrentWorkspace(selectedWorkspace || null, selectedStats || {});
    } catch (error) {
        const status = document.getElementById("workspace-status");
        if (status) {
            status.textContent = error.message;
            status.classList.add("is-error");
        }

        if (list) {
            list.innerHTML = "";
            renderEmptyState(list, {
                icon: "wifi-off",
                title: "Could not load workspaces",
                message: error.message,
            });
        }
    }
}

async function checkHealth() {
    const status = document.getElementById("workspace-status");
    const apiStatus = document.getElementById("api-status");

    try {
        await fetchHealth();
        const dbHealth = await fetchDbHealth();

        if (apiStatus) {
            apiStatus.textContent = dbHealth.ok ? "API connected" : "DB unavailable";
            apiStatus.classList.toggle("is-ok", dbHealth.ok);
            apiStatus.classList.toggle("is-error", !dbHealth.ok);
        }

        if (status && !dbHealth.ok) {
            status.textContent = dbHealth.data.message || "Database unavailable";
            status.classList.add("is-error");
        }
    } catch (error) {
        if (status) {
            status.textContent = error.message;
            status.classList.add("is-error");
        }
        if (apiStatus) {
            apiStatus.textContent = "Offline";
            apiStatus.classList.add("is-error");
        }
    }
}

async function handleCreateWorkspace() {
    const nameInput = document.getElementById("workspace-name");
    const status = document.getElementById("workspace-status");
    const createBtn = document.getElementById("create-workspace-btn");
    const name = nameInput.value.trim();

    if (!name) {
        status.textContent = "Enter a workspace name.";
        status.classList.add("is-error");
        return;
    }

    setBusy(createBtn, true, "Creating...", "New Workspace");
    status.textContent = "";
    status.classList.remove("is-error");

    try {
        const data = await createWorkspace(name);
        setSelectedWorkspaceId(data.workspace.id);
        nameInput.value = "";
        window.location.href = workspaceUrl("pages/schema-builder.html", data.workspace.id);
    } catch (error) {
        status.textContent = error.message;
        status.classList.add("is-error");
    } finally {
        setBusy(createBtn, false, "Creating...", "New Workspace");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    checkHealth();
    refreshDashboard();

    const createBtn = document.getElementById("create-workspace-btn");
    const nameInput = document.getElementById("workspace-name");
    const workspaceSelect = document.getElementById("dashboard-workspace-select");

    createBtn?.addEventListener("click", handleCreateWorkspace);
    nameInput?.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            handleCreateWorkspace();
        }
    });

    workspaceSelect?.addEventListener("change", async () => {
        setSelectedWorkspaceId(workspaceSelect.value);

        const workspace = workspacesCache.find(
            (ws) => String(ws.id) === String(workspaceSelect.value)
        );

        if (workspace) {
            const stats = await loadWorkspaceStats(workspace);
            await renderCurrentWorkspace(workspace, stats);
        } else {
            await renderCurrentWorkspace(null, {});
        }
    });
});
