// ============================================================
// LOAN MANAGEMENT
// Correction/cancellation controls for linked loan movements.
// ============================================================
import React, { useCallback, useEffect, useState } from "react";
import { RefreshCw, Pencil, Ban, Landmark, HandCoins, AlertTriangle } from "lucide-react";
import { apiFetch, getCurrentUserId } from "./api";

const API_BASE_URL = "https://wealthmanager.duckdns.org";
const USER_ID = getCurrentUserId();
const money = (value) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 }).format(Number(value || 0));
const inputStyle = { width: "100%", boxSizing: "border-box", padding: "10px", borderRadius: 9, border: "1px solid rgba(255,255,255,.16)", background: "#171729", color: "#fff" };
const buttonStyle = { display: "inline-flex", alignItems: "center", gap: 7, padding: "8px 11px", borderRadius: 9, border: "1px solid rgba(255,255,255,.15)", background: "rgba(139,92,246,.16)", color: "#fff", cursor: "pointer" };

export default function LoanManagement() {
  const [loans, setLoans] = useState([]);
  const [receivables, setReceivables] = useState([]);
  const [movements, setMovements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const request = async (path, options = {}) => {
    const response = await apiFetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || `Request failed (${response.status})`);
    return payload;
  };

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const [loanData, receivableData, movementData] = await Promise.all([
        request(`/api/loans?user_id=${USER_ID}`),
        request(`/api/loan-receivables?user_id=${USER_ID}`),
        request(`/api/financial-summary/loan-movements?user_id=${USER_ID}`),
      ]);
      setLoans(Array.isArray(loanData.loans) ? loanData.loans : []);
      setReceivables(Array.isArray(receivableData.loan_receivables) ? receivableData.loan_receivables : []);
      setMovements(Array.isArray(movementData) ? movementData : []);
    } catch (e) { setError(e.message || "Loan data could not be loaded."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const correctMovement = async (item) => {
    const principal = window.prompt("Correct principal amount (₹):", String(item.principal_amount));
    if (principal === null) return;
    const interest = window.prompt("Correct interest amount (₹):", String(item.interest_amount));
    if (interest === null) return;
    const fees = window.prompt("Correct fees amount (₹):", String(item.fee_amount));
    if (fees === null) return;
    const date = window.prompt("Transaction date (YYYY-MM-DD):", item.transaction_date || new Date().toISOString().slice(0, 10));
    if (date === null) return;
    if (![principal, interest, fees].every((v) => v.trim() !== "" && Number.isFinite(Number(v)) && Number(v) >= 0) || Number(principal) <= 0 || !/^\d{4}-\d{2}-\d{2}$/.test(date)) {
      setError("Enter a positive principal, non-negative interest/fees, and a valid YYYY-MM-DD date."); return;
    }
    setBusyId(item.id); setError(""); setMessage("");
    try {
      await request(`/api/loan-movements/${item.id}`, { method: "PUT", body: JSON.stringify({
        user_id: USER_ID, account_id: item.account_id, principal_amount: Number(principal),
        interest_amount: Number(interest), fee_amount: Number(fees), transaction_date: date,
        reference: item.reference || null, notes: item.description || null,
      }) });
      setMessage("Loan movement corrected and linked balances updated."); await load();
    } catch (e) { setError(e.message || "Correction failed."); }
    finally { setBusyId(null); }
  };

  const cancelMovement = async (item) => {
    const ok = window.confirm(`Cancel this ${item.movement_type} for ${money(item.amount)}? The linked account balance and principal will be reversed.`);
    if (!ok) return;
    setBusyId(item.id); setError(""); setMessage("");
    try {
      await request(`/api/loan-movements/${item.id}?user_id=${USER_ID}`, { method: "DELETE" });
      setMessage("Loan movement cancelled and linked balances reversed."); await load();
    } catch (e) { setError(e.message || "Cancellation failed."); }
    finally { setBusyId(null); }
  };

  const card = { background: "rgba(255,255,255,.04)", border: "1px solid rgba(255,255,255,.09)", borderRadius: 16, padding: 18, minWidth: 0 };
  return <div className="loan-management-page" style={{ display: "grid", gap: 18 }}>
    <section className="loan-management-header">
      <div className="loan-management-heading">
        <p className="loan-management-eyebrow">MONEY · LOANS</p>
        <h2>Loan Management</h2>
        <p className="loan-management-description">Review borrowing, lending, repayments and recoveries. Corrections update linked balances together.</p>
      </div>
      <button className="loan-management-refresh" onClick={load} disabled={loading} type="button">
        <RefreshCw size={16} className={loading ? "loan-refresh-spinning" : ""} />
        <span>{loading ? "Refreshing…" : "Refresh"}</span>
      </button>
    </section>
    {error && <div role="alert" style={{ ...card, borderColor: "rgba(248,113,113,.45)", color: "#fecaca" }}><AlertTriangle size={17} style={{ verticalAlign: "middle", marginRight: 8 }} />{error}</div>}
    {message && <div role="status" style={{ ...card, borderColor: "rgba(74,222,128,.4)", color: "#bbf7d0" }}>{message}</div>}
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(240px,1fr))", gap: 14 }}>
      <div style={card}><div style={{ display: "flex", gap: 9, alignItems: "center", color: "#c4b5fd" }}><Landmark size={19} /> Borrowed loans</div><h3>{loans.length} records</h3><div style={{ color: "#a1a1b5", fontSize: 13 }}>Outstanding principal</div><strong>{money(loans.reduce((s, x) => s + Number(x.outstanding_principal || 0), 0))}</strong></div>
      <div style={card}><div style={{ display: "flex", gap: 9, alignItems: "center", color: "#86efac" }}><HandCoins size={19} /> Loans given</div><h3>{receivables.length} records</h3><div style={{ color: "#a1a1b5", fontSize: 13 }}>Principal still receivable</div><strong>{money(receivables.reduce((s, x) => s + Number(x.outstanding_principal || 0), 0))}</strong></div>
    </div>
    <section style={card}><h3 style={{ marginTop: 0 }}>Recent repayments and recoveries</h3><p style={{ color: "#a1a1b5", fontSize: 13 }}>Use Correct or Cancel for repayment/recovery movements. Disbursement cancellation is managed separately and is not offered here.</p>
      {loading ? <p>Loading loan records…</p> : movements.filter(x => ["repayment", "recovery"].includes(x.movement_type)).length === 0 ? <p style={{ color: "#a1a1b5" }}>No linked repayments or recoveries were found.</p> : <div style={{ overflowX: "auto" }}><table style={{ width: "100%", borderCollapse: "collapse", minWidth: 760 }}><thead><tr>{["Date", "Type", "Description", "Principal", "Interest", "Fees", "Total", "Actions"].map(t => <th key={t} style={{ textAlign: "left", padding: 10, borderBottom: "1px solid rgba(255,255,255,.12)", color: "#c4b5fd", fontSize: 12 }}>{t}</th>)}</tr></thead><tbody>{movements.filter(x => ["repayment", "recovery"].includes(x.movement_type)).map(item => <tr key={item.id}><td style={{ padding: 10, borderBottom: "1px solid rgba(255,255,255,.06)" }}>{item.transaction_date || "—"}</td><td style={{ padding: 10 }}>{item.movement_type}</td><td style={{ padding: 10, maxWidth: 220 }}>{item.description || `Transaction #${item.transaction_id}`}</td><td style={{ padding: 10 }}>{money(item.principal_amount)}</td><td style={{ padding: 10 }}>{money(item.interest_amount)}</td><td style={{ padding: 10 }}>{money(item.fee_amount)}</td><td style={{ padding: 10 }}>{money(item.amount)}</td><td style={{ padding: 10, whiteSpace: "nowrap" }}><button style={buttonStyle} disabled={busyId === item.id} onClick={() => correctMovement(item)}><Pencil size={14} /> Correct</button> <button style={{ ...buttonStyle, background: "rgba(248,113,113,.12)" }} disabled={busyId === item.id} onClick={() => cancelMovement(item)}><Ban size={14} /> Cancel</button></td></tr>)}</tbody></table></div>}
    </section>
    <section style={card}><h3 style={{ marginTop: 0 }}>Borrowed loans</h3>{loans.length ? loans.map(x => <div key={x.id} style={{ display: "flex", justifyContent: "space-between", gap: 12, padding: "12px 0", borderBottom: "1px solid rgba(255,255,255,.07)" }}><div><strong>{x.name}</strong><div style={{ color: "#a1a1b5", fontSize: 13 }}>{x.lender_name} · {x.status}</div></div><div style={{ textAlign: "right" }}><strong>{money(x.outstanding_principal)}</strong><div style={{ color: "#a1a1b5", fontSize: 12 }}>Outstanding</div></div></div>) : <p style={{ color: "#a1a1b5" }}>No borrowed loans found.</p>}</section>
    <section style={card}><h3 style={{ marginTop: 0 }}>Loans given</h3>{receivables.length ? receivables.map(x => <div key={x.id} style={{ display: "flex", justifyContent: "space-between", gap: 12, padding: "12px 0", borderBottom: "1px solid rgba(255,255,255,.07)" }}><div><strong>{x.name}</strong><div style={{ color: "#a1a1b5", fontSize: 13 }}>{x.borrower_name} · {x.status}</div></div><div style={{ textAlign: "right" }}><strong>{money(x.outstanding_principal)}</strong><div style={{ color: "#a1a1b5", fontSize: 12 }}>Outstanding</div></div></div>) : <p style={{ color: "#a1a1b5" }}>No loans given found.</p>}</section>
    <div style={{ color: "#a1a1b5", fontSize: 12, lineHeight: 1.6 }}>Safety: account switching is not supported during correction. Disbursement cancellation remains blocked unless a dedicated backend cancellation endpoint is deployed. Test with sample records before using real financial data.</div>
  </div>;
}
