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

        if (status && dbHealth.ok) {
            status.textContent = "";
            status.classList.remove("is-error");
        } else if (status) {
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

function countRelationships(tables) {
    return tables.reduce((sum, table) => sum + (table.foreign_keys?.length || 0), 0);
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

async function loadWorkspaceList() {
    const list = document.getElementById("workspace-list");
    if (!list) return;

    renderSkeletonCards(list, 3);

    try {
        const data = await fetchWorkspaces();
        const workspaces = data.workspaces ?? [];
        list.innerHTML = "";

        if (!workspaces.length) {
            renderEmptyState(list, {
                icon: "folder-open",
                title: "No workspaces yet",
                message: "Create your first workspace to start designing schemas and analyzing queries.",
            });
            return;
        }

        const stats = await Promise.all(workspaces.map((ws) => loadWorkspaceStats(ws)));

        workspaces.forEach((workspace, index) => {
            const stat = stats[index];
            const card = document.createElement("article");
            card.className = "card workspace-card";
            card.innerHTML = `
                <div class="workspace-card-header">
                    <h3>${escapeHtml(workspace.name)}</h3>
                    <button type="button" class="btn btn-icon btn-secondary workspace-delete" title="Delete" data-id="${workspace.id}" data-name="${escapeHtml(workspace.name)}">
                        <i data-lucide="trash-2"></i>
                    </button>
                </div>
                <div class="workspace-card-meta">
                    <div class="workspace-stat"><span>Tables</span><strong>${stat.tableCount}</strong></div>
                    <div class="workspace-stat"><span>Relationships</span><strong>${stat.relationshipCount}</strong></div>
                    <div class="workspace-stat"><span>Modified</span><strong style="font-size:0.85rem">${formatDate(stat.updatedAt)}</strong></div>
                </div>
                <div class="workspace-card-actions">
                    <a href="pages/schema-builder.html?workspace=${workspace.id}" class="btn btn-primary">Open</a>
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
                    await loadWorkspaceList();
                } catch (error) {
                    const status = document.getElementById("workspace-status");
                    status.textContent = error.message;
                    status.classList.add("is-error");
                }
            });

            list.appendChild(card);
        });

        if (typeof lucide !== "undefined") lucide.createIcons();
    } catch (error) {
        const status = document.getElementById("workspace-status");
        if (status) {
            status.textContent = error.message;
            status.classList.add("is-error");
        }
        list.innerHTML = "";
        renderEmptyState(list, {
            icon: "wifi-off",
            title: "Could not load workspaces",
            message: error.message,
        });
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
        window.location.href = `pages/schema-builder.html?workspace=${data.workspace.id}`;
    } catch (error) {
        status.textContent = error.message;
        status.classList.add("is-error");
    } finally {
        setBusy(createBtn, false, "Creating...", "New Workspace");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    checkHealth();
    loadWorkspaceList();

    const createBtn = document.getElementById("create-workspace-btn");
    const nameInput = document.getElementById("workspace-name");

    createBtn?.addEventListener("click", handleCreateWorkspace);
    nameInput?.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            handleCreateWorkspace();
        }
    });
});
