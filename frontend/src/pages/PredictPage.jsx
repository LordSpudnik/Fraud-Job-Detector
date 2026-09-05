import React, { useEffect, useState } from "react";
import { listModels, predictJob } from "../api/client.js";

const EMPLOYMENT_TYPES = ["Full-time", "Part-time", "Contract", "Temporary", "Other"];
const EXPERIENCE_LEVELS = ["Not Applicable", "Internship", "Entry level", "Associate", "Mid-Senior level", "Director", "Executive"];
const EDUCATION_LEVELS = ["Unspecified", "High School or equivalent", "Some College Coursework Completed", "Vocational", "Bachelor's Degree", "Master's Degree", "Doctorate"];

const SAMPLE_SUSPICIOUS = {
  title: "Work From Home Data Entry — Immediate Start, $5000/week",
  company_profile: "",
  description:
    "No experience needed. Urgent hiring, limited spots available. Just send your bank details and a copy of your ID to get started immediately. Full training kit provided after a small registration fee.",
  requirements: "Must have a bank account and be willing to pay a refundable deposit for equipment.",
  benefits: "Guaranteed weekly income, work from anywhere.",
  employment_type: "Full-time",
  required_experience: "Not Applicable",
  required_education: "Unspecified",
  industry: "Unknown",
  function: "Unknown",
  telecommuting: 1,
  has_company_logo: 0,
  has_questions: 0,
};

const EMPTY_FORM = {
  title: "",
  company_profile: "",
  description: "",
  requirements: "",
  benefits: "",
  employment_type: "Full-time",
  required_experience: "Not Applicable",
  required_education: "Unspecified",
  industry: "",
  function: "",
  telecommuting: 0,
  has_company_logo: 0,
  has_questions: 0,
};

export default function PredictPage() {
  const [form, setForm] = useState(EMPTY_FORM);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    listModels()
      .then((data) => {
        setModels(data.models);
        setSelectedModel(data.best_model);
      })
      .catch(() => setError("Could not reach the API. Is the backend running on port 8000?"));
  }, []);

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function loadSample() {
    setForm(SAMPLE_SUSPICIOUS);
    setResult(null);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const payload = { ...form, model_name: selectedModel || undefined };
      const data = await predictJob(payload);
      setResult(data);
    } catch (err) {
      setError(err.message || "Prediction failed.");
    } finally {
      setLoading(false);
    }
  }

  const maxAbsImpact = result
    ? Math.max(...result.top_factors.map((f) => Math.abs(f.impact)), 0.0001)
    : 1;

  return (
    <div>
      <div className="page-header">
        <h1>Review a job posting</h1>
        <p>Paste in a job advertisement's details and get a fraud verdict with a confidence score and the specific factors behind it.</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="grid-2">
        <form className="card" onSubmit={handleSubmit}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
            <h3>Posting details</h3>
            <button type="button" className="btn-ghost btn" onClick={loadSample}>
              Load suspicious sample
            </button>
          </div>

          <div className="field">
            <label>Job title</label>
            <input
              type="text"
              required
              value={form.title}
              onChange={(e) => update("title", e.target.value)}
              placeholder="e.g. Marketing Intern"
            />
          </div>

          <div className="field">
            <label>Company profile</label>
            <textarea
              value={form.company_profile}
              onChange={(e) => update("company_profile", e.target.value)}
              placeholder="How the company describes itself"
            />
          </div>

          <div className="field">
            <label>Job description</label>
            <textarea
              required
              value={form.description}
              onChange={(e) => update("description", e.target.value)}
              placeholder="What the role involves"
            />
          </div>

          <div className="field">
            <label>Requirements</label>
            <textarea
              value={form.requirements}
              onChange={(e) => update("requirements", e.target.value)}
              placeholder="Skills, experience, qualifications asked for"
            />
          </div>

          <div className="field">
            <label>Benefits</label>
            <textarea
              value={form.benefits}
              onChange={(e) => update("benefits", e.target.value)}
              placeholder="What's offered in return"
            />
          </div>

          <div className="grid-2">
            <div className="field">
              <label>Employment type</label>
              <select value={form.employment_type} onChange={(e) => update("employment_type", e.target.value)}>
                {EMPLOYMENT_TYPES.map((v) => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Required experience</label>
              <select value={form.required_experience} onChange={(e) => update("required_experience", e.target.value)}>
                {EXPERIENCE_LEVELS.map((v) => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid-2">
            <div className="field">
              <label>Required education</label>
              <select value={form.required_education} onChange={(e) => update("required_education", e.target.value)}>
                {EDUCATION_LEVELS.map((v) => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Industry</label>
              <input
                type="text"
                value={form.industry}
                onChange={(e) => update("industry", e.target.value)}
                placeholder="e.g. Computer Software"
              />
            </div>
          </div>

          <div className="field">
            <label>Function</label>
            <input
              type="text"
              value={form.function}
              onChange={(e) => update("function", e.target.value)}
              placeholder="e.g. Engineering, Marketing, Sales"
            />
          </div>

          <div className="field" style={{ display: "flex", gap: 20 }}>
            <label className="checkbox-row" style={{ marginBottom: 0 }}>
              <input
                type="checkbox"
                checked={!!form.telecommuting}
                onChange={(e) => update("telecommuting", e.target.checked ? 1 : 0)}
              />
              Telecommuting
            </label>
            <label className="checkbox-row" style={{ marginBottom: 0 }}>
              <input
                type="checkbox"
                checked={!!form.has_company_logo}
                onChange={(e) => update("has_company_logo", e.target.checked ? 1 : 0)}
              />
              Has company logo
            </label>
            <label className="checkbox-row" style={{ marginBottom: 0 }}>
              <input
                type="checkbox"
                checked={!!form.has_questions}
                onChange={(e) => update("has_questions", e.target.checked ? 1 : 0)}
              />
              Has screening questions
            </label>
          </div>

          <div className="field">
            <label>Model</label>
            <select value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)}>
              {models.map((m) => (
                <option key={m} value={m}>{m.replace(/_/g, " ")}</option>
              ))}
            </select>
          </div>

          <button className="btn" type="submit" disabled={loading}>
            {loading && <span className="spinner" />}
            {loading ? "Analyzing…" : "Check this posting"}
          </button>
        </form>

        <div>
          {!result && !loading && (
            <div className="empty-state">
              Submit a posting on the left to see the verdict, confidence score, and the factors driving the prediction.
            </div>
          )}

          {result && (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div className={`verdict ${result.prediction === "Fraudulent" ? "fraud" : "genuine"}`}>
                <div>
                  <div className="verdict-label">{result.prediction}</div>
                  <div style={{ fontSize: "0.82rem", color: "var(--ink-soft)" }}>
                    Model: {result.model_used.replace(/_/g, " ")}
                  </div>
                </div>
                <div style={{ marginLeft: "auto", textAlign: "right" }}>
                  <div className="confidence-figure">{(result.confidence * 100).toFixed(1)}%</div>
                  <div style={{ fontSize: "0.78rem", color: "var(--ink-soft)" }}>confidence</div>
                </div>
              </div>

              <div className="card">
                <h3>What drove this prediction</h3>
                <p style={{ fontSize: "0.85rem", marginBottom: 14 }}>
                  SHAP-based factors. Amber bars push toward "Fraudulent," teal bars push toward "Genuine."
                </p>
                {result.top_factors.length === 0 && (
                  <p style={{ fontSize: "0.85rem" }}>No dominant factors — this model works differently from the tree-based explainer.</p>
                )}
                {result.top_factors.map((f, i) => (
                  <div className="factor-row" key={i}>
                    <span style={{ width: 190, flexShrink: 0, color: "var(--ink)" }}>{f.feature}</span>
                    <div className="factor-bar-track">
                      <div
                        className={`factor-bar-fill ${f.impact >= 0 ? "pos" : "neg"}`}
                        style={{ width: `${(Math.abs(f.impact) / maxAbsImpact) * 100}%` }}
                      />
                    </div>
                    <span style={{ width: 56, textAlign: "right", fontFamily: "var(--font-mono)", fontSize: "0.78rem" }}>
                      {f.impact >= 0 ? "+" : ""}{f.impact.toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>

              <p style={{ fontSize: "0.8rem" }}>Saved to prediction history as record #{result.record_id}.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
