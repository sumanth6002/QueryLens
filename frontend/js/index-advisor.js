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

    function renderSummary(summary) {
        summaryPanel.innerHTML = `
            <div class="summary-card"><strong>${escapeHtml(summary.total)}</strong><span>Total</span></div>
            <div class="summary-card"><strong>${escapeHtml(summary.high_priority)}</strong><span>High priority</span></div>
            <div class="summary-card"><strong>${escapeHtml(summary.medium_priority)}</strong><span>Medium priority</span></div>
            <div class="summary-card"><strong>${escapeHtml(summary.by_clause.WHERE)}</strong><span>WHERE</span></div>
            <div class="summary-card"><strong>${escapeHtml(summary.by_clause.JOIN)}</strong><span>JOIN</span></div>
        `;
    }

    function renderRecommendations(recommendations) {
        recommendationsList.innerHTML = "";

        if (!recommendations.length) {
            const empty = document.createElement("p");
            empty.textContent = "No index recommendations for this query.";
            recommendationsList.appendChild(empty);
            return;
        }

        recommendations.forEach((item) => {
            const card = document.createElement("article");
            card.className = `recommendation-card ${item.priority}`;

            const title = document.createElement("h3");
            title.textContent = item.index_name;

            const meta = document.createElement("div");
            meta.className = "recommendation-meta";
            meta.textContent = `Table: ${item.table} · Clause: ${item.clause} · Priority: ${item.priority}`;

            const explanation = document.createElement("p");
            explanation.textContent = item.explanation;

            const sql = document.createElement("pre");
            sql.textContent = item.sql;

            card.appendChild(title);
            card.appendChild(meta);
            card.appendChild(explanation);
            card.appendChild(sql);
            recommendationsList.appendChild(card);
        });
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
