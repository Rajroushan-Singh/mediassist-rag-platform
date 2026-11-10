import axios from "axios";

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
    headers: {
        "Content-Type": "application/json",
    },
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 429) {
            const retryAfter = error.response.headers?.["retry-after"];
            const detail =
                error.response.data?.detail ||
                `Rate limit exceeded: maximum 10 requests per minute allowed. Please wait ${
                    retryAfter ? retryAfter + " seconds" : "a moment"
                } before trying again.`;
            if (!error.response.data) {
                error.response.data = {};
            }
            error.response.data.detail = detail;
        }
        return Promise.reject(error);
    }
);

export default api;
