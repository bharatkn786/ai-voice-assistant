const API_BASE = "http://localhost:8001/api";

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