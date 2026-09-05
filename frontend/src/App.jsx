import React from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import PredictPage from "./pages/PredictPage.jsx";
import CompareModelsPage from "./pages/CompareModelsPage.jsx";
import HistoryPage from "./pages/HistoryPage.jsx";
import DatasetPage from "./pages/DatasetPage.jsx";

const NAV_ITEMS = [
  { to: "/", label: "Submit a Posting", end: true },
  { to: "/compare", label: "Model Comparison" },
  { to: "/history", label: "Prediction History" },
  { to: "/dataset", label: "Dataset & EDA" },
];

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <div className="brand">Sentry</div>
          <span className="brand-sub">Job posting fraud review</span>
        </div>
        <ul className="nav-list">
          {NAV_ITEMS.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.end}
                className={({ isActive }) => "nav-item" + (isActive ? " active" : "")}
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<PredictPage />} />
          <Route path="/compare" element={<CompareModelsPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/dataset" element={<DatasetPage />} />
        </Routes>
      </main>
    </div>
  );
}
