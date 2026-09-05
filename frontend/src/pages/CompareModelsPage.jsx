import React, { useEffect, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { compareModels } from "../api/client.js";

const METRIC_KEYS = ["accuracy", "precision", "recall", "f1", "roc_auc"];
const METRIC_LABELS = {
  accuracy: "Accuracy",
  precision: "Precision",
  recall: "Recall",
  f1: "F1 Score",
  roc_auc: "ROC-AUC",
};

const COLORS = ["#16202a", "#c98a2c", "#2f6f6b", "#a5471f", "#5b7fae", "#8a6bb1"];

export default function CompareModelsPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    compareModels()
      .then((d) => {
        setData(d);
        setSelected(d.best_model);
      })
      .catch(() => setError("Could not reach the API. Is the backend running on port 8000?"));
  }, []);

  if (error) return <div className="error-banner">{error}</div>;
  if (!data) return <p>Loading model comparison…</p>;

  const modelNames = Object.keys(data.models);

  // Build ROC chart data: one series per model, interpolated onto a shared fpr grid isn't
  // necessary for a class project — recharts can plot each series against its own fpr as x.
  const rocSeries = modelNames.map((name) => ({
    name,
    points: data.models[name].roc_curve.fpr.map((fpr, i) => ({
      fpr,
      [name]: data.models[name].roc_curve.tpr[i],
    })),
  }));

  const cm = data.models[selected].confusion_matrix;

  return (
    <div>
      <div className="page-header">
        <h1>Model comparison</h1>
        <p>
          All six candidate models were trained and evaluated on the same held-out test split.{" "}
          <strong>{data.best_model.replace(/_/g, " ")}</strong> was selected as the production model
          based on F1 score on the fraud class.
        </p>
      </div>

      <div className="card" style={{ marginBottom: 24, overflowX: "auto" }}>
        <h3>Metrics</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Model</th>
              {METRIC_KEYS.map((k) => (
                <th key={k}>{METRIC_LABELS[k]}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {modelNames.map((name) => (
              <tr key={name} className={name === data.best_model ? "best-row" : ""}>
                <td style={{ fontWeight: 600 }}>
                  {name.replace(/_/g, " ")}
                  {name === data.best_model && <span className="badge" style={{ marginLeft: 8 }}>selected</span>}
                </td>
                {METRIC_KEYS.map((k) => (
                  <td key={k} style={{ fontFamily: "var(--font-mono)" }}>
                    {data.models[name][k].toFixed(3)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid-2" style={{ marginBottom: 24 }}>
        <div className="card">
          <h3>ROC curves</h3>
          <p style={{ fontSize: "0.82rem" }}>True positive rate vs. false positive rate. Closer to the top-left is better.</p>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid stroke="#d7dde3" />
              <XAxis dataKey="fpr" type="number" domain={[0, 1]} tick={{ fontSize: 11 }} />
              <YAxis type="number" domain={[0, 1]} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: "0.78rem" }} />
              {modelNames.map((name, i) => (
                <Line
                  key={name}
                  data={rocSeries.find((s) => s.name === name).points}
                  dataKey={name}
                  stroke={COLORS[i % COLORS.length]}
                  dot={false}
                  strokeWidth={name === data.best_model ? 2.5 : 1.5}
                  isAnimationActive={false}
                  type="monotone"
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3>Confusion matrix</h3>
          <div className="field" style={{ marginBottom: 12 }}>
            <select value={selected} onChange={(e) => setSelected(e.target.value)}>
              {modelNames.map((name) => (
                <option key={name} value={name}>{name.replace(/_/g, " ")}</option>
              ))}
            </select>
          </div>
          <div className="confusion-grid">
            <div className="confusion-cell header" />
            <div className="confusion-cell header">Predicted Genuine</div>
            <div className="confusion-cell header">Predicted Fraud</div>

            <div className="confusion-cell header" style={{ writingMode: "vertical-rl" }}>Actual Genuine</div>
            <div className="confusion-cell" style={{ background: "var(--clear-soft)" }}>{cm[0][0]}</div>
            <div className="confusion-cell" style={{ background: "var(--flag-soft)" }}>{cm[0][1]}</div>

            <div className="confusion-cell header" style={{ writingMode: "vertical-rl" }}>Actual Fraud</div>
            <div className="confusion-cell" style={{ background: "var(--flag-soft)" }}>{cm[1][0]}</div>
            <div className="confusion-cell" style={{ background: "var(--clear-soft)" }}>{cm[1][1]}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
