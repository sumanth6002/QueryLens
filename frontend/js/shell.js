/**
 * Shared app shell: sidebar, navigation, Lucide icons.
 */

const QL_NAV = [
    { id: "dashboard", label: "Dashboard", href: "index.html", icon: "layout-dashboard", root: true },
    { id: "schema-builder", label: "Schema Builder", href: "pages/schema-builder.html", icon: "table-2" },
    { id: "er-diagram", label: "ER Diagram", href: "pages/er-diagram.html", icon: "git-branch" },
    { id: "explain", label: "EXPLAIN", href: "pages/explain.html", icon: "workflow" },
    { id: "normalization", label: "Normalization", href: "pages/normalization.html", icon: "layers" },
    { id: "index-advisor", label: "Index Advisor", href: "pages/index-advisor.html", icon: "zap" },
    { id: "reports", label: "Reports", href: "pages/reports.html", icon: "file-text" },
    { id: "settings", label: "Settings", href: "pages/settings.html", icon: "settings" },
];

function qlBasePath() {
    return window.location.pathname.includes("/pages/") ? ".." : ".";
}

function qlHref(path, isRoot) {
    const base = qlBasePath();
    if (isRoot) {
        return base === ".." ? "../index.html" : "index.html";
    }
    return base === ".." ? path.replace("pages/", "") : path;
}

function qlResolvePageId() {
    const fromBody = document.body.dataset.page;
    if (fromBody) return fromBody;
    const file = window.location.pathname.split("/").pop() || "index.html";
    const map = {
        "index.html": "dashboard",
        "schema-builder.html": "schema-builder",
        "er-diagram.html": "er-diagram",
        "explain.html": "explain",
        "normalization.html": "normalization",
        "index-advisor.html": "index-advisor",
        "reports.html": "reports",
        "settings.html": "settings",
    };
    return map[file] || "dashboard";
}

function qlInitShell() {
    const pageId = qlResolvePageId();

    document.querySelectorAll(".ql-nav a[data-nav], .ql-sidebar-footer a[data-nav]").forEach((link) => {
        const item = QL_NAV.find((nav) => nav.id === link.dataset.nav);
        if (item) {
            link.href = qlHref(item.href, item.root);
        }
        if (link.dataset.nav === pageId) {
            link.classList.add("is-active");
        }
    });

    const brandLink = document.querySelector(".ql-sidebar-brand a");
    if (brandLink) {
        brandLink.href = qlHref("index.html", true);
    }

    if (typeof lucide !== "undefined") {
        lucide.createIcons();
    }
}

document.addEventListener("DOMContentLoaded", qlInitShell);
