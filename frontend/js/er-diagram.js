mermaid.initialize({
    startOnLoad: false,
    theme: "default",
    er: {
        useMaxWidth: true,
    },
});

document.addEventListener("DOMContentLoaded", () => {
    const workspaceSelect = document.getElementById("workspace-select");
    const loadDiagramBtn = document.getElementById("load-diagram-btn");
    const refreshWorkspacesBtn = document.getElementById("refresh-workspaces-btn");
    const diagramPanel = document.getElementById("diagram-panel");
    const diagramMeta = document.getElementById("diagram-meta");
    const errorBanner = document.getElementById("error-banner");
    const mermaidSource = document.getElementById("mermaid-source");

    function setDiagramMeta(data) {
        if (data.empty) {
            diagramMeta.hidden = true;
            return;
        }

        diagramMeta.hidden = false;
        diagramMeta.innerHTML = `
            <span><strong>Tables:</strong> ${escapeHtml(data.table_count)}</span>
            <span><strong>Relationships:</strong> ${escapeHtml(data.relationship_count)}</span>
            <span><strong>Names:</strong> ${escapeHtml(data.tables.join(", "))}</span>
        `;
    }

    async function renderMermaid(definition) {
        diagramPanel.classList.remove("empty");
        diagramPanel.innerHTML = "";

        const element = document.createElement("div");
        element.className = "mermaid";
        element.textContent = definition;
        diagramPanel.appendChild(element);

        await mermaid.run({ nodes: [element] });
    }

    function showEmptyState(message) {
        diagramPanel.classList.add("empty");
        const paragraph = document.createElement("p");
        paragraph.textContent = message;
        diagramPanel.innerHTML = "";
        diagramPanel.appendChild(paragraph);
        mermaidSource.textContent = "No diagram loaded.";
    }

    async function loadErDiagram() {
        clearError(errorBanner);

        const workspaceId = workspaceSelect.value;
        if (!workspaceId) {
            showError(errorBanner, "Select a workspace first.");
            return;
        }

        setBusy(loadDiagramBtn, true, "Loading...", "Load ER Diagram");

        try {
            const data = await fetchErDiagram(workspaceId);
            setDiagramMeta(data);

            if (data.empty) {
                showEmptyState(data.message);
                return;
            }

            mermaidSource.textContent = data.mermaid;
            await renderMermaid(data.mermaid);
        } catch (error) {
            showError(errorBanner, error.message);
            showEmptyState("Unable to render ER diagram.");
        } finally {
            setBusy(loadDiagramBtn, false, "Loading...", "Load ER Diagram");
        }
    }

    if (loadDiagramBtn) {
        loadDiagramBtn.addEventListener("click", loadErDiagram);
    }

    if (refreshWorkspacesBtn) {
        refreshWorkspacesBtn.addEventListener("click", () => {
            initWorkspaceSelect(workspaceSelect, {
                onReady: async () => {
                    if (workspaceSelect.value) {
                        await loadErDiagram();
                    }
                },
            });
        });
    }

    initWorkspaceSelect(workspaceSelect, {
        onReady: async () => {
            if (workspaceSelect.value) {
                await loadErDiagram();
            }
        },
    });
});
