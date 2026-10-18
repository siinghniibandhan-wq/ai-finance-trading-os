import React, { useEffect, useState } from "react";
import { API_BASE_URL, apiFetch, getCurrentUser } from "./api";
import "./account-contact-settings.css";

function readSessionUser() {
  try { return JSON.parse(sessionStorage.getItem("financial_os_user") || "null"); }
  catch { return null; }
}

export default function AccountContactSettings() {
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [emailPassword, setEmailPassword] = useState("");
  const [phonePassword, setPhonePassword] = useState("");
  const [loading, setLoading] = useState(true);
  const [savingEmail, setSavingEmail] = useState(false);
  const [savingPhone, setSavingPhone] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const response = await apiFetch(`${API_BASE_URL}/api/auth/me`);
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data?.detail || "Unable to load account details.");
        if (!active) return;
        setEmail(data.email || "");
        setPhone(data.phone_number || "");
        const previous = readSessionUser() || getCurrentUser() || {};
        sessionStorage.setItem("financial_os_user", JSON.stringify({ ...previous, ...data }));
      } catch (err) {
        if (active) setError(err?.message || "Unable to load account details.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, []);

  const updateContact = async (kind, event) => {
    event.preventDefault();
    setError("");
    setNotice("");
    const isEmail = kind === "email";
    const password = isEmail ? emailPassword : phonePassword;
    const value = isEmail ? email.trim().toLowerCase() : phone.trim();
    if (!value) {
      setError(isEmail ? "Enter an email address." : "Enter a phone number.");
      return;
    }
    if (!password) {
      setError("Enter your current password to confirm this change.");
      return;
    }
    isEmail ? setSavingEmail(true) : setSavingPhone(true);
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/auth/contact`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          ...(isEmail ? { email: value } : { phone_number: value }),
          current_password: password,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data?.detail || "Unable to update contact details.");
      const current = readSessionUser() || getCurrentUser() || {};
      sessionStorage.setItem("financial_os_user", JSON.stringify({ ...current, ...data.user }));
      setEmail(data.user?.email || value);
      setPhone(data.user?.phone_number || phone);
      if (isEmail) setEmailPassword(""); else setPhonePassword("");
      setNotice(isEmail
        ? "Email updated. Your new email can now be used to sign in with your existing password."
        : "Phone number updated. Your new phone number can now be used to sign in with your existing password.");
      // The header reads the session snapshot at render time; refresh it after showing success.
      window.setTimeout(() => window.location.reload(), 1400);
    } catch (err) {
      setError(err?.message || "Unable to update contact details.");
    } finally {
      isEmail ? setSavingEmail(false) : setSavingPhone(false);
    }
  };

  return <section className="account-contact-settings glass-card" aria-labelledby="account-contact-heading">
    <div className="account-contact-heading">
      <div><p className="account-contact-eyebrow">ACCOUNT SETTINGS</p><h3 id="account-contact-heading">Login contact details</h3>
      <p>Update the email address or phone number used to sign in. Your existing password remains unchanged.</p></div>
    </div>
    {error && <div className="account-contact-message is-error" role="alert">{error}</div>}
    {notice && <div className="account-contact-message is-success" role="status">{notice}</div>}
    {loading ? <p className="account-contact-loading">Loading account details…</p> : <div className="account-contact-grid">
      <form className="account-contact-form" onSubmit={(event) => updateContact("email", event)}>
        <h4>Update email address</h4>
        <label>Email address<input type="email" autoComplete="email" maxLength={255} required value={email} onChange={(event) => setEmail(event.target.value)} /></label>
        <label>Current password<input type="password" autoComplete="current-password" maxLength={128} required value={emailPassword} onChange={(event) => setEmailPassword(event.target.value)} /></label>
        <button className="primary-button" type="submit" disabled={savingEmail || savingPhone}>{savingEmail ? "Updating…" : "Update email"}</button>
      </form>
      <form className="account-contact-form" onSubmit={(event) => updateContact("phone", event)}>
        <h4>Update phone number</h4>
        <label>Phone number<input type="tel" autoComplete="tel" inputMode="tel" maxLength={25} required value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="+91 98765 43210" /></label>
        <label>Current password<input type="password" autoComplete="current-password" maxLength={128} required value={phonePassword} onChange={(event) => setPhonePassword(event.target.value)} /></label>
        <button className="primary-button" type="submit" disabled={savingEmail || savingPhone}>{savingPhone ? "Updating…" : "Update phone number"}</button>
      </form>
    </div>}
    <p className="account-contact-security">For security, each change requires your current password. Email and phone number must be unique to your account.</p>
  </section>;
}
