mermaid.initialize({
    startOnLoad: false,
    theme: "dark",
    er: {
        useMaxWidth: true,
    },
});

document.addEventListener("DOMContentLoaded", () => {
    const workspaceSelect = document.getElementById("workspace-select");
    const loadDiagramBtn = document.getElementById("load-diagram-btn");
    const refreshWorkspacesBtn = document.getElementById("refresh-workspaces-btn");
    const diagramPanel = document.getElementById("diagram-panel");
    const diagramViewport = document.getElementById("diagram-viewport");
    const diagramMeta = document.getElementById("diagram-meta");
    const errorBanner = document.getElementById("error-banner");
    const mermaidSource = document.getElementById("mermaid-source");
    const zoomInBtn = document.getElementById("zoom-in-btn");
    const zoomOutBtn = document.getElementById("zoom-out-btn");
    const fitBtn = document.getElementById("fit-btn");
    const exportPngBtn = document.getElementById("export-png-btn");
    const fullscreenBtn = document.getElementById("fullscreen-btn");

    let zoomScale = 1;

    function applyZoom() {
        diagramPanel.style.transform = `scale(${zoomScale})`;
    }

    function setDiagramMeta(data) {
        if (data.empty) {
            diagramMeta.hidden = true;
            return;
        }

        diagramMeta.hidden = false;
        diagramMeta.innerHTML = `
            <span><strong>Tables:</strong> ${escapeHtml(data.table_count)}</span>
            <span><strong>Relationships:</strong> ${escapeHtml(data.relationship_count)}</span>
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
        zoomScale = 1;
        applyZoom();
    }

    function showEmptyState(message) {
        diagramPanel.classList.add("empty");
        diagramPanel.innerHTML = `<p>${escapeHtml(message)}</p>`;
        mermaidSource.textContent = "No diagram loaded.";
        diagramMeta.hidden = true;
    }

    async function loadErDiagram() {
        clearError(errorBanner);

        const workspaceId = workspaceSelect.value;
        if (!workspaceId) {
            showError(errorBanner, "Select a workspace first.");
            return;
        }

        setBusy(loadDiagramBtn, true, "Loading...", "Load");

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
            setBusy(loadDiagramBtn, false, "Loading...", "Load");
        }
    }

    async function exportDiagramPng() {
        const svg = diagramPanel.querySelector("svg");
        if (!svg) {
            showError(errorBanner, "Load a diagram before exporting.");
            return;
        }

        clearError(errorBanner);

        const rect = svg.getBoundingClientRect();
        const clone = svg.cloneNode(true);
        clone.setAttribute("width", rect.width);
        clone.setAttribute("height", rect.height);

        const svgData = new XMLSerializer().serializeToString(clone);
        const canvas = document.createElement("canvas");
        const scale = 2;
        canvas.width = rect.width * scale;
        canvas.height = rect.height * scale;
        const ctx = canvas.getContext("2d");
        ctx.fillStyle = "#050505";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        const img = new Image();
        const url = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svgData)}`;

        await new Promise((resolve, reject) => {
            img.onload = resolve;
            img.onerror = reject;
            img.src = url;
        });

        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

        const link = document.createElement("a");
        link.download = "er-diagram.png";
        link.href = canvas.toDataURL("image/png");
        link.click();
    }

    function toggleFullscreen() {
        const target = diagramViewport;
        if (!document.fullscreenElement) {
            target.requestFullscreen?.();
        } else {
            document.exitFullscreen?.();
        }
    }

    zoomInBtn?.addEventListener("click", () => {
        zoomScale = Math.min(zoomScale + 0.15, 2.5);
        applyZoom();
    });

    zoomOutBtn?.addEventListener("click", () => {
        zoomScale = Math.max(zoomScale - 0.15, 0.4);
        applyZoom();
    });

    fitBtn?.addEventListener("click", () => {
        zoomScale = 1;
        applyZoom();
    });

    exportPngBtn?.addEventListener("click", exportDiagramPng);
    fullscreenBtn?.addEventListener("click", toggleFullscreen);

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
