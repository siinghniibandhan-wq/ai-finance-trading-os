import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, AlertCircle, CheckCircle2, RefreshCw, ShieldCheck, Users, UserCheck, UserX } from "lucide-react";
import { API_BASE_URL, apiFetch } from "./api";
import "./AdminPanel.css";

async function readResponse(response) {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(typeof body.detail === "string" ? body.detail : `Request failed (${response.status}).`);
  }
  return body;
}

export default function AdminPanel() {
  const [users, setUsers] = useState([]);
  const [overview, setOverview] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [savingUserId, setSavingUserId] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [filter, setFilter] = useState("all");

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [usersResponse, overviewResponse, auditResponse] = await Promise.all([
        apiFetch(`${API_BASE_URL}/api/auth/admin/users?limit=500&offset=0`),
        apiFetch(`${API_BASE_URL}/api/auth/admin/overview`),
        apiFetch(`${API_BASE_URL}/api/auth/admin/audit-logs?limit=100&offset=0`),
      ]);
      const [usersData, overviewData, auditData] = await Promise.all([
        readResponse(usersResponse), readResponse(overviewResponse), readResponse(auditResponse),
      ]);
      setUsers(Array.isArray(usersData.items) ? usersData.items : []);
      setOverview(overviewData);
      setAuditLogs(Array.isArray(auditData.items) ? auditData.items : []);
    } catch (err) {
      setError(err?.message || "Unable to load customer accounts.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadUsers(); }, [loadUsers]);

  const counts = useMemo(() => ({
    total: overview?.users_total ?? users.length,
    active: overview?.users_active ?? users.filter((user) => user.is_active).length,
    inactive: overview?.users_inactive ?? users.filter((user) => !user.is_active).length,
    admins: users.filter((user) => user.is_admin).length,
  }), [users, overview]);

  const visibleUsers = useMemo(() => users.filter((user) => {
    if (filter === "active") return user.is_active;
    if (filter === "inactive") return !user.is_active;
    if (filter === "admins") return user.is_admin;
    return true;
  }), [users, filter]);

  const updateStatus = async (user) => {
    const nextStatus = !user.is_active;
    setSavingUserId(user.id);
    setError("");
    setNotice("");
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/auth/admin/users/${encodeURIComponent(user.id)}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ is_active: nextStatus }),
      });
      await readResponse(response);
      setUsers((current) => current.map((item) => item.id === user.id ? { ...item, is_active: nextStatus } : item));
      setNotice(`${user.email || user.name}: account ${nextStatus ? "activated" : "deactivated"}.`);
    } catch (err) {
      setError(err?.message || "Unable to update this account.");
    } finally {
      setSavingUserId(null);
    }
  };

  const deleteUser = async (user) => {
    const label = user.email || user.name || `user #${user.id}`;
    if (!window.confirm(`Permanently delete ${label} (ID ${user.id})? This cannot be undone.`)) return;
    setSavingUserId(user.id);
    setError("");
    setNotice("");
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/auth/admin/users/${encodeURIComponent(user.id)}`, {
        method: "DELETE",
        headers: { Accept: "application/json" },
      });
      await readResponse(response);
      setUsers((current) => current.filter((item) => item.id !== user.id));
      setOverview((current) => current ? {
        ...current,
        users_total: Math.max(0, (current.users_total ?? users.length) - 1),
        users_active: Math.max(0, (current.users_active ?? users.filter((item) => item.is_active).length) - (user.is_active ? 1 : 0)),
        users_inactive: Math.max(0, (current.users_inactive ?? users.filter((item) => !item.is_active).length) - (user.is_active ? 0 : 1)),
      } : current);
      setNotice(`${label}: user permanently deleted.`);
      await loadUsers();
    } catch (err) {
      setError(err?.message || "Unable to delete this account.");
    } finally {
      setSavingUserId(null);
    }
  };

  return (
    <section className="admin-panel" aria-labelledby="admin-panel-title">
      <header className="admin-panel-header">
        <div>
          <div className="admin-eyebrow"><ShieldCheck size={15} /> Administration</div>
          <h1 id="admin-panel-title">Admin Dashboard</h1>
          <p>Manage customer access and review account status.</p>
        </div>
        <button className="admin-refresh" type="button" onClick={loadUsers} disabled={loading}>
          <RefreshCw size={16} className={loading ? "admin-spinning" : ""} /> Refresh
        </button>
      </header>

      {error && <div className="admin-alert admin-alert-error" role="alert"><AlertCircle size={17} />{error}</div>}
      {notice && <div className="admin-alert admin-alert-success" role="status"><CheckCircle2 size={17} />{notice}</div>}

      <div className="admin-stat-grid">
        <article className="admin-stat-card"><span className="admin-stat-icon"><Users size={20} /></span><span className="admin-stat-label">Customer accounts</span><strong>{loading ? "—" : counts.total}</strong><small>Accounts returned by the backend</small></article>
        <article className="admin-stat-card"><span className="admin-stat-icon"><UserCheck size={20} /></span><span className="admin-stat-label">Active accounts</span><strong>{loading ? "—" : counts.active}</strong><small>Currently enabled</small></article>
        <article className="admin-stat-card"><span className="admin-stat-icon"><UserX size={20} /></span><span className="admin-stat-label">Inactive accounts</span><strong>{loading ? "—" : counts.inactive}</strong><small>Sign-in disabled</small></article>
        <article className="admin-stat-card"><span className="admin-stat-icon"><ShieldCheck size={20} /></span><span className="admin-stat-label">Administrator accounts</span><strong>{loading ? "—" : counts.admins}</strong><small>Based on backend configuration</small></article>
      </div>

      <div className="admin-section-card admin-system-status">
        <div className="admin-table-heading"><div><h2>System configuration health</h2><p>Only configuration status is shown; secret values are never exposed.</p></div></div>
        <div className="admin-config-grid">
          <div><span>Admin configuration</span><strong className={overview?.admin_configuration_present ? "is-good" : "is-bad"}>{overview?.admin_configuration_present ? "Configured" : "Missing"}</strong></div>
          <div><span>Authentication secret</span><strong className={overview?.auth_secret_configured ? "is-good" : "is-bad"}>{overview?.auth_secret_configured ? "Configured" : "Missing / too short"}</strong></div>
          <div><span>CORS allowlist</span><strong className={overview?.cors_configured ? "is-good" : "is-bad"}>{overview?.cors_configured ? "Configured" : "Using local defaults"}</strong></div>
          <div><span>Active sessions</span><strong>{overview?.active_sessions ?? "—"}</strong></div>
        </div>
      </div>

      <div className="admin-section-card">
        <div className="admin-table-heading">
          <div><h2>Customer management</h2><p>Account status changes are enforced by the backend.</p></div>
          <label className="admin-filter-label">Filter
            <select value={filter} onChange={(event) => setFilter(event.target.value)}>
              <option value="all">All accounts</option><option value="active">Active</option><option value="inactive">Inactive</option><option value="admins">Administrators</option>
            </select>
          </label>
        </div>
        {loading ? <div className="admin-empty"><RefreshCw size={18} className="admin-spinning" /> Loading accounts…</div> :
          visibleUsers.length === 0 ? <div className="admin-empty"><Activity size={20} />No accounts match this filter.</div> :
          <div className="admin-table-wrap"><table className="admin-users-table">
            <thead><tr><th>Account</th><th>Email</th><th>User ID</th><th>Role</th><th>Status</th><th>Created</th><th>Action</th></tr></thead>
            <tbody>{visibleUsers.map((user) => <tr key={user.id}>
              <td><strong>{user.name || "Unnamed user"}</strong><span className="admin-mobile-email">{user.email || "No email"}</span></td>
              <td>{user.email || "—"}</td><td>{user.id}</td>
              <td><span className={`admin-role-pill ${user.is_admin ? "is-admin" : ""}`}>{user.is_admin ? "Admin" : "Customer"}</span></td>
              <td><span className={`admin-status-pill ${user.is_active ? "is-active" : "is-inactive"}`}>{user.is_active ? "Active" : "Inactive"}</span></td>
              <td>{user.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}</td>
              <td className="admin-user-actions"><button type="button" className={`admin-status-button ${user.is_active ? "is-disable" : "is-enable"}`} disabled={savingUserId === user.id || user.is_admin} title={user.is_admin ? "Administrator accounts cannot be changed here" : undefined} onClick={() => updateStatus(user)}>{savingUserId === user.id ? "Saving…" : user.is_active ? "Deactivate" : "Activate"}</button><button type="button" className="admin-status-button is-delete" disabled={savingUserId === user.id || user.is_admin} title={user.is_admin ? "Administrator accounts cannot be deleted here" : "Permanently delete this user"} onClick={() => deleteUser(user)}>{savingUserId === user.id ? "Working…" : "Delete"}</button></td>
            </tr>)}</tbody>
          </table></div>}
      </div>
      <div className="admin-section-card">
        <div className="admin-table-heading"><div><h2>Administrative audit log</h2><p>Recent account activation and deactivation actions.</p></div></div>
        {loading ? <div className="admin-empty">Loading activity…</div> : auditLogs.length === 0 ? <div className="admin-empty"><Activity size={20} />No administrative actions recorded yet.</div> :
          <div className="admin-table-wrap"><table className="admin-users-table">
            <thead><tr><th>Time</th><th>Action</th><th>Administrator ID</th><th>Target user ID</th><th>Details</th></tr></thead>
            <tbody>{auditLogs.map((row) => <tr key={row.id}><td>{row.created_at ? new Date(row.created_at).toLocaleString() : "—"}</td><td>{row.action.replaceAll("_", " ")}</td><td>{row.admin_user_id}</td><td>{row.target_user_id ?? "—"}</td><td>{row.details || "—"}</td></tr>)}</tbody>
          </table></div>}
      </div>

      <p className="admin-security-note"><ShieldCheck size={16} /> This page relies on server-side authorization. Hiding the menu is not the security boundary; the backend validates every administrative request.</p>
    </section>
  );
}
