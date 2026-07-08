const isLocalDevHost =
    window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";

const API_BASE_URL = (
    window.QUERYLENS_API_URL || (isLocalDevHost ? "http://localhost:5000" : window.location.origin)
).replace(/\/$/, "");
