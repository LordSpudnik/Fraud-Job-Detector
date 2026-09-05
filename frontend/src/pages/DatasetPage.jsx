import React, { useEffect, useState } from "react";
import { getEda } from "../api/client.js";

export default function DatasetPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getEda()
      .then(setData)
      .catch(() => setError("Could not reach the API. Is the backend running on port 8000?"));
  }, []);

  if (error) return <div className="error-banner">{error}</div>;
  if (!data) return <p>Loading dataset statistics…</p>;

  const totalRows = data.fraud_distribution.genuine + data.fraud_distribution.fraudulent;
  const fraudPct = ((data.fraud_distribution.fraudulent / totalRows) * 100).toFixed(1);

  const topMissing = Object.entries(data.missing_values_pct)
    .filter(([, v]) => v > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8);

  const topIndustries = Object.entries(data.top_industries).slice(0, 8);
  const topWords = Object.entries(data.top_fraud_words).slice(0, 15);
  const maxWordCount = Math.max(...topWords.map(([, c]) => c), 1);

  return (
    <div>
      <div className="page-header">
        <h1>Dataset & exploratory analysis</h1>
        <p>Based on the EMSCAD-derived Fake Job Postings dataset, {totalRows.toLocaleString()} postings after cleaning and de-duplication.</p>
      </div>

      <div className="grid-3" style={{ marginBottom: 24 }}>
        <div className="stat-block">
          <span className="stat-value">{totalRows.toLocaleString()}</span>
          <span className="stat-label">Total postings</span>
        </div>
        <div className="stat-block">
          <span className="stat-value">{data.fraud_distribution.fraudulent.toLocaleString()}</span>
          <span className="stat-label">Fraudulent ({fraudPct}%)</span>
        </div>
        <div className="stat-block">
          <span className="stat-value">{data.fraud_distribution.genuine.toLocaleString()}</span>
          <span className="stat-label">Genuine</span>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: 24 }}>
        <div className="card">
          <h3>Missing values by field</h3>
          <p style={{ fontSize: "0.82rem" }}>Fields left blank in the raw dataset, before cleaning filled them in.</p>
          {topMissing.map(([field, pct]) => (
            <div className="factor-row" key={field}>
              <span style={{ width: 160, flexShrink: 0 }}>{field}</span>
              <div className="factor-bar-track">
                <div className="factor-bar-fill neg" style={{ width: `${pct}%`, background: "var(--flag)" }} />
              </div>
              <span style={{ width: 50, textAlign: "right", fontFamily: "var(--font-mono)", fontSize: "0.78rem" }}>
                {pct}%
              </span>
            </div>
          ))}
        </div>

        <div className="card">
          <h3>Top industries by volume</h3>
          <p style={{ fontSize: "0.82rem" }}>Which industries post the most jobs in this dataset.</p>
          {topIndustries.map(([industry, count]) => (
            <div className="factor-row" key={industry}>
              <span style={{ width: 190, flexShrink: 0 }}>{industry}</span>
              <div className="factor-bar-track">
                <div
                  className="factor-bar-fill"
                  style={{
                    width: `${(count / topIndustries[0][1]) * 100}%`,
                    background: "var(--ink)",
                  }}
                />
              </div>
              <span style={{ width: 50, textAlign: "right", fontFamily: "var(--font-mono)", fontSize: "0.78rem" }}>
                {count}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <h3>Fraud rate by whether a salary was listed</h3>
        <div className="grid-2" style={{ marginTop: 12 }}>
          {Object.entries(data.fraud_rate_by_salary_presence_pct).map(([key, pct]) => (
            <div className="stat-block" key={key}>
              <span className="stat-value">{pct.toFixed(1)}%</span>
              <span className="stat-label">{key === "0" ? "No salary listed" : "Salary listed"}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h3>Most frequent words in fraudulent postings</h3>
        <p style={{ fontSize: "0.82rem" }}>After lowercasing, stop-word removal, and lemmatization.</p>
        {topWords.map(([word, count]) => (
          <div className="factor-row" key={word}>
            <span style={{ width: 140, flexShrink: 0 }}>{word}</span>
            <div className="factor-bar-track">
              <div className="factor-bar-fill" style={{ width: `${(count / maxWordCount) * 100}%`, background: "var(--flag)" }} />
            </div>
            <span style={{ width: 50, textAlign: "right", fontFamily: "var(--font-mono)", fontSize: "0.78rem" }}>
              {count}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
