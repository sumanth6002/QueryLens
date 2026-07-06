async function apiRequest(path, options = {}) {
    const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {}),
    };

    let response;
    try {
        response = await fetch(`${API_BASE_URL}${path}`, {
            ...options,
            headers,
            signal: options.signal || AbortSignal.timeout(30000),
        });
    } catch (error) {
        if (error.name === "TimeoutError") {
            throw new Error("Request timed out. The server may be busy or unreachable.");
        }
        throw new Error(
            `Cannot reach the API at ${API_BASE_URL}. Start the backend with: cd backend && python app.py`
        );
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        const message = data.message || data.error || `Request failed (${response.status})`;
        throw new Error(message);
    }

    return data;
}

async function fetchHealth() {
    return apiRequest("/api/health");
}

async function fetchDbHealth() {
    const response = await fetch(`${API_BASE_URL}/api/health/db`, {
        signal: AbortSignal.timeout(10000),
    });
    const data = await response.json().catch(() => ({}));
    return { ok: response.ok, data };
}

async function fetchWorkspaces() {
    return apiRequest("/api/workspaces");
}

async function createWorkspace(name, description = "") {
    return apiRequest("/api/workspaces", {
        method: "POST",
        body: JSON.stringify({ name, description }),
    });
}

async function fetchSchema(workspaceId) {
    return apiRequest(`/api/workspaces/${workspaceId}/schema`);
}

async function createTable(workspaceId, payload) {
    return apiRequest(`/api/workspaces/${workspaceId}/schema/tables`, {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

async function updateTable(workspaceId, tableName, payload) {
    return apiRequest(`/api/workspaces/${workspaceId}/schema/tables/${encodeURIComponent(tableName)}`, {
        method: "PUT",
        body: JSON.stringify(payload),
    });
}

async function deleteTable(workspaceId, tableName) {
    return apiRequest(`/api/workspaces/${workspaceId}/schema/tables/${encodeURIComponent(tableName)}`, {
        method: "DELETE",
    });
}

async function previewSchemaSql(workspaceId, tableName = null) {
    const query = tableName ? `?table=${encodeURIComponent(tableName)}` : "";
    return apiRequest(`/api/workspaces/${workspaceId}/schema/sql${query}`);
}

async function fetchErDiagram(workspaceId) {
    return apiRequest(`/api/workspaces/${workspaceId}/schema/er-diagram`);
}

async function runExplain(workspaceId, sql) {
    return apiRequest(`/api/workspaces/${workspaceId}/explain`, {
        method: "POST",
        body: JSON.stringify({ sql }),
    });
}

async function analyzeNormalization(workspaceId, payload) {
    return apiRequest(`/api/workspaces/${workspaceId}/normalization/analyze`, {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

async function analyzeIndexes(workspaceId, sql, save = false) {
    return apiRequest(`/api/workspaces/${workspaceId}/index-advisor/analyze`, {
        method: "POST",
        body: JSON.stringify({ sql, save }),
    });
}
