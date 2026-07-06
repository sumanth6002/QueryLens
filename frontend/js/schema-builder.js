const DATA_TYPES = [
    "INT",
    "BIGINT",
    "SMALLINT",
    "TINYINT",
    "VARCHAR(255)",
    "CHAR(10)",
    "TEXT",
    "BOOLEAN",
    "DATE",
    "DATETIME",
    "TIMESTAMP",
    "DECIMAL(10,2)",
    "FLOAT",
    "DOUBLE",
];

const ON_DELETE_OPTIONS = ["RESTRICT", "CASCADE", "SET NULL", "NO ACTION"];

document.addEventListener("DOMContentLoaded", () => {
    const workspaceSelect = document.getElementById("workspace-select");
    const loadSchemaBtn = document.getElementById("load-schema-btn");
    const refreshWorkspacesBtn = document.getElementById("refresh-workspaces-btn");
    const erDiagramLink = document.getElementById("er-diagram-link");
    const tableList = document.getElementById("table-list");
    const editorPanel = document.getElementById("editor-panel");
    const editorTitle = document.getElementById("editor-title");
    const tableNameInput = document.getElementById("table-name-input");
    const columnsBody = document.getElementById("columns-body");
    const fkList = document.getElementById("fk-list");
    const newTableBtn = document.getElementById("new-table-btn");
    const addColumnBtn = document.getElementById("add-column-btn");
    const addFkBtn = document.getElementById("add-fk-btn");
    const saveTableBtn = document.getElementById("save-table-btn");
    const deleteTableBtn = document.getElementById("delete-table-btn");
    const previewSqlBtn = document.getElementById("preview-sql-btn");
    const sqlPreviewPanel = document.getElementById("sql-preview-panel");
    const sqlPreviewOutput = document.getElementById("sql-preview-output");
    const errorBanner = document.getElementById("error-banner");
    const infoBanner = document.getElementById("info-banner");

    let schemaTables = [];
    let editingTableName = null;

    function updateErDiagramLink() {
        const workspaceId = workspaceSelect.value;
        erDiagramLink.href = workspaceId
            ? `er-diagram.html?workspace=${workspaceId}`
            : "er-diagram.html";
    }

    function blankColumn() {
        return {
            name: "",
            data_type: "INT",
            nullable: true,
            auto_increment: false,
            is_pk: false,
        };
    }

    function createTypeSelect(selectedType) {
        const select = document.createElement("select");
        DATA_TYPES.forEach((type) => {
            const option = document.createElement("option");
            option.value = type;
            option.textContent = type;
            if (type === selectedType) {
                option.selected = true;
            }
            select.appendChild(option);
        });
        return select;
    }

    function renderColumns(columns) {
        columnsBody.innerHTML = "";

        if (!columns.length) {
            columns.push(blankColumn());
        }

        columns.forEach((column, index) => {
            const row = document.createElement("tr");

            const nameCell = document.createElement("td");
            const nameInput = document.createElement("input");
            nameInput.type = "text";
            nameInput.value = column.name;
            nameInput.placeholder = "column_name";
            nameCell.appendChild(nameInput);

            const typeCell = document.createElement("td");
            const typeSelect = createTypeSelect(column.data_type);
            typeCell.appendChild(typeSelect);

            const pkCell = document.createElement("td");
            const pkInput = document.createElement("input");
            pkInput.type = "checkbox";
            pkInput.checked = Boolean(column.is_pk);
            pkCell.appendChild(pkInput);

            const nullableCell = document.createElement("td");
            const nullableInput = document.createElement("input");
            nullableInput.type = "checkbox";
            nullableInput.checked = column.nullable !== false;
            nullableCell.appendChild(nullableInput);

            const autoIncCell = document.createElement("td");
            const autoIncInput = document.createElement("input");
            autoIncInput.type = "checkbox";
            autoIncInput.checked = Boolean(column.auto_increment);
            autoIncCell.appendChild(autoIncInput);

            const removeCell = document.createElement("td");
            const removeBtn = document.createElement("button");
            removeBtn.type = "button";
            removeBtn.className = "btn btn-small btn-secondary btn-icon";
            removeBtn.textContent = "×";
            removeBtn.title = "Remove column";
            removeBtn.addEventListener("click", () => {
                row.remove();
                if (!columnsBody.children.length) {
                    renderColumns([blankColumn()]);
                }
            });
            removeCell.appendChild(removeBtn);

            row.dataset.index = String(index);
            row.append(nameCell, typeCell, pkCell, nullableCell, autoIncCell, removeCell);
            columnsBody.appendChild(row);
        });
    }

    function getColumnNamesFromEditor() {
        return Array.from(columnsBody.querySelectorAll("tr"))
            .map((row) => row.querySelector('input[type="text"]').value.trim())
            .filter(Boolean);
    }

    function getOtherTableNames(excludeName = null) {
        return schemaTables
            .map((table) => table.name)
            .filter((name) => name !== excludeName);
    }

    function renderForeignKeys(foreignKeys, tableName) {
        fkList.innerHTML = "";

        const otherTables = getOtherTableNames(tableName);
        if (!foreignKeys.length) {
            return;
        }

        foreignKeys.forEach((foreignKey) => {
            fkList.appendChild(createFkRow(foreignKey, otherTables));
        });
    }

    function createFkRow(foreignKey = {}, otherTables = []) {
        const row = document.createElement("div");
        row.className = "fk-row";

        const nameLabel = document.createElement("label");
        nameLabel.textContent = "Name (optional)";
        const nameInput = document.createElement("input");
        nameInput.type = "text";
        nameInput.value = foreignKey.name || "";
        nameInput.placeholder = "fk_users_role";
        nameLabel.appendChild(nameInput);

        const columnLabel = document.createElement("label");
        columnLabel.textContent = "Column";
        const columnSelect = document.createElement("select");
        getColumnNamesFromEditor().forEach((columnName) => {
            const option = document.createElement("option");
            option.value = columnName;
            option.textContent = columnName;
            if (columnName === (foreignKey.columns?.[0] || "")) {
                option.selected = true;
            }
            columnSelect.appendChild(option);
        });
        columnLabel.appendChild(columnSelect);

        const refTableLabel = document.createElement("label");
        refTableLabel.textContent = "References Table";
        const refTableSelect = document.createElement("select");
        otherTables.forEach((tableName) => {
            const option = document.createElement("option");
            option.value = tableName;
            option.textContent = tableName;
            if (tableName === foreignKey.referenced_table) {
                option.selected = true;
            }
            refTableSelect.appendChild(option);
        });
        refTableLabel.appendChild(refTableSelect);

        const refColumnLabel = document.createElement("label");
        refColumnLabel.textContent = "References Column";
        const refColumnSelect = document.createElement("select");
        const referencedTable = foreignKey.referenced_table || otherTables[0];
        const referencedTableData = schemaTables.find((table) => table.name === referencedTable);
        (referencedTableData?.columns || []).forEach((column) => {
            const option = document.createElement("option");
            option.value = column.name;
            option.textContent = column.name;
            if (column.name === (foreignKey.referenced_columns?.[0] || "")) {
                option.selected = true;
            }
            refColumnSelect.appendChild(option);
        });
        refColumnLabel.appendChild(refColumnSelect);

        refTableSelect.addEventListener("change", () => {
            const selectedTable = schemaTables.find((table) => table.name === refTableSelect.value);
            refColumnSelect.innerHTML = "";
            (selectedTable?.columns || []).forEach((column) => {
                const option = document.createElement("option");
                option.value = column.name;
                option.textContent = column.name;
                refColumnSelect.appendChild(option);
            });
        });

        const onDeleteLabel = document.createElement("label");
        onDeleteLabel.textContent = "On Delete";
        const onDeleteSelect = document.createElement("select");
        ON_DELETE_OPTIONS.forEach((value) => {
            const option = document.createElement("option");
            option.value = value;
            option.textContent = value;
            if (value === (foreignKey.on_delete || "RESTRICT")) {
                option.selected = true;
            }
            onDeleteSelect.appendChild(option);
        });
        onDeleteLabel.appendChild(onDeleteSelect);

        const removeBtn = document.createElement("button");
        removeBtn.type = "button";
        removeBtn.className = "btn btn-small btn-secondary btn-icon";
        removeBtn.textContent = "×";
        removeBtn.title = "Remove foreign key";
        removeBtn.addEventListener("click", () => row.remove());

        row.append(nameLabel, columnLabel, refTableLabel, refColumnLabel, onDeleteLabel, removeBtn);
        return row;
    }

    function readColumnsFromEditor() {
        return Array.from(columnsBody.querySelectorAll("tr")).map((row) => {
            const cells = row.querySelectorAll("td");
            return {
                name: cells[0].querySelector("input").value.trim(),
                data_type: cells[1].querySelector("select").value,
                is_pk: cells[2].querySelector("input").checked,
                nullable: cells[3].querySelector("input").checked,
                auto_increment: cells[4].querySelector("input").checked,
            };
        });
    }

    function readForeignKeysFromEditor() {
        return Array.from(fkList.querySelectorAll(".fk-row")).map((row) => {
            const inputs = row.querySelectorAll("input, select");
            const payload = {
                columns: [inputs[1].value],
                referenced_table: inputs[2].value,
                referenced_columns: [inputs[3].value],
                on_delete: inputs[4].value,
            };
            if (inputs[0].value.trim()) {
                payload.name = inputs[0].value.trim();
            }
            return payload;
        });
    }

    function buildTablePayload() {
        const columns = readColumnsFromEditor();
        const tableName = tableNameInput.value.trim();

        if (!tableName) {
            throw new Error("Table name is required.");
        }

        if (!columns.length) {
            throw new Error("Add at least one column.");
        }

        const primaryKey = columns.filter((column) => column.is_pk).map((column) => column.name);
        const foreignKeys = readForeignKeysFromEditor();

        return {
            name: tableName,
            columns: columns.map((column) => ({
                name: column.name,
                data_type: column.data_type,
                nullable: column.nullable,
                auto_increment: column.auto_increment,
            })),
            primary_key: primaryKey,
            foreign_keys: foreignKeys,
        };
    }

    function renderTableList() {
        tableList.innerHTML = "";

        if (!schemaTables.length) {
            const emptyItem = document.createElement("li");
            emptyItem.className = "table-list-empty";
            emptyItem.textContent = "No tables yet. Click “New Table” to add one.";
            tableList.appendChild(emptyItem);
            return;
        }

        schemaTables.forEach((table) => {
            const item = document.createElement("li");
            const button = document.createElement("button");
            button.type = "button";
            button.className = "table-list-item";
            if (table.name === editingTableName) {
                button.classList.add("active");
            }

            const columnCount = table.columns?.length || 0;
            const fkCount = table.foreign_keys?.length || 0;
            button.innerHTML = `
                <span>${escapeHtml(table.name)}</span>
                <span class="table-list-item-meta">${columnCount} column${columnCount === 1 ? "" : "s"}, ${fkCount} FK${fkCount === 1 ? "" : "s"}</span>
            `;
            button.addEventListener("click", () => loadTableIntoEditor(table.name));
            item.appendChild(button);
            tableList.appendChild(item);
        });
    }

    function loadTableIntoEditor(tableName) {
        const table = schemaTables.find((entry) => entry.name === tableName);
        if (!table) {
            return;
        }

        editingTableName = table.name;
        editorPanel.hidden = false;
        editorTitle.textContent = `Edit Table: ${table.name}`;
        tableNameInput.value = table.name;
        deleteTableBtn.hidden = false;

        const primaryKeys = new Set(table.primary_key || []);
        renderColumns(
            table.columns.map((column) => ({
                ...column,
                is_pk: primaryKeys.has(column.name),
            }))
        );
        renderForeignKeys(table.foreign_keys || [], table.name);
        renderTableList();
        clearError(errorBanner);
        sqlPreviewPanel.hidden = true;
    }

    function startNewTable() {
        editingTableName = null;
        editorPanel.hidden = false;
        editorTitle.textContent = "New Table";
        tableNameInput.value = "";
        deleteTableBtn.hidden = true;
        renderColumns([blankColumn()]);
        fkList.innerHTML = "";
        renderTableList();
        clearError(errorBanner);
        sqlPreviewPanel.hidden = true;
        tableNameInput.focus();
    }

    async function loadSchema() {
        clearError(errorBanner);
        clearInfo(infoBanner);
        sqlPreviewPanel.hidden = true;

        const workspaceId = workspaceSelect.value;
        if (!workspaceId) {
            showError(errorBanner, "Select a workspace first.");
            return;
        }

        setBusy(loadSchemaBtn, true, "Loading...", "Load Schema");

        try {
            const data = await fetchSchema(workspaceId);
            schemaTables = data.schema_data?.tables || [];
            renderTableList();
            showInfo(infoBanner, `Loaded ${schemaTables.length} table${schemaTables.length === 1 ? "" : "s"}.`);

            if (schemaTables.length) {
                const params = new URLSearchParams(window.location.search);
                const tableFromUrl = params.get("table");
                if (tableFromUrl && schemaTables.some((table) => table.name === tableFromUrl)) {
                    loadTableIntoEditor(tableFromUrl);
                }
            } else {
                editingTableName = null;
                startNewTable();
            }
        } catch (error) {
            showError(errorBanner, error.message);
        } finally {
            setBusy(loadSchemaBtn, false, "Loading...", "Load Schema");
        }
    }

    async function saveTable() {
        clearError(errorBanner);
        clearInfo(infoBanner);

        const workspaceId = workspaceSelect.value;
        if (!workspaceId) {
            showError(errorBanner, "Select a workspace first.");
            return;
        }

        let payload;
        try {
            payload = buildTablePayload();
        } catch (error) {
            showError(errorBanner, error.message);
            return;
        }

        setBusy(saveTableBtn, true, "Saving...", "Save Table");

        try {
            if (editingTableName) {
                await updateTable(workspaceId, editingTableName, payload);
                showInfo(infoBanner, `Table "${payload.name}" updated.`);
            } else {
                await createTable(workspaceId, payload);
                showInfo(infoBanner, `Table "${payload.name}" created.`);
            }

            editingTableName = payload.name;
            deleteTableBtn.hidden = false;
            await loadSchema();
            loadTableIntoEditor(payload.name);
        } catch (error) {
            showError(errorBanner, error.message);
        } finally {
            setBusy(saveTableBtn, false, "Saving...", "Save Table");
        }
    }

    async function removeTable() {
        clearError(errorBanner);
        clearInfo(infoBanner);

        const workspaceId = workspaceSelect.value;
        if (!workspaceId || !editingTableName) {
            return;
        }

        const confirmed = window.confirm(`Delete table "${editingTableName}"?`);
        if (!confirmed) {
            return;
        }

        setBusy(deleteTableBtn, true, "Deleting...", "Delete Table");

        try {
            await deleteTable(workspaceId, editingTableName);
            showInfo(infoBanner, `Table "${editingTableName}" deleted.`);
            editingTableName = null;
            editorPanel.hidden = true;
            sqlPreviewPanel.hidden = true;
            await loadSchema();
        } catch (error) {
            showError(errorBanner, error.message);
        } finally {
            setBusy(deleteTableBtn, false, "Deleting...", "Delete Table");
        }
    }

    async function previewSql() {
        clearError(errorBanner);

        const workspaceId = workspaceSelect.value;
        if (!workspaceId) {
            showError(errorBanner, "Select a workspace first.");
            return;
        }

        const tableName = tableNameInput.value.trim() || editingTableName;

        setBusy(previewSqlBtn, true, "Loading...", "Preview SQL");

        try {
            const data = await previewSchemaSql(workspaceId, tableName || null);
            sqlPreviewPanel.hidden = false;
            sqlPreviewOutput.textContent = (data.statements || []).join("\n\n") || "No SQL to preview.";
        } catch (error) {
            showError(errorBanner, error.message);
        } finally {
            setBusy(previewSqlBtn, false, "Loading...", "Preview SQL");
        }
    }

    if (loadSchemaBtn) {
        loadSchemaBtn.addEventListener("click", loadSchema);
    }

    if (refreshWorkspacesBtn) {
        refreshWorkspacesBtn.addEventListener("click", () => {
            initWorkspaceSelect(workspaceSelect, {
                onReady: () => {
                    updateErDiagramLink();
                    if (workspaceSelect.value) {
                        return loadSchema();
                    }
                    return undefined;
                },
            });
        });
    }

    if (newTableBtn) {
        newTableBtn.addEventListener("click", startNewTable);
    }

    if (addColumnBtn) {
        addColumnBtn.addEventListener("click", () => {
            const rows = readColumnsFromEditor();
            rows.push(blankColumn());
            renderColumns(rows);
        });
    }

    if (addFkBtn) {
        addFkBtn.addEventListener("click", () => {
            const tableName = tableNameInput.value.trim() || editingTableName;
            const otherTables = getOtherTableNames(tableName);
            if (!otherTables.length) {
                showError(errorBanner, "Add another table first before creating foreign keys.");
                return;
            }
            clearError(errorBanner);
            fkList.appendChild(
                createFkRow(
                    {
                        referenced_table: otherTables[0],
                        referenced_columns: [schemaTables.find((table) => table.name === otherTables[0])?.columns?.[0]?.name].filter(Boolean),
                        on_delete: "RESTRICT",
                    },
                    otherTables
                )
            );
        });
    }

    if (saveTableBtn) {
        saveTableBtn.addEventListener("click", saveTable);
    }

    if (deleteTableBtn) {
        deleteTableBtn.addEventListener("click", removeTable);
    }

    if (previewSqlBtn) {
        previewSqlBtn.addEventListener("click", previewSql);
    }

    workspaceSelect.addEventListener("change", updateErDiagramLink);

    initWorkspaceSelect(workspaceSelect, {
        onReady: async () => {
            updateErDiagramLink();
            if (workspaceSelect.value) {
                await loadSchema();
            }
        },
    });
});
