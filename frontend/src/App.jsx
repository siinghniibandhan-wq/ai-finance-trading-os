function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="logo">
          AI Finance
        </div>

        <nav>
          <div className="nav-item active">Dashboard</div>
          <div className="nav-item">Accounts</div>
          <div className="nav-item">Transactions</div>
          <div className="nav-item">Investments</div>
          <div className="nav-item">Assets</div>
          <div className="nav-item">Liabilities</div>
          <div className="nav-item">Trading</div>
          <div className="nav-item">AI Chat</div>
          <div className="nav-item">Reports</div>
          <div className="nav-item">Settings</div>
        </nav>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <h1>AI Finance Trading OS</h1>
        </header>

        <section className="content">
          <h2>Dashboard</h2>
          <p>Finance OS shell is working.</p>
        </section>
      </main>
    </div>
  );
}

export default App;
