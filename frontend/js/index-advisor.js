document.addEventListener("DOMContentLoaded", () => {
    const workspaceSelect = document.getElementById("workspace-select");
    const sqlInput = document.getElementById("sql-input");
    const analyzeBtn = document.getElementById("analyze-btn");
    const saveBtn = document.getElementById("save-btn");
    const refreshWorkspacesBtn = document.getElementById("refresh-workspaces-btn");
    const resultsPanel = document.getElementById("results-panel");
    const summaryPanel = document.getElementById("summary-panel");
    const recommendationsList = document.getElementById("recommendations-list");
    const parsedOutput = document.getElementById("parsed-output");
    const errorBanner = document.getElementById("error-banner");
    const infoBanner = document.getElementById("info-banner");

    async function copyText(text) {
        await navigator.clipboard.writeText(text);
        showInfo(infoBanner, "SQL copied to clipboard.");
    }

    function renderSummary(summary) {
        summaryPanel.innerHTML = `
            <div class="metric-card"><strong>${escapeHtml(summary.total)}</strong><span>Total</span></div>
            <div class="metric-card"><strong>${escapeHtml(summary.high_priority)}</strong><span>High priority</span></div>
            <div class="metric-card"><strong>${escapeHtml(summary.medium_priority)}</strong><span>Medium priority</span></div>
            <div class="metric-card"><strong>${escapeHtml(summary.by_clause.WHERE)}</strong><span>WHERE</span></div>
            <div class="metric-card"><strong>${escapeHtml(summary.by_clause.JOIN)}</strong><span>JOIN</span></div>
            <div class="metric-card"><strong>${escapeHtml(summary.by_clause["GROUP BY"])}</strong><span>GROUP BY</span></div>
            <div class="metric-card"><strong>${escapeHtml(summary.by_clause["ORDER BY"])}</strong><span>ORDER BY</span></div>
        `;
    }

    function renderRecommendations(recommendations) {
        recommendationsList.innerHTML = "";

        if (!recommendations.length) {
            renderEmptyState(recommendationsList, {
                icon: "zap",
                title: "No index recommendations",
                message: "This query does not suggest any new indexes based on current analysis.",
            });
            return;
        }

        recommendations.forEach((item) => {
            const card = document.createElement("article");
            card.className = `index-rec-card ${item.priority}`;

            const header = document.createElement("div");
            header.className = "index-rec-header";

            const title = document.createElement("h3");
            title.textContent = item.index_name;

            const copyBtn = document.createElement("button");
            copyBtn.type = "button";
            copyBtn.className = "btn btn-small btn-secondary";
            copyBtn.innerHTML = '<i data-lucide="copy"></i> Copy';
            copyBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                copyText(item.sql);
            });

            header.appendChild(title);
            header.appendChild(copyBtn);

            const meta = document.createElement("div");
            meta.className = "index-rec-meta";
            meta.textContent = `Table: ${item.table} · Clause: ${item.clause} · Priority: ${item.priority}`;

            const reason = document.createElement("p");
            reason.className = "index-rec-reason";
            reason.textContent = item.explanation;

            const sqlWrap = document.createElement("div");
            sqlWrap.className = "index-rec-sql";
            const sql = document.createElement("pre");
            sql.textContent = item.sql;
            sqlWrap.appendChild(sql);

            card.appendChild(header);
            card.appendChild(meta);
            card.appendChild(reason);
            card.appendChild(sqlWrap);
            recommendationsList.appendChild(card);
        });

        if (typeof lucide !== "undefined") lucide.createIcons();
    }

    async function handleAnalyze(save) {
        clearError(errorBanner);
        clearInfo(infoBanner);

        const workspaceId = workspaceSelect.value;
        const sql = sqlInput.value.trim();

        if (!workspaceId) {
            showError(errorBanner, "Select a workspace first.");
            return;
        }

        if (!sql) {
            showError(errorBanner, "Enter a SELECT query to analyze.");
            return;
        }

        const activeButton = save ? saveBtn : analyzeBtn;
        const label = save ? "Analyze & Save" : "Analyze Indexes";
        setBusy(activeButton, true, "Analyzing...", label);

        try {
            const data = await analyzeIndexes(workspaceId, sql, save);
            resultsPanel.hidden = false;
            renderSummary(data.summary);
            renderRecommendations(data.recommendations);
            parsedOutput.textContent = JSON.stringify({
                where: data.parsed_query.where,
                joins: data.parsed_query.joins,
                group_by: data.parsed_query.group_by,
                order_by: data.parsed_query.order_by,
            }, null, 2);

            if (data.recommendation_id) {
                showInfo(infoBanner, `Recommendation saved with id ${data.recommendation_id}.`);
            }
        } catch (error) {
            showError(errorBanner, error.message);
        } finally {
            setBusy(activeButton, false, "Analyzing...", label);
        }
    }

    if (analyzeBtn) {
        analyzeBtn.addEventListener("click", () => handleAnalyze(false));
    }

    if (saveBtn) {
        saveBtn.addEventListener("click", () => handleAnalyze(true));
    }

    if (refreshWorkspacesBtn) {
        refreshWorkspacesBtn.addEventListener("click", () => {
            initWorkspaceSelect(workspaceSelect);
        });
    }

    initWorkspaceSelect(workspaceSelect);
});
