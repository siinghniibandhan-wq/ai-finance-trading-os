import { useEffect, useState } from "react";

const API_URL = "https://ai-finance-trading-os-api.onrender.com";

function App() {
  const [summary, setSummary] = useState(null);
  const [netWorth, setNetWorth] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDashboard() {
    try {
      setLoading(true);
      setError("");

      const [summaryRes, netWorthRes, accountsRes] = await Promise.all([
        fetch(`${API_URL}/api/dashboard/summary`),
        fetch(`${API_URL}/api/dashboard/net-worth`),
        fetch(`${API_URL}/api/accounts/`),
      ]);

      if (!summaryRes.ok || !netWorthRes.ok || !accountsRes.ok) {
        throw new Error("Unable to load dashboard data");
      }

      const summaryData = await summaryRes.json();
      const netWorthData = await netWorthRes.json();
      const accountsData = await accountsRes.json();

      setSummary(summaryData);
      setNetWorth(netWorthData);
      setAccounts(accountsData);
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  const money = (value) =>
    new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(Number(value || 0));

  return (
    <>
      <style>{`
        * {
          box-sizing: border-box;
        }

        body {
          margin: 0;
          font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont,
            "Segoe UI", sans-serif;
          background: #f5f3ff;
          color: #171329;
        }

        button {
          font-family: inherit;
        }

        .app {
          min-height: 100vh;
        }

        .topbar {
          background: linear-gradient(135deg, #6d28d9, #9333ea, #f97316);
          color: white;
          padding: 18px 22px;
          position: sticky;
          top: 0;
          z-index: 10;
          box-shadow: 0 5px 20px rgba(91, 33, 182, 0.2);
        }

        .topbar-inner {
          max-width: 1400px;
          margin: auto;
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 15px;
        }

        .brand {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .logo {
          width: 44px;
          height: 44px;
          border-radius: 14px;
          background: rgba(255,255,255,.2);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 22px;
          font-weight: 800;
          backdrop-filter: blur(10px);
        }

        .brand h1 {
          margin: 0;
          font-size: 19px;
        }

        .brand p {
          margin: 3px 0 0;
          opacity: .85;
          font-size: 12px;
        }

        .refresh {
          border: 1px solid rgba(255,255,255,.35);
          background: rgba(255,255,255,.15);
          color: white;
          border-radius: 12px;
          padding: 10px 14px;
          cursor: pointer;
        }

        .container {
          max-width: 1400px;
          margin: auto;
          padding: 25px 18px 50px;
        }

        .welcome {
          margin-bottom: 22px;
        }

        .welcome h2 {
          margin: 0;
          font-size: 28px;
        }

        .welcome p {
          color: #6b6780;
          margin: 7px 0 0;
        }

        .cards {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 16px;
          margin-bottom: 22px;
        }

        .card {
          background: white;
          border-radius: 20px;
          padding: 20px;
          box-shadow: 0 5px 25px rgba(50, 30, 100, .07);
          border: 1px solid #ece8f8;
        }

        .card-label {
          color: #77718b;
          font-size: 13px;
          margin-bottom: 10px;
        }

        .card-value {
          font-size: 25px;
          font-weight: 800;
        }

        .networth {
          background: linear-gradient(135deg, #581c87, #7e22ce);
          color: white;
          border: none;
        }

        .networth .card-label {
          color: rgba(255,255,255,.75);
        }

        .section-grid {
          display: grid;
          grid-template-columns: 1.5fr 1fr;
          gap: 18px;
          margin-bottom: 20px;
        }

        .section-title {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .section-title h3 {
          margin: 0;
          font-size: 17px;
        }

        .small-button {
          border: 0;
          background: #f0e9ff;
          color: #6d28d9;
          padding: 8px 11px;
          border-radius: 10px;
          font-weight: 600;
        }

        .account {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 14px 0;
          border-bottom: 1px solid #eeeaf6;
        }

        .account:last-child {
          border-bottom: none;
        }

        .account-name {
          font-weight: 700;
        }

        .account-type {
          color: #817b94;
          font-size: 12px;
          margin-top: 3px;
        }

        .account-balance {
          font-weight: 800;
        }

        .empty {
          text-align: center;
          padding: 35px 10px;
          color: #8a849b;
        }

        .empty-icon {
          font-size: 34px;
          margin-bottom: 8px;
        }

        .quick-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 14px;
        }

        .quick {
          background: white;
          border: 1px solid #ece8f8;
          border-radius: 18px;
          padding: 18px;
          cursor: pointer;
          text-align: left;
          box-shadow: 0 5px 20px rgba(50,30,100,.05);
        }

        .quick:hover {
          transform: translateY(-2px);
        }

        .quick-icon {
          font-size: 25px;
          margin-bottom: 10px;
        }

        .quick-title {
          font-weight: 750;
        }

        .quick-text {
          color: #77718b;
          font-size: 12px;
          margin-top: 4px;
        }

        .status {
          margin-bottom: 18px;
          padding: 12px 15px;
          border-radius: 12px;
          background: #ecfdf5;
          color: #047857;
          font-size: 13px;
        }

        .error {
          background: #fff1f2;
          color: #be123c;
        }

        @media (max-width: 900px) {
          .cards {
            grid-template-columns: repeat(2, 1fr);
          }

          .section-grid {
            grid-template-columns: 1fr;
          }

          .quick-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        @media (max-width: 600px) {
          .topbar {
            padding: 14px;
          }

          .container {
            padding: 20px 12px 40px;
          }

          .welcome h2 {
            font-size: 23px;
          }

          .cards {
            grid-template-columns: 1fr 1fr;
            gap: 10px;
          }

          .card {
            padding: 15px;
            border-radius: 16px;
          }

          .card-value {
            font-size: 19px;
          }

          .quick-grid {
            grid-template-columns: 1fr 1fr;
            gap: 10px;
          }

          .brand h1 {
            font-size: 16px;
          }

          .refresh {
            padding: 8px 10px;
          }
        }
      `}</style>

      <div className="app">
        <header className="topbar">
          <div className="topbar-inner">
            <div className="brand">
              <div className="logo">₹</div>
              <div>
                <h1>AI Finance Trading OS</h1>
                <p>Your personal financial command center</p>
              </div>
            </div>

            <button className="refresh" onClick={loadDashboard}>
              ↻ Refresh
            </button>
          </div>
        </header>

        <main className="container">
          <div className="welcome">
            <h2>Financial Dashboard</h2>
            <p>Track your money, wealth, investments and liabilities in one place.</p>
          </div>

          {loading && (
            <div className="status">
              Loading your financial data...
            </div>
          )}

          {error && (
            <div className="status error">
              {error}
            </div>
          )}

          <div className="cards">
            <div className="card networth">
              <div className="card-label">Net Worth</div>
              <div className="card-value">
                {money(netWorth?.net_worth)}
              </div>
            </div>

            <div className="card">
              <div className="card-label">Total Assets</div>
              <div className="card-value">
                {money(netWorth?.total_assets)}
              </div>
            </div>

            <div className="card">
              <div className="card-label">Total Liabilities</div>
              <div className="card-value">
                {money(netWorth?.total_liabilities)}
              </div>
            </div>

            <div className="card">
              <div className="card-label">Investments</div>
              <div className="card-value">
                {money(summary?.investments)}
              </div>
            </div>
          </div>

          <div className="cards">
            <div className="card">
              <div className="card-label">Income</div>
              <div className="card-value">
                {money(summary?.income)}
              </div>
            </div>

            <div className="card">
              <div className="card-label">Expenses</div>
              <div className="card-value">
                {money(summary?.expenses)}
              </div>
            </div>

            <div className="card">
              <div className="card-label">Accounts</div>
              <div className="card-value">
                {accounts.length}
              </div>
            </div>

            <div className="card">
              <div className="card-label">Financial Status</div>
              <div className="card-value">
                ✓ Connected
              </div>
            </div>
          </div>

          <div className="section-grid">
            <section className="card">
              <div className="section-title">
                <h3>💳 Accounts</h3>
                <button className="small-button">View all</button>
              </div>

              {accounts.length === 0 ? (
                <div className="empty">
                  <div className="empty-icon">🏦</div>
                  <div>No active accounts yet.</div>
                  <div style={{fontSize: "12px", marginTop: "5px"}}>
                    Add your first bank or cash account.
                  </div>
                </div>
              ) : (
                accounts.map((account) => (
                  <div className="account" key={account.id}>
                    <div>
                      <div className="account-name">{account.name}</div>
                      <div className="account-type">
                        {account.account_type} • {account.institution || "Personal"}
                      </div>
                    </div>

                    <div className="account-balance">
                      {money(account.current_balance)}
                    </div>
                  </div>
                ))
              )}
            </section>

            <section className="card">
              <div className="section-title">
                <h3>📊 Wealth Overview</h3>
              </div>

              <div className="account">
                <span>Assets</span>
                <strong>{money(netWorth?.total_assets)}</strong>
              </div>

              <div className="account">
                <span>Liabilities</span>
                <strong>{money(netWorth?.total_liabilities)}</strong>
              </div>

              <div className="account">
                <span>Net Worth</span>
                <strong>{money(netWorth?.net_worth)}</strong>
              </div>
            </section>
          </div>

          <section>
            <div className="section-title">
              <h3>Quick Actions</h3>
            </div>

            <div className="quick-grid">
              <button className="quick">
                <div className="quick-icon">💰</div>
                <div className="quick-title">Add Transaction</div>
                <div className="quick-text">Record income or expense</div>
              </button>

              <button className="quick">
                <div className="quick-icon">🏦</div>
                <div className="quick-title">Add Account</div>
                <div className="quick-text">Bank, cash or credit card</div>
              </button>

              <button className="quick">
                <div className="quick-icon">📈</div>
                <div className="quick-title">Investments</div>
                <div className="quick-text">Track your portfolio</div>
              </button>

              <button className="quick">
                <div className="quick-icon">🤖</div>
                <div className="quick-title">AI Finance Chat</div>
                <div className="quick-text">Ask your financial AI</div>
              </button>
            </div>
          </section>
        </main>
      </div>
    </>
  );
}

export default App;
