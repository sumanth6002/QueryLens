const SCAN_COLORS = {
    table_scan: "#ef4444",
    full_index_scan: "#f59e0b",
    index_seek: "#22c55e",
    operation: "#64748b",
    other: "#94a3b8",
};

document.addEventListener("DOMContentLoaded", () => {
    const workspaceSelect = document.getElementById("workspace-select");
    const sqlInput = document.getElementById("sql-input");
    const runExplainBtn = document.getElementById("run-explain-btn");
    const refreshWorkspacesBtn = document.getElementById("refresh-workspaces-btn");
    const treePanel = document.getElementById("tree-panel");
    const summaryPanel = document.getElementById("summary-panel");
    const errorBanner = document.getElementById("error-banner");
    const infoBanner = document.getElementById("info-banner");

    function toD3Hierarchy(node) {
        return {
            name: node.label,
            meta: node,
            children: (node.children || []).map(toD3Hierarchy),
        };
    }

    function renderSummary(summary, executionTimeMs) {
        if (!summary) {
            summaryPanel.hidden = true;
            return;
        }

        summaryPanel.hidden = false;
        summaryPanel.innerHTML = `
            <div class="summary-card"><strong>${escapeHtml(summary.total_tables)}</strong><span>Tables</span></div>
            <div class="summary-card"><strong>${escapeHtml(summary.table_scans)}</strong><span>Table scans</span></div>
            <div class="summary-card"><strong>${escapeHtml(summary.full_index_scans)}</strong><span>Full index scans</span></div>
            <div class="summary-card"><strong>${escapeHtml(summary.index_seeks)}</strong><span>Index seeks</span></div>
            <div class="summary-card"><strong>${escapeHtml(executionTimeMs)} ms</strong><span>Analysis time</span></div>
        `;
    }

    function renderTree(treeData) {
        treePanel.classList.remove("empty");
        treePanel.innerHTML = "";

        const width = Math.max(treePanel.clientWidth, 900);
        const root = d3.hierarchy(toD3Hierarchy(treeData));
        const treeLayout = d3.tree().nodeSize([110, 220]);
        treeLayout(root);

        const nodes = root.descendants();
        const links = root.links();
        const height = Math.max(500, nodes.length * 90);
        const svg = d3.select(treePanel)
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .append("g")
            .attr("transform", "translate(120,40)");

        svg.selectAll(".link")
            .data(links)
            .enter()
            .append("path")
            .attr("class", "link")
            .attr("d", d3.linkHorizontal()
                .x((d) => d.y)
                .y((d) => d.x));

        const node = svg.selectAll(".node")
            .data(nodes)
            .enter()
            .append("g")
            .attr("class", "node")
            .attr("transform", (d) => `translate(${d.y},${d.x})`);

        node.append("circle")
            .attr("r", 14)
            .attr("fill", (d) => SCAN_COLORS[d.data.meta.scan_category] || SCAN_COLORS.other)
            .attr("stroke", "#0f172a");

        node.append("text")
            .attr("dy", -22)
            .attr("x", 18)
            .attr("class", "node-label")
            .text((d) => d.data.name);

        node.append("text")
            .attr("dy", -6)
            .attr("x", 18)
            .attr("class", "node-meta")
            .text((d) => {
                const meta = d.data.meta;
                if (meta.node_type === "table") {
                    const access = meta.access_type || "unknown";
                    const key = meta.key ? ` key=${meta.key}` : "";
                    const rows = meta.rows != null ? ` rows=${meta.rows}` : "";
                    return `${access}${key}${rows}`;
                }
                return "operation";
            });
    }

    function showEmptyState(message) {
        treePanel.classList.add("empty");
        const paragraph = document.createElement("p");
        paragraph.textContent = message;
        treePanel.innerHTML = "";
        treePanel.appendChild(paragraph);
        summaryPanel.hidden = true;
    }

    async function handleRunExplain() {
        clearError(errorBanner);
        clearInfo(infoBanner);

        const workspaceId = workspaceSelect.value;
        const sql = sqlInput.value.trim();

        if (!workspaceId) {
            showError(errorBanner, "Select a workspace first.");
            return;
        }

        if (!sql) {
            showError(errorBanner, "Enter a SELECT query to explain.");
            return;
        }

        setBusy(runExplainBtn, true, "Running...", "Run EXPLAIN");

        try {
            const data = await runExplain(workspaceId, sql);

            if (!data.executed && data.message) {
                showInfo(infoBanner, data.message);
            }

            if (!data.tree) {
                showEmptyState(data.message || "No execution plan available.");
                return;
            }

            renderSummary(data.summary, data.execution_time_ms);
            renderTree(data.tree);
        } catch (error) {
            showError(errorBanner, error.message);
            showEmptyState("Unable to render execution plan.");
        } finally {
            setBusy(runExplainBtn, false, "Running...", "Run EXPLAIN");
        }
    }

    if (runExplainBtn) {
        runExplainBtn.addEventListener("click", handleRunExplain);
    }

    if (refreshWorkspacesBtn) {
        refreshWorkspacesBtn.addEventListener("click", () => {
            initWorkspaceSelect(workspaceSelect);
        });
    }

    initWorkspaceSelect(workspaceSelect);
});
