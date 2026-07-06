document.addEventListener("DOMContentLoaded", () => {
    const workspaceSelect = document.getElementById("workspace-select");
    const analyzeBtn = document.getElementById("analyze-btn");
    const saveReportBtn = document.getElementById("save-report-btn");
    const refreshWorkspacesBtn = document.getElementById("refresh-workspaces-btn");
    const resultsPanel = document.getElementById("results-panel");
    const keysSummary = document.getElementById("keys-summary");
    const normalForms = document.getElementById("normal-forms");
    const closureOutput = document.getElementById("closure-output");
    const errorBanner = document.getElementById("error-banner");
    const infoBanner = document.getElementById("info-banner");

    function parseAttributes(text) {
        return text
            .split(/\r?\n/)
            .map((line) => line.trim())
            .filter(Boolean);
    }

    function parseCommaSeparated(text) {
        return text
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean);
    }

    function buildPayload(saveReport) {
        const attributes = parseAttributes(document.getElementById("attributes-input").value);
        let functional_dependencies;

        try {
            functional_dependencies = JSON.parse(document.getElementById("fds-input").value);
        } catch (error) {
            throw new Error("Functional dependencies must be valid JSON.");
        }

        const multivalued_attributes = parseCommaSeparated(
            document.getElementById("multivalued-input").value
        );
        const closure_of = parseCommaSeparated(document.getElementById("closure-input").value);

        const payload = {
            attributes,
            functional_dependencies,
            multivalued_attributes,
            save_report: saveReport,
        };

        if (closure_of.length) {
            payload.closure_of = closure_of;
        }

        return payload;
    }

    function renderNormalForm(name, result) {
        const card = document.createElement("article");
        card.className = `norm-card ${result.satisfied ? "pass" : "fail"}`;

        const badge = document.createElement("span");
        badge.className = `badge ${result.satisfied ? "pass" : "fail"}`;
        badge.textContent = result.satisfied ? "Passed" : "Failed";

        const title = document.createElement("h3");
        title.textContent = name;

        const summary = document.createElement("p");
        summary.className = "norm-summary";
        summary.textContent = result.satisfied ? "All requirements satisfied." : "Violations detected.";

        const details = document.createElement("div");
        details.className = "norm-details";
        details.hidden = true;

        const explanation = document.createElement("p");
        explanation.textContent = result.explanation;
        details.appendChild(explanation);

        if (result.violations?.length) {
            const list = document.createElement("ul");
            list.className = "violation-list";
            result.violations.forEach((violation) => {
                const item = document.createElement("li");
                item.textContent = violation.explanation;
                list.appendChild(item);
            });
            details.appendChild(list);
        }

        card.appendChild(badge);
        card.appendChild(title);
        card.appendChild(summary);
        card.appendChild(details);

        card.addEventListener("click", () => {
            details.hidden = !details.hidden;
        });

        return card;
    }

    function formatKeyList(keys) {
        return keys.map((key) => `[${key.join(", ")}]`).join(", ");
    }

    function renderResults(analysis) {
        resultsPanel.hidden = false;

        keysSummary.innerHTML = `
            <p><strong>Candidate Keys:</strong> ${escapeHtml(formatKeyList(analysis.candidate_keys))}</p>
            <p><strong>Superkeys:</strong> ${escapeHtml(formatKeyList(analysis.superkeys.slice(0, 8)))}${analysis.superkeys.length > 8 ? " ..." : ""}</p>
            <p><strong>Prime Attributes:</strong> ${escapeHtml(analysis.prime_attributes.join(", ") || "None")}</p>
            <p><strong>Non-prime Attributes:</strong> ${escapeHtml(analysis.non_prime_attributes.join(", ") || "None")}</p>
            ${analysis.requested_closure ? `<p><strong>Closure(${escapeHtml(analysis.requested_closure.seed.join(", "))}):</strong> ${escapeHtml(analysis.requested_closure.closure.join(", "))}</p>` : ""}
        `;

        normalForms.innerHTML = "";
        Object.entries(analysis.normal_forms).forEach(([name, result]) => {
            normalForms.appendChild(renderNormalForm(name, result));
        });

        closureOutput.textContent = JSON.stringify(analysis.attribute_closure, null, 2);
    }

    async function handleAnalyze(saveReport) {
        clearError(errorBanner);
        clearInfo(infoBanner);

        const workspaceId = workspaceSelect.value;
        if (!workspaceId) {
            showError(errorBanner, "Select a workspace first.");
            return;
        }

        const activeButton = saveReport ? saveReportBtn : analyzeBtn;
        const label = saveReport ? "Analyze & Save Report" : "Analyze";
        setBusy(activeButton, true, "Analyzing...", label);

        try {
            const payload = buildPayload(saveReport);
            const data = await analyzeNormalization(workspaceId, payload);
            renderResults(data.analysis);

            if (data.report_id) {
                showInfo(infoBanner, `Report saved with id ${data.report_id}.`);
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

    if (saveReportBtn) {
        saveReportBtn.addEventListener("click", () => handleAnalyze(true));
    }

    if (refreshWorkspacesBtn) {
        refreshWorkspacesBtn.addEventListener("click", () => {
            initWorkspaceSelect(workspaceSelect);
        });
    }

    initWorkspaceSelect(workspaceSelect);
});
