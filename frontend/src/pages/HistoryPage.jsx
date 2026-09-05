import React, { useEffect, useState } from "react";
import { clearHistory, getHistory } from "../api/client.js";

export default function HistoryPage() {
  const [items, setItems] = useState(null);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState(null);

  function load() {
    getHistory()
      .then(setItems)
      .catch(() => setError("Could not reach the API. Is the backend running on port 8000?"));
  }

  useEffect(load, []);

  async function handleClear() {
    if (!window.confirm("Clear all prediction history? This cannot be undone.")) return;
    await clearHistory();
    load();
  }

  if (error) return <div className="error-banner">{error}</div>;
  if (!items) return <p>Loading history…</p>;

  return (
    <div>
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <h1>Prediction history</h1>
          <p>Every posting submitted for review, most recent first, stored in the database.</p>
        </div>
        {items.length > 0 && (
          <button className="btn-ghost btn" onClick={handleClear}>Clear history</button>
        )}
      </div>

      {items.length === 0 && (
        <div className="empty-state">No predictions yet. Submit a posting on the Review page to get started.</div>
      )}

      {items.length > 0 && (
        <div className="card" style={{ padding: 0 }}>
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ padding: "14px 16px" }}>Time</th>
                <th>Title</th>
                <th>Model</th>
                <th>Verdict</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <React.Fragment key={item.id}>
                  <tr
                    style={{ cursor: "pointer" }}
                    onClick={() => setExpanded(expanded === item.id ? null : item.id)}
                  >
                    <td style={{ padding: "10px 16px", whiteSpace: "nowrap" }}>
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                    <td>{item.title || "(untitled)"}</td>
                    <td>{item.model_used.replace(/_/g, " ")}</td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          background: item.prediction === "Fraudulent" ? "var(--danger-line)" : "var(--clear)",
                        }}
                      >
                        {item.prediction}
                      </span>
                    </td>
                    <td style={{ fontFamily: "var(--font-mono)" }}>{(item.confidence * 100).toFixed(1)}%</td>
                  </tr>
                  {expanded === item.id && (
                    <tr>
                      <td colSpan={5} style={{ background: "var(--paper)", padding: "14px 16px" }}>
                        <strong style={{ fontSize: "0.82rem" }}>Top factors:</strong>
                        <ul style={{ margin: "8px 0 0 0", paddingLeft: 18, fontSize: "0.85rem" }}>
                          {item.top_factors.map((f, i) => (
                            <li key={i}>
                              {f.feature}: {f.impact >= 0 ? "+" : ""}{f.impact.toFixed(2)}
                            </li>
                          ))}
                        </ul>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
