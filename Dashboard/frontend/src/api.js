// Determine API base URL from environment so it can be configured per environment.
//
// Priority:
// 1. REACT_APP_DASHBOARD_API_BASE (full URL, e.g. https://your-domain/api)
// 2. BASE_URL from root .env exposed as REACT_APP_BASE_URL (we append /api)
// 3. Fallback to local development default http://localhost:8001/api

const envApiBase = process.env.REACT_APP_DASHBOARD_API_BASE;
const envRootBase = process.env.REACT_APP_BASE_URL; // should mirror BASE_URL from root .env

export let API_BASE = "http://localhost:8001/api";

if (envApiBase && envApiBase.trim()) {
  API_BASE = envApiBase.trim().replace(/\/$/, "");
} else if (envRootBase && envRootBase.trim()) {
  const normalized = envRootBase.trim().replace(/\/$/, "");
  API_BASE = `${normalized}/api`;
}

export async function fetchCalls() {
  const res = await fetch(`${API_BASE}/calls`);
  return res.json();
}

export async function fetchSummary() {
  const res = await fetch(`${API_BASE}/calls/status-summary`);
  return res.json();
}

export async function fetchCallById(call_sid){
    const res = await fetch(`${API_BASE}/calls/${call_sid}`);
    return res.json();
}

export async function fetchActiveCalls() {
  const res = await fetch(`${API_BASE}/calls/active`);
  return res.json();
}

export async function fetchRecentCalls(limit = 10) {
  const res = await fetch(`${API_BASE}/calls/recent?limit=${limit}`);
  return res.json();
}