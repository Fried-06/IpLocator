const API_BASE_URL = "http://localhost:8000/api/v1";

function getAuthHeaders() {
    const token = localStorage.getItem("jwt_token");
    return token ? { "Authorization": Bearer  } : {};
}

async function apiCall(endpoint, options = {}) {
    options.headers = { ...options.headers, ...getAuthHeaders(), "Content-Type": "application/json" };
    const response = await fetch(${API_BASE_URL}, options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || data.message || "Erreur API");
    return data;
}

export { API_BASE_URL, getAuthHeaders, apiCall };
