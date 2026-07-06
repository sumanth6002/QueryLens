async function checkHealth() {
    const status = document.getElementById("workspace-status");
    if (!status) {
        return;
    }

    try {
        await fetchHealth();
        const dbHealth = await fetchDbHealth();

        if (dbHealth.ok) {
            status.textContent = "API connected. Create a workspace to get started.";
            status.classList.remove("home-status-error");
        } else {
            const message = dbHealth.data.message || "check backend logs";
            status.textContent = `API is running but the database is unavailable: ${message}`;
            status.classList.add("home-status-error");
        }
    } catch (error) {
        status.textContent = error.message;
        status.classList.add("home-status-error");
    }
}

async function handleCreateWorkspace() {
    const nameInput = document.getElementById("workspace-name");
    const status = document.getElementById("workspace-status");
    const createBtn = document.getElementById("create-workspace-btn");
    const name = nameInput.value.trim();

    if (!name) {
        status.textContent = "Enter a workspace name.";
        status.classList.add("home-status-error");
        return;
    }

    setBusy(createBtn, true, "Creating...", "Create Workspace");
    status.textContent = "Creating workspace...";
    status.classList.remove("home-status-error");

    try {
        const data = await createWorkspace(name);
        window.location.href = `pages/schema-builder.html?workspace=${data.workspace.id}`;
    } catch (error) {
        status.textContent = error.message;
        status.classList.add("home-status-error");
    } finally {
        setBusy(createBtn, false, "Creating...", "Create Workspace");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    checkHealth();

    const createBtn = document.getElementById("create-workspace-btn");
    const nameInput = document.getElementById("workspace-name");

    if (createBtn) {
        createBtn.addEventListener("click", handleCreateWorkspace);
    }

    if (nameInput) {
        nameInput.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                handleCreateWorkspace();
            }
        });
    }
});
