const BASE = "/api";

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch (e) {
      // ignore
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function predictJob(payload) {
  const res = await fetch(`${BASE}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handle(res);
}

export async function listModels() {
  const res = await fetch(`${BASE}/models`);
  return handle(res);
}

export async function compareModels() {
  const res = await fetch(`${BASE}/models/compare`);
  return handle(res);
}

export async function getEda() {
  const res = await fetch(`${BASE}/eda`);
  return handle(res);
}

export async function getHistory(limit = 50) {
  const res = await fetch(`${BASE}/history?limit=${limit}`);
  return handle(res);
}

export async function getHistoryItem(id) {
  const res = await fetch(`${BASE}/history/${id}`);
  return handle(res);
}

export async function clearHistory() {
  const res = await fetch(`${BASE}/history`, { method: "DELETE" });
  return handle(res);
}
