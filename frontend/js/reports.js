document.addEventListener("DOMContentLoaded", () => {
    const workspaceSelect = document.getElementById("workspace-select");
    const loadReportsBtn = document.getElementById("load-reports-btn");
    const refreshWorkspacesBtn = document.getElementById("refresh-workspaces-btn");
    const normReportsList = document.getElementById("norm-reports-list");
    const indexReportsList = document.getElementById("index-reports-list");
    const errorBanner = document.getElementById("error-banner");

    function renderNormReports(reports) {
        normReportsList.innerHTML = "";

        if (!reports.length) {
            renderEmptyState(normReportsList, {
                icon: "layers",
                title: "No normalization reports",
                message: "Run normalization analysis and save a report to see it here.",
            });
            return;
        }

        reports.forEach((report) => {
            const item = document.createElement("article");
            item.className = "report-item";

            const forms = report.report_data?.normal_forms || {};
            const passed = Object.values(forms).filter((f) => f.satisfied).length;
            const total = Object.keys(forms).length;

            item.innerHTML = `
                <div class="report-item-header">
                    <h3>Report #${escapeHtml(report.id)}</h3>
                    <span class="report-item-meta">${formatDate(report.created_at)}</span>
                </div>
                <div class="report-item-meta">${escapeHtml(report.attributes?.length || 0)} attributes · ${passed}/${total} forms passed</div>
                <pre>${escapeHtml(JSON.stringify(forms, null, 2))}</pre>
            `;
            normReportsList.appendChild(item);
        });
    }

    function renderIndexReports(records) {
        indexReportsList.innerHTML = "";

        if (!records.length) {
            renderEmptyState(indexReportsList, {
                icon: "zap",
                title: "No saved recommendations",
                message: "Analyze a query in Index Advisor and save to see recommendations here.",
            });
            return;
        }

        records.forEach((record) => {
            const item = document.createElement("article");
            item.className = "report-item";
            const recs = record.recommendation_data?.recommendations || [];

            item.innerHTML = `
                <div class="report-item-header">
                    <h3>Recommendation #${escapeHtml(record.id)}</h3>
                    <span class="report-item-meta">${formatDate(record.created_at)}</span>
                </div>
                <div class="report-item-meta">${escapeHtml(recs.length)} suggested indexes</div>
                <pre>${escapeHtml(record.sql_text)}</pre>
            `;
            indexReportsList.appendChild(item);
        });
    }

    async function loadReports() {
        clearError(errorBanner);

        const workspaceId = workspaceSelect.value;
        if (!workspaceId) {
            showError(errorBanner, "Select a workspace first.");
            return;
        }

        setBusy(loadReportsBtn, true, "Loading...", "Load Reports");
        renderSkeletonCards(normReportsList, 2);
        renderSkeletonCards(indexReportsList, 2);

        try {
            const [normData, indexData] = await Promise.all([
                fetchNormalizationReports(workspaceId),
                fetchIndexRecommendations(workspaceId),
            ]);

            renderNormReports(normData.reports || []);
            renderIndexReports(indexData.recommendations || []);
        } catch (error) {
            showError(errorBanner, error.message);
            normReportsList.innerHTML = "";
            indexReportsList.innerHTML = "";
        } finally {
            setBusy(loadReportsBtn, false, "Loading...", "Load Reports");
        }
    }

    loadReportsBtn?.addEventListener("click", loadReports);

    refreshWorkspacesBtn?.addEventListener("click", () => {
        initWorkspaceSelect(workspaceSelect);
    });

    initWorkspaceSelect(workspaceSelect, {
        onReady: () => {
            if (workspaceSelect.value) {
                loadReports();
            } else {
                renderEmptyState(normReportsList, {
                    icon: "folder-open",
                    title: "Select a workspace",
                    message: "Choose a workspace to load saved reports.",
                });
                renderEmptyState(indexReportsList, {
                    icon: "folder-open",
                    title: "Select a workspace",
                    message: "Choose a workspace to load saved recommendations.",
                });
            }
        },
    });

    workspaceSelect?.addEventListener("change", () => {
        if (workspaceSelect.value) {
            loadReports();
        }
    });
});
