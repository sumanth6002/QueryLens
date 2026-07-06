async function populateWorkspaceSelect(selectElement) {
    const data = await fetchWorkspaces();
    const workspaces = data.workspaces ?? [];
    const selectedValue = selectElement.value;

    selectElement.innerHTML = '<option value="">Select a workspace</option>';
    workspaces.forEach((workspace) => {
        const option = document.createElement("option");
        option.value = workspace.id;
        option.textContent = workspace.name;
        selectElement.appendChild(option);
    });

    if (selectedValue) {
        selectElement.value = selectedValue;
    }

    const params = new URLSearchParams(window.location.search);
    const workspaceFromUrl = params.get("workspace");
    if (workspaceFromUrl) {
        selectElement.value = workspaceFromUrl;
    }

    return workspaces;
}

async function initWorkspaceSelect(selectElement, { onReady } = {}) {
    clearError(document.getElementById("error-banner"));

    try {
        await populateWorkspaceSelect(selectElement);
        if (typeof onReady === "function") {
            await onReady();
        }
    } catch (error) {
        showError(document.getElementById("error-banner"), error.message);
    }
}
