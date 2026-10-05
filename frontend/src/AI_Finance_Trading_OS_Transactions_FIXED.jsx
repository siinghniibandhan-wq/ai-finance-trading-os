import React, { useEffect, useState } from "react";

/*
=====================================================
AI FINANCE TRADING OS
APP.JSX
=====================================================

NAVIGATION RULES
-----------------------------------------------------
1. Overview is the global homepage.

2. Finance itself opens Finance Overview.
   Finance does NOT contain "Finance Overview"
   as a separate submenu item.

3. Wealth itself opens Wealth Overview.

4. Investments itself opens Investment Overview.

5. Trading itself opens Trading Overview.

6. AI itself opens AI Overview.

7. Clicking the section NAME:
   - opens its overview
   - expands its submenu

8. Clicking the ARROW:
   - only expands/collapses the submenu
   - does NOT change the current page

9. Only ONE major section can be expanded at a time.

10. Accounts API is preserved.
=====================================================
*/

function App() {
  // =====================================================
  // BASIC APP STATE
  // =====================================================

  const [active, setActive] = useState("Overview");
  const [menuOpen, setMenuOpen] = useState(false);

  // =====================================================
  // EXPANDED SECTION
  // null = everything collapsed
  // =====================================================

  const [expandedSection, setExpandedSection] = useState(null);

  // =====================================================
  // ACCOUNTS STATE
  // EXISTING FUNCTIONALITY PRESERVED
  // =====================================================

  const [accounts, setAccounts] = useState([]);
  const [accountsLoading, setAccountsLoading] = useState(false);
  const [accountsError, setAccountsError] = useState("");

  // =====================================================
  // ADD ACCOUNT STATE
  // =====================================================

  const [showAddAccount, setShowAddAccount] = useState(false);

  const [accountForm, setAccountForm] = useState({
    name: "",
    account_type: "bank",
    institution: "",
    account_number: "",
    currency: "INR",
    opening_balance: ""
  });

  const [accountSaving, setAccountSaving] = useState(false);

// =====================================================
// TRANSACTIONS STATE
// NEW TRANSACTION MODULE
// =====================================================

// -----------------------------------------------------
// TRANSACTION LIST
// -----------------------------------------------------
const [transactions, setTransactions] = useState([]);
const [transactionsLoading, setTransactionsLoading] = useState(false);
const [transactionsError, setTransactionsError] = useState("");

// -----------------------------------------------------
// ADD / EDIT TRANSACTION MODAL
// -----------------------------------------------------
const [showTransactionForm, setShowTransactionForm] = useState(false);
const [editingTransaction, setEditingTransaction] = useState(null);
const [transactionSaving, setTransactionSaving] = useState(false);

// -----------------------------------------------------
// TRANSACTION FORM
// -----------------------------------------------------
const [transactionForm, setTransactionForm] = useState({
  account_id: "",
  category_id: "",
  transaction_type: "expense",
  amount: "",
  currency: "INR",
  description: "",
  merchant: "",
  reference_number: "",
  transaction_date: new Date().toISOString().slice(0, 10),
  notes: ""
});

// -----------------------------------------------------
// TRANSACTION FILTERS
// -----------------------------------------------------
const [transactionSearch, setTransactionSearch] = useState("");
const [transactionTypeFilter, setTransactionTypeFilter] = useState("all");
const [transactionAccountFilter, setTransactionAccountFilter] = useState("all");

// -----------------------------------------------------
// DELETE CONFIRMATION
// -----------------------------------------------------
const [transactionToDelete, setTransactionToDelete] = useState(null);
const [transactionDeleting, setTransactionDeleting] = useState(false);

// =====================================================
// CATEGORIES STATE
// FINANCE CATEGORY DATA
// =====================================================

const [categories, setCategories] = useState([]);
const [categoriesLoading, setCategoriesLoading] = useState(false);
const [categoriesError, setCategoriesError] = useState("");


// =====================================================
// LOAD CATEGORIES FROM BACKEND
// =====================================================

async function loadCategories() {
  setCategoriesLoading(true);
  setCategoriesError("");

  try {
    const response = await fetch(
      "https://ai-finance-trading-os-api.onrender.com/api/categories/"
    );

    if (!response.ok) {
      throw new Error("Unable to load categories.");
    }

    const data = await response.json();

    setCategories(Array.isArray(data) ? data : []);
  } catch (error) {
    setCategoriesError(
      error?.message || "Unable to load categories."
    );
  } finally {
    setCategoriesLoading(false);
  }
}


// =====================================================
// CATEGORY CRUD STATE
// =====================================================

const [showCategoryForm, setShowCategoryForm] = useState(false);
const [editingCategory, setEditingCategory] = useState(null);
const [categorySaving, setCategorySaving] = useState(false);
const [categoryToDelete, setCategoryToDelete] = useState(null);
const [categoryDeleting, setCategoryDeleting] = useState(false);

const [categoryForm, setCategoryForm] = useState({
  name: "",
  description: "",
  category_type: "expense",
  parent_id: ""
});


// =====================================================
// RESET CATEGORY FORM
// =====================================================

function resetCategoryForm() {
  setCategoryForm({
    name: "",
    description: "",
    category_type: "expense",
    parent_id: ""
  });

  setEditingCategory(null);
}


// =====================================================
// OPEN ADD CATEGORY FORM
// =====================================================

function openAddCategoryForm() {
  resetCategoryForm();
  setCategoriesError("");
  setShowCategoryForm(true);
}


// =====================================================
// OPEN EDIT CATEGORY FORM
// =====================================================

function openEditCategoryForm(category) {
  if (!category) {
    return;
  }

  setEditingCategory(category);

  setCategoryForm({
    name: category.name || "",
    description: category.description || "",
    category_type: category.category_type || "expense",
    parent_id:
      category.parent_id !== null &&
      category.parent_id !== undefined
        ? String(category.parent_id)
        : ""
  });

  setCategoriesError("");
  setShowCategoryForm(true);
}


// =====================================================
// CLOSE CATEGORY FORM
// =====================================================

function closeCategoryForm() {
  if (categorySaving) {
    return;
  }

  setShowCategoryForm(false);
  setCategoriesError("");
  resetCategoryForm();
}


// =====================================================
// SAVE CATEGORY
// CREATE / UPDATE
// =====================================================

async function saveCategory() {
  setCategoriesError("");

  const name = categoryForm.name.trim();

  if (!name) {
    setCategoriesError("Category name is required.");
    return;
  }

  if (!["income", "expense", "other"].includes(categoryForm.category_type)) {
    setCategoriesError("Please select a valid category type.");
    return;
  }

  const payload = {
    name: name,
    description: categoryForm.description.trim() || null,
    category_type: categoryForm.category_type,
    parent_id:
      categoryForm.parent_id === ""
        ? null
        : Number(categoryForm.parent_id)
  };

  setCategorySaving(true);

  try {
    const isEditing = Boolean(editingCategory);

    const url = isEditing
      ? `https://ai-finance-trading-os-api.onrender.com/api/categories/${editingCategory.id}`
      : "https://ai-finance-trading-os-api.onrender.com/api/categories/";

    const response = await fetch(url, {
      method: isEditing ? "PUT" : "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    const data = await response.json().catch(function () {
      return null;
    });

    if (!response.ok) {
      throw new Error(
        data?.detail ||
        data?.message ||
        "Unable to save category."
      );
    }

    setShowCategoryForm(false);
    resetCategoryForm();
    await loadCategories();
  } catch (error) {
    setCategoriesError(
      error?.message || "Unable to save category."
    );
  } finally {
    setCategorySaving(false);
  }
}


// =====================================================
// DELETE CATEGORY
// =====================================================

async function deleteCategory(categoryId) {
  if (!categoryId) {
    return;
  }

  setCategoryDeleting(true);
  setCategoriesError("");

  try {
    const response = await fetch(
      `https://ai-finance-trading-os-api.onrender.com/api/categories/${categoryId}`,
      {
        method: "DELETE"
      }
    );

    const data = await response.json().catch(function () {
      return null;
    });

    if (!response.ok) {
      throw new Error(
        data?.detail ||
        data?.message ||
        "Unable to delete category."
      );
    }

    setCategoryToDelete(null);
    await loadCategories();
  } catch (error) {
    setCategoriesError(
      error?.message || "Unable to delete category."
    );
  } finally {
    setCategoryDeleting(false);
  }
}


// =====================================================
// LOAD CATEGORIES WHEN CATEGORIES OR TRANSACTIONS OPENS
// =====================================================

useEffect(
  function () {
    if (
      active === "Categories" ||
      active === "Transactions"
    ) {
      loadCategories();
    }
  },
  [active]
);
  // =====================================================
  // NAVIGATION STRUCTURE
  // IMPORTANT:
  // OVERVIEW ITEMS ARE NOT SUBMENU ITEMS.
  // THE MAIN SECTION ITSELF IS THE OVERVIEW.
  // =====================================================

  const navigation = [
    {
      name: "Overview",
      icon: "🏠",
      type: "single"
    },

    {
      name: "Finance",
      icon: "💰",
      type: "section",
      children: [
        "Accounts",
        "Transactions",
        "Categories",
        "Cash Flow",
        "Budget",
        "Bills & Subscriptions",
        "Statements / Import"
      ]
    },

    {
      name: "Wealth",
      icon: "💎",
      type: "section",
      children: [
        "Assets",
        "Liabilities",
        "Net Worth",
        "Insurance",
        "Real Estate",
        "Retirement",
        "Financial Goals"
      ]
    },

    {
      name: "Investments",
      icon: "📊",
      type: "section",
      children: [
        "Portfolio",
        "Stocks",
        "Mutual Funds",
        "ETFs",
        "Bonds",
        "Gold",
        "Crypto"
      ]
    },

    {
      name: "Trading",
      icon: "📈",
      type: "section",
      children: [
        "Markets",
        "Watchlist",
        "Screener",
        "Charts",
        "Strategies",
        "Backtesting",
        "Paper Trading",
        "Live Trading",
        "Positions",
        "Orders",
        "Risk Management",
        "Trading Journal"
      ]
    },

    {
      name: "AI",
      icon: "🤖",
      type: "section",
      children: [
        "AI Chat",
        "AI Research",
        "AI Analysis",
        "AI Predictions",
        "AI Reports"
      ]
    },

    {
      name: "Reports",
      icon: "📑",
      type: "single"
    },

    {
      name: "Settings",
      icon: "⚙️",
      type: "single"
    }
  ];

  // =====================================================
  // OVERVIEW KPI DATA
  // =====================================================

  const overviewCards = [
    ["Net Worth", "₹0", "Assets − liabilities"],
    ["Total Assets", "₹0", "Current asset value"],
    ["Liabilities", "₹0", "Outstanding amount"],
    ["Investments", "₹0", "Portfolio value"]
  ];

  // =====================================================
  // SECTION OVERVIEW TITLES
  // =====================================================

  const sectionOverviewTitles = {
    Finance: "Finance Overview",
    Wealth: "Wealth Overview",
    Investments: "Investment Overview",
    Trading: "Trading Overview",
    AI: "AI Overview"
  };

  // =====================================================
  // SECTION OVERVIEW DESCRIPTIONS
  // =====================================================

  const sectionDescriptions = {
    Finance:
      "Accounts, transactions, cash flow, budgets and everyday finances.",

    Wealth:
      "Assets, liabilities, net worth, insurance and long-term wealth.",

    Investments:
      "Your investment portfolio, holdings and investment performance.",

    Trading:
      "Markets, strategies, positions, orders, risk and trading activity.",

    AI:
      "Your AI-powered financial assistant, research, analysis and reports."
  };

  // =====================================================
  // FIND PARENT SECTION
  // =====================================================

  function findParentSection(page) {
    for (let i = 0; i < navigation.length; i += 1) {
      const item = navigation[i];

      if (
        item.type === "section" &&
        item.children.indexOf(page) !== -1
      ) {
        return item.name;
      }
    }

    return null;
  }

  // =====================================================
  // OPEN MAIN SECTION
  //
  // Example:
  // Click Finance
  // -> Finance Overview
  // -> Finance expands
  // =====================================================

  function openMainSection(sectionName) {
    setActive(sectionName);
    setExpandedSection(sectionName);
    setMenuOpen(false);
  }

  // =====================================================
  // TOGGLE ONLY THE ARROW
  //
  // IMPORTANT:
  // This does NOT change active page.
  // =====================================================

  function toggleSection(sectionName) {
    setExpandedSection(function (current) {
      if (current === sectionName) {
        return null;
      }

      return sectionName;
    });
  }

  // =====================================================
  // OPEN SINGLE PAGE
  //
  // Overview / Reports / Settings
  // collapse all major sections.
  // =====================================================

  function openSinglePage(page) {
    setActive(page);
    setExpandedSection(null);
    setMenuOpen(false);
  }

  // =====================================================
  // OPEN SUBPAGE
  // =====================================================

  function openSubPage(page, parentSection) {
    setActive(page);
    setExpandedSection(parentSection);
    setMenuOpen(false);
  }

  // =====================================================
  // LOAD ACCOUNTS
  //
  // EXISTING API URL PRESERVED
  // =====================================================

  async function loadAccounts() {
    setAccountsLoading(true);
    setAccountsError("");

    try {
      const response = await fetch(
        "https://ai-finance-trading-os-api.onrender.com/api/accounts/"
      );

      if (!response.ok) {
        throw new Error("Unable to load accounts.");
      }

      const data = await response.json();

      setAccounts(Array.isArray(data) ? data : []);
    } catch (error) {
      setAccountsError(
        error?.message || "Unable to load accounts."
      );
    } finally {
      setAccountsLoading(false);
    }
  }

  // =====================================================
  // LOAD ACCOUNTS WHEN ACCOUNTS PAGE OPENS
  // =====================================================

  useEffect(
    function () {
      if (
        active === "Accounts" ||
        active === "Transactions"
      ) {
        loadAccounts();
      }
    },
    [active]
  );

  // =====================================================
  // ADD ACCOUNT — FORM FIELD HANDLER
  // =====================================================

  function updateAccountForm(field, value) {
    setAccountForm(function (current) {
      return {
        ...current,
        [field]: value
      };
    });
  }

  // =====================================================
  // ADD ACCOUNT — RESET FORM
  // =====================================================

  function resetAccountForm() {
    setAccountForm({
      name: "",
      account_type: "bank",
      institution: "",
      account_number: "",
      currency: "INR",
      opening_balance: ""
    });

    setAccountsError("");
  }

  // =====================================================
  // ADD ACCOUNT — SUBMIT
  //
  // Uses the existing Accounts API.
  // =====================================================

  async function createAccount() {
    setAccountsError("");

    if (!accountForm.name.trim()) {
      setAccountsError("Account name is required.");
      return;
    }

    const openingBalance =
      accountForm.opening_balance === ""
        ? 0
        : Number(accountForm.opening_balance);

    if (!Number.isFinite(openingBalance)) {
      setAccountsError("Opening balance must be a valid number.");
      return;
    }

    setAccountSaving(true);

    try {
      const response = await fetch(
        "https://ai-finance-trading-os-api.onrender.com/api/accounts/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            name: accountForm.name.trim(),
            account_type: accountForm.account_type,
            institution: accountForm.institution.trim() || null,
            account_number: accountForm.account_number.trim() || null,
            currency: accountForm.currency,
            opening_balance: openingBalance
          })
        }
      );

      const data = await response.json().catch(function () {
        return null;
      });

      if (!response.ok) {
        throw new Error(
          data?.detail ||
          data?.message ||
          "Unable to create account."
        );
      }

      resetAccountForm();
      setShowAddAccount(false);

      // Reload from the database so the UI shows the saved record.
      await loadAccounts();
    } catch (error) {
      setAccountsError(
        error?.message || "Unable to create account."
      );
    } finally {
      setAccountSaving(false);
    }
  }

   // =====================================================
// TRANSACTIONS API
// LOAD TRANSACTIONS
// =====================================================

async function loadTransactions() {
  setTransactionsLoading(true);
  setTransactionsError("");

  try {
    const response = await fetch(
      "https://ai-finance-trading-os-api.onrender.com/api/transactions/"
    );

    if (!response.ok) {
      throw new Error("Unable to load transactions.");
    }

    const data = await response.json();

    setTransactions(Array.isArray(data) ? data : []);
  } catch (error) {
    setTransactionsError(
      error?.message || "Unable to load transactions."
    );
  } finally {
    setTransactionsLoading(false);
  }
}


// =====================================================
// LOAD TRANSACTIONS WHEN TRANSACTIONS PAGE OPENS
// =====================================================

useEffect(
  function () {
    if (active === "Transactions") {
      loadTransactions();
    }
  },
  [active]
);


// =====================================================
// TRANSACTION FORM FIELD HANDLER
// =====================================================

function updateTransactionForm(field, value) {
  setTransactionForm(function (current) {
    return {
      ...current,
      [field]: value
    };
  });
}


// =====================================================
// RESET TRANSACTION FORM
// =====================================================

function resetTransactionForm() {
  setTransactionForm({
    account_id: "",
    category_id: "",
    transaction_type: "expense",
    amount: "",
    currency: "INR",
    description: "",
    merchant: "",
    reference_number: "",
    transaction_date: new Date().toISOString().slice(0, 10),
    notes: ""
  });

  setEditingTransaction(null);
  setTransactionsError("");
}


// =====================================================
// OPEN NEW TRANSACTION FORM
// =====================================================

async function openNewTransactionForm() {
  resetTransactionForm();

  // ---------------------------------------------------
  // ENSURE ACCOUNTS ARE AVAILABLE
  // ---------------------------------------------------
  // Transactions depend on an active account. If the page
  // was opened directly, load the latest accounts first.
  let availableAccounts = accounts;

  if (!Array.isArray(availableAccounts) || availableAccounts.length === 0) {
    try {
      await loadAccounts();
      availableAccounts = accounts;
    } catch (error) {
      // The normal save validation will show the account error.
    }
  }

  // Automatically select the first available account.
  if (Array.isArray(availableAccounts) && availableAccounts.length > 0) {
    setTransactionForm(function (current) {
      return {
        ...current,
        account_id: String(availableAccounts[0].id)
      };
    });
  }

  setShowTransactionForm(true);
}


// =====================================================
// OPEN EDIT TRANSACTION FORM
// =====================================================

function openEditTransactionForm(transaction) {
  setEditingTransaction(transaction);

  setTransactionForm({
    account_id:
      transaction.account_id !== null &&
      transaction.account_id !== undefined
        ? String(transaction.account_id)
        : "",

    category_id:
      transaction.category_id !== null &&
      transaction.category_id !== undefined
        ? String(transaction.category_id)
        : "",

    transaction_type:
      transaction.transaction_type || "expense",

    amount:
      transaction.amount !== null &&
      transaction.amount !== undefined
        ? String(transaction.amount)
        : "",

    currency:
      transaction.currency || "INR",

    description:
      transaction.description || "",

    merchant:
      transaction.merchant || "",

    reference_number:
      transaction.reference_number || "",

    transaction_date:
      transaction.transaction_date
        ? String(transaction.transaction_date).slice(0, 10)
        : new Date().toISOString().slice(0, 10),

    notes:
      transaction.notes || ""
  });

  setTransactionsError("");
  setShowTransactionForm(true);
}


// =====================================================
// CLOSE TRANSACTION FORM
// =====================================================

function closeTransactionForm() {
  if (transactionSaving) {
    return;
  }

  setShowTransactionForm(false);
  setEditingTransaction(null);
  setTransactionsError("");
}


// =====================================================
// CREATE / UPDATE TRANSACTION
// =====================================================

async function saveTransaction() {
  setTransactionsError("");

  // ---------------------------------------------------
  // BASIC VALIDATION
  // ---------------------------------------------------

  if (!transactionForm.account_id) {
    setTransactionsError("Please select an account.");
    return;
  }

  const amount = Number(transactionForm.amount);

  if (!Number.isFinite(amount) || amount <= 0) {
    setTransactionsError("Amount must be greater than zero.");
    return;
  }

  if (!transactionForm.transaction_date) {
    setTransactionsError("Transaction date is required.");
    return;
  }

  // ---------------------------------------------------
  // PREPARE API DATA
  // ---------------------------------------------------

  const payload = {
    account_id: Number(transactionForm.account_id),

    category_id:
      transactionForm.category_id === ""
        ? null
        : Number(transactionForm.category_id),

    transaction_type: transactionForm.transaction_type,

    amount: amount,

    currency: transactionForm.currency || "INR",

    description:
      transactionForm.description.trim() || null,

    merchant:
      transactionForm.merchant.trim() || null,

    reference_number:
      transactionForm.reference_number.trim() || null,

    transaction_date:
      transactionForm.transaction_date,

    notes:
      transactionForm.notes.trim() || null
  };

  setTransactionSaving(true);

  try {
    const isEditing = Boolean(editingTransaction);

    const url = isEditing
      ? `https://ai-finance-trading-os-api.onrender.com/api/transactions/${editingTransaction.id}`
      : "https://ai-finance-trading-os-api.onrender.com/api/transactions/";

    const response = await fetch(url, {
      method: isEditing ? "PUT" : "POST",

      headers: {
        "Content-Type": "application/json"
      },

      body: JSON.stringify(payload)
    });

    const data = await response.json().catch(function () {
      return null;
    });

    if (!response.ok) {
      throw new Error(
        data?.detail ||
        data?.message ||
        "Unable to save transaction."
      );
    }

    // -------------------------------------------------
    // SUCCESS
    // -------------------------------------------------

    resetTransactionForm();
    setShowTransactionForm(false);

    // Reload accounts because transaction balance
    // changes the account's current balance.
    await loadAccounts();

    // Reload transactions so the table is current.
    await loadTransactions();

  } catch (error) {
    setTransactionsError(
      error?.message || "Unable to save transaction."
    );
  } finally {
    setTransactionSaving(false);
  }
}


// =====================================================
// DELETE TRANSACTION
// =====================================================

async function deleteTransaction(transactionId) {
  if (!transactionId) {
    return;
  }

  setTransactionDeleting(true);
  setTransactionsError("");

  try {
    const response = await fetch(
      `https://ai-finance-trading-os-api.onrender.com/api/transactions/${transactionId}`,
      {
        method: "DELETE"
      }
    );

    const data = await response.json().catch(function () {
      return null;
    });

    if (!response.ok) {
      throw new Error(
        data?.detail ||
        data?.message ||
        "Unable to delete transaction."
      );
    }

    // -------------------------------------------------
    // SUCCESS
    // -------------------------------------------------

    setTransactionToDelete(null);

    // The backend reverses the transaction's balance
    // effect when the transaction is deleted.
    await loadAccounts();

    await loadTransactions();

  } catch (error) {
    setTransactionsError(
      error?.message || "Unable to delete transaction."
    );
  } finally {
    setTransactionDeleting(false);
  }
}


// =====================================================
// TRANSACTION TYPE LABEL
// =====================================================

function transactionTypeLabel(type) {
  if (!type) {
    return "Transaction";
  }

  return String(type)
    .replaceAll("_", " ")
    .replace(/\b\w/g, function (letter) {
      return letter.toUpperCase();
    });
    }
  // =====================================================
  // MONEY FORMATTER
  // =====================================================

  function formatMoney(value, currency) {
    const amount = Number(value || 0);

    return `${currency || "INR"} ${amount.toLocaleString(
      "en-IN",
      {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }
    )}`;
  }

  // =====================================================
  // ACCOUNT TYPE LABEL
  // =====================================================

  function accountTypeLabel(type) {
    if (!type) {
      return "Account";
    }

    return String(type)
      .replaceAll("_", " ")
      .replace(/\b\w/g, function (letter) {
        return letter.toUpperCase();
      });
  }

  // =====================================================
  // DETERMINE CURRENT OVERVIEW SECTION
  // =====================================================

  function getCurrentOverviewSection() {
    if (
      active === "Finance" ||
      active === "Wealth" ||
      active === "Investments" ||
      active === "Trading" ||
      active === "AI"
    ) {
      return active;
    }

    return null;
  }

  // =====================================================
  // PAGE TITLE
  // =====================================================

  function getPageTitle() {
    const overviewSection = getCurrentOverviewSection();

    if (overviewSection) {
      return sectionOverviewTitles[overviewSection];
    }

    if (active === "Overview") {
      return "Overview";
    }

    return active;
  }

  // =====================================================
  // PAGE DESCRIPTION
  // =====================================================

  function getPageDescription() {
    const overviewSection = getCurrentOverviewSection();

    if (overviewSection) {
      return sectionDescriptions[overviewSection];
    }

    const descriptions = {
      Accounts:
        "Manage your bank accounts, cash, credit cards and wallets.",

      Transactions:
        "View and manage your financial transactions.",

      Categories:
        "Organize your income and expense categories.",

      "Cash Flow":
        "Understand money coming in and going out.",

      Budget:
        "Plan and control your spending.",

      "Bills & Subscriptions":
        "Track recurring bills and subscriptions.",

      "Statements / Import":
        "Import and reconcile financial statements.",

      Assets:
        "Manage everything you own.",

      Liabilities:
        "Manage loans, credit cards and other obligations.",

      "Net Worth":
        "Track your total wealth over time.",

      Insurance:
        "Track insurance policies and coverage.",

      "Real Estate":
        "Manage property and real estate holdings.",

      Retirement:
        "Plan and track retirement assets.",

      "Financial Goals":
        "Set and track your long-term financial goals.",

      Portfolio:
        "Track investment holdings and performance.",

      Stocks:
        "Manage and analyze stock investments.",

      "Mutual Funds":
        "Manage mutual fund investments.",

      ETFs:
        "Manage exchange-traded funds.",

      Bonds:
        "Track fixed-income investments.",

      Gold:
        "Track gold holdings.",

      Crypto:
        "Track cryptocurrency investments.",

      Markets:
        "Market intelligence and market data.",

      Watchlist:
        "Track instruments you are watching.",

      Screener:
        "Find instruments using custom filters.",

      Charts:
        "Analyze price charts and technical indicators.",

      Strategies:
        "Build and manage trading strategies.",

      Backtesting:
        "Test trading strategies against historical data.",

      "Paper Trading":
        "Practice trading without real money.",

      "Live Trading":
        "Manage connected live trading activity.",

      Positions:
        "Monitor open and closed trading positions.",

      Orders:
        "Track trading orders.",

      "Risk Management":
        "Monitor exposure and trading risk.",

      "Trading Journal":
        "Record and analyze trading decisions.",

      "AI Chat":
        "Talk to your AI financial assistant.",

      "AI Research":
        "AI-powered financial and market research.",

      "AI Analysis":
        "AI-powered analysis of your financial data.",

      "AI Predictions":
        "AI-generated predictions and scenarios.",

      "AI Reports":
        "Generate intelligent financial reports.",

      Reports:
        "Financial, investment, trading and tax reporting.",

      Settings:
        "Configure your Finance OS."
    };

    return (
      descriptions[active] ||
      "This module will be connected to the Finance OS engine."
    );
  }

  // =====================================================
  // GLOBAL STYLES
  // =====================================================

  const styles = `
    * {
      box-sizing: border-box;
    }

    html,
    body,
    #root {
      margin: 0;
      min-height: 100%;
      width: 100%;
    }

    body {
      font-family: Arial, sans-serif;
      background: #f5f3fb;
      color: #18152b;
    }

    button {
      font-family: inherit;
    }

    /* =================================================
       APP
       ================================================= */

    .finance-app {
      min-height: 100vh;
      display: flex;
      background: #f5f3fb;
    }

    /* =================================================
       SIDEBAR
       ================================================= */

    .finance-sidebar {
      width: 275px;
      min-height: 100vh;
      flex-shrink: 0;
      background: #ffffff;
      border-right: 1px solid #e8e3f4;
      padding: 20px 13px;
      overflow-y: auto;
    }

    .brand {
      padding: 5px 13px 23px;
      font-size: 21px;
      font-weight: 800;
    }

    .brand span {
      color: #7048ff;
    }

    /* =================================================
       MAIN NAVIGATION BUTTON
       ================================================= */

    .main-nav-row {
      display: flex;
      width: 100%;
      margin-bottom: 3px;
    }

    .main-nav-button {
      flex: 1;
      min-width: 0;
      border: 0;
      background: transparent;
      border-radius: 10px 0 0 10px;
      padding: 11px 12px;
      display: flex;
      align-items: center;
      gap: 9px;
      cursor: pointer;
      color: #514c61;
      font-size: 14px;
      text-align: left;
    }

    .main-nav-button:hover {
      background: #f5f1ff;
    }

    .main-nav-button.active-main {
      background: #eee8ff;
      color: #5530d9;
      font-weight: 700;
    }

    .nav-arrow-button {
      width: 42px;
      border: 0;
      background: transparent;
      border-radius: 0 10px 10px 0;
      color: #817b91;
      cursor: pointer;
      font-size: 11px;
    }

    .nav-arrow-button:hover {
      background: #f5f1ff;
      color: #5530d9;
    }

    .main-nav-row.active-row .nav-arrow-button {
      background: #eee8ff;
      color: #5530d9;
    }

    .nav-left {
      display: flex;
      align-items: center;
      gap: 9px;
      min-width: 0;
    }

    .nav-icon {
      width: 22px;
      text-align: center;
      flex-shrink: 0;
    }

    /* =================================================
       SUB NAVIGATION
       ================================================= */

    .sub-nav {
      padding: 2px 0 7px 30px;
    }

    .sub-nav-button {
      width: 100%;
      border: 0;
      background: transparent;
      color: #777184;
      border-radius: 8px;
      padding: 9px 10px;
      text-align: left;
      cursor: pointer;
      font-size: 13px;
      margin-bottom: 2px;
    }

    .sub-nav-button:hover {
      background: #f7f4ff;
      color: #5530d9;
    }

    .sub-nav-button.active {
      background: #eee8ff;
      color: #5530d9;
      font-weight: 700;
    }

    /* =================================================
       MAIN AREA
       ================================================= */

    .finance-main {
      flex: 1;
      min-width: 0;
    }

    .topbar {
      height: 72px;
      background: #ffffff;
      border-bottom: 1px solid #e8e3f4;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 26px;
      position: sticky;
      top: 0;
      z-index: 20;
    }

    .top-left {
      display: flex;
      align-items: center;
    }

    .top-title small {
      display: block;
      color: #8b859b;
      font-size: 12px;
      margin-bottom: 3px;
    }

    .top-title strong {
      font-size: 21px;
    }

    .profile {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: #eee8ff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      color: #5c3bdd;
    }

    .mobile-menu {
      display: none;
    }

    /* =================================================
       PAGE
       ================================================= */

    .page {
      padding: 26px;
      max-width: 1500px;
    }

    .page-heading {
      margin-bottom: 20px;
    }

    .page-heading h2 {
      margin: 0 0 5px;
      font-size: 24px;
    }

    .page-heading p {
      margin: 0;
      color: #817b91;
      font-size: 14px;
    }

    /* =================================================
       KPI
       ================================================= */

    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 15px;
    }

    .kpi {
      background: #ffffff;
      border: 1px solid #e8e3f4;
      border-radius: 16px;
      padding: 19px;
    }

    .kpi-label {
      color: #858092;
      font-size: 13px;
      margin-bottom: 10px;
    }

    .kpi-value {
      font-size: 27px;
      font-weight: 800;
      margin-bottom: 6px;
    }

    .kpi-note {
      color: #9993a4;
      font-size: 12px;
    }

    /* =================================================
       PANELS
       ================================================= */

    .dashboard-grid {
      display: grid;
      grid-template-columns: minmax(0, 2fr) minmax(280px, 1fr);
      gap: 15px;
      margin-top: 15px;
    }

    .panel {
      background: #ffffff;
      border: 1px solid #e8e3f4;
      border-radius: 16px;
      padding: 20px;
    }

    .panel h3 {
      margin: 0 0 6px;
      font-size: 17px;
    }

    .panel-subtitle {
      color: #858092;
      font-size: 13px;
      margin-bottom: 20px;
    }

    .chart-placeholder {
      height: 190px;
      border-radius: 12px;
      background: #faf9fd;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #9993a4;
      font-size: 13px;
    }

    .ai-panel {
      background: linear-gradient(145deg, #ffffff, #f8f5ff);
    }

    .ai-icon {
      width: 44px;
      height: 44px;
      border-radius: 13px;
      background: #eee8ff;
      color: #6940ed;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      margin-bottom: 15px;
    }

    .ai-text {
      color: #716b7d;
      font-size: 13px;
      line-height: 1.55;
    }

    /* =================================================
       QUICK ACTIONS
       ================================================= */

    .quick-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin-top: 15px;
    }

    .quick {
      background: #ffffff;
      border: 1px solid #e8e3f4;
      border-radius: 13px;
      padding: 15px;
      cursor: pointer;
    }

    .quick strong {
      display: block;
      margin-bottom: 5px;
    }

    .quick span {
      font-size: 12px;
      color: #8b859b;
    }

    /* =================================================
       ACCOUNTS
       ================================================= */

    .accounts-summary {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 15px;
      margin-bottom: 20px;
    }

    .summary-card {
      background: #ffffff;
      border: 1px solid #e8e3f4;
      border-radius: 16px;
      padding: 18px;
    }

    .summary-label {
      color: #858092;
      font-size: 13px;
      margin-bottom: 8px;
    }

    .summary-value {
      font-size: 23px;
      font-weight: 800;
    }

    .accounts-list {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 15px;
    }

    .account-card {
      background: #ffffff;
      border: 1px solid #e8e3f4;
      border-radius: 16px;
      padding: 19px;
    }

    .account-name {
      font-size: 17px;
      font-weight: 700;
      word-break: break-word;
    }

    .account-type {
      display: inline-block;
      margin-top: 6px;
      padding: 5px 9px;
      border-radius: 8px;
      background: #f0ecff;
      color: #6040dc;
      font-size: 11px;
      font-weight: 700;
    }

    .account-balance {
      margin-top: 22px;
      font-size: 24px;
      font-weight: 800;
    }

    .account-meta {
      margin-top: 9px;
      color: #858092;
      font-size: 12px;
      line-height: 1.6;
    }

    .account-empty {
      background: #ffffff;
      border: 1px dashed #d9d2e9;
      border-radius: 16px;
      padding: 45px 20px;
      text-align: center;
      color: #858092;
      grid-column: 1 / -1;
    }

    .account-error {
      background: #fff1f1;
      border: 1px solid #f1caca;
      color: #a33333;
      border-radius: 12px;
      padding: 14px;
      margin-bottom: 15px;
    }

    /* =================================================
       ADD ACCOUNT FORM
       ================================================= */

    .accounts-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 20px;
    }

    .add-account-button {
      border: 0;
      background: #7048ff;
      color: #ffffff;
      border-radius: 10px;
      padding: 11px 17px;
      font-weight: 700;
      cursor: pointer;
      white-space: nowrap;
    }

    .add-account-button:hover {
      background: #5f38e8;
    }

    .account-form-card {
      background: #ffffff;
      border: 1px solid #e8e3f4;
      border-radius: 16px;
      padding: 20px;
      margin-bottom: 20px;
    }

    .account-form-title {
      margin: 0 0 16px;
      font-size: 18px;
      font-weight: 800;
    }

    .account-form-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }

    .account-field {
      min-width: 0;
    }

    .account-field.full {
      grid-column: 1 / -1;
    }

    .account-field label {
      display: block;
      margin-bottom: 6px;
      color: #625c70;
      font-size: 12px;
      font-weight: 700;
    }

    .account-field input,
    .account-field select {
      width: 100%;
      min-height: 44px;
      border: 1px solid #ddd7ea;
      border-radius: 10px;
      background: #ffffff;
      color: #18152b;
      padding: 10px 12px;
      font-size: 14px;
      outline: none;
    }

    .account-field input:focus,
    .account-field select:focus {
      border-color: #7048ff;
      box-shadow: 0 0 0 3px rgba(112, 72, 255, 0.10);
    }

    .account-form-actions {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      margin-top: 18px;
    }

    .account-cancel-button {
      border: 1px solid #ddd7ea;
      background: #ffffff;
      color: #5d566a;
      border-radius: 10px;
      padding: 10px 16px;
      font-weight: 700;
      cursor: pointer;
    }

    .account-save-button {
      border: 0;
      background: #7048ff;
      color: #ffffff;
      border-radius: 10px;
      padding: 10px 18px;
      font-weight: 700;
      cursor: pointer;
    }

    .account-save-button:disabled,
    .account-cancel-button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    /* =================================================
       MODULE PAGE
       ================================================= */

    .module-card {
      background: #ffffff;
      border: 1px solid #e8e3f4;
      border-radius: 16px;
      padding: 28px;
      min-height: 220px;
    }

    .module-icon {
      font-size: 36px;
      margin-bottom: 12px;
    }

    .module-card h3 {
      margin: 0 0 8px;
      font-size: 20px;
    }

    .module-card p {
      color: #817b91;
      font-size: 14px;
      line-height: 1.6;
      max-width: 700px;
    }

    /* =================================================
       MOBILE
       ================================================= */

    .mobile-bottom {
      display: none;
    }

    .drawer {
      display: none;
    }

    @media (max-width: 1050px) {
      .finance-sidebar {
        width: 240px;
      }

      .kpi-grid {
        grid-template-columns: repeat(2, 1fr);
      }

      .dashboard-grid {
        grid-template-columns: 1fr;
      }

      .accounts-list {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    @media (max-width: 700px) {
      .finance-app {
        display: block;
        padding-bottom: 70px;
      }

      .finance-sidebar {
        display: none;
      }

      .topbar {
        height: 64px;
        padding: 0 15px;
      }

      .mobile-menu {
        display: flex;
        width: 40px;
        height: 40px;
        border: 0;
        border-radius: 11px;
        background: #f0ebff;
        color: #5935d9;
        align-items: center;
        justify-content: center;
        font-size: 21px;
        margin-right: 10px;
        cursor: pointer;
      }

      .top-title small {
        display: none;
      }

      .top-title strong {
        font-size: 18px;
      }

      .profile {
        width: 36px;
        height: 36px;
      }

      .page {
        padding: 18px 15px 25px;
      }

      .page-heading h2 {
        font-size: 21px;
      }

      .kpi-grid {
        grid-template-columns: 1fr 1fr;
        gap: 10px;
      }

      .kpi {
        padding: 15px;
      }

      .kpi-value {
        font-size: 22px;
      }

      .dashboard-grid {
        grid-template-columns: 1fr;
        gap: 10px;
      }

      .panel {
        padding: 17px;
      }

      .chart-placeholder {
        height: 150px;
      }

      .quick-grid {
        grid-template-columns: 1fr 1fr;
        gap: 10px;
      }

      .accounts-summary {
        grid-template-columns: 1fr 1fr;
        gap: 10px;
      }

      .accounts-list {
        grid-template-columns: 1fr;
        gap: 10px;
      }

      .account-card {
        padding: 17px;
      }

      .account-form-grid {
        grid-template-columns: 1fr;
      }

      .account-field.full {
        grid-column: auto;
      }

      .accounts-toolbar {
        align-items: flex-start;
      }

      .add-account-button {
        flex-shrink: 0;
      }

      /* =============================================
         MOBILE BOTTOM NAV
         ============================================= */

      .mobile-bottom {
        position: fixed;
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        bottom: 0;
        left: 0;
        right: 0;
        height: 64px;
        background: #ffffff;
        border-top: 1px solid #e5e1f0;
        z-index: 40;
      }

      .bottom-item {
        border: 0;
        background: transparent;
        color: #77718c;
        font-size: 10px;
        cursor: pointer;
      }

      .bottom-item.active {
        color: #6040dc;
        font-weight: 700;
      }

      .bottom-icon {
        display: block;
        font-size: 18px;
        margin-bottom: 3px;
      }

      /* =============================================
         MOBILE DRAWER
         ============================================= */

      .drawer-overlay {
        position: fixed;
        inset: 0;
        background: rgba(20, 16, 35, 0.38);
        z-index: 80;
      }

      .drawer {
        display: block;
        position: fixed;
        top: 0;
        left: 0;
        width: 300px;
        max-width: 86vw;
        height: 100vh;
        overflow-y: auto;
        background: #ffffff;
        z-index: 90;
        padding: 20px 15px;
        box-shadow: 8px 0 30px rgba(0,0,0,0.14);
      }

      .drawer-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 5px 8px 20px;
      }

      .drawer-brand {
        font-size: 20px;
        font-weight: 800;
      }

      .drawer-close {
        width: 36px;
        height: 36px;
        border: 0;
        border-radius: 10px;
        background: #f2eff8;
        font-size: 20px;
        cursor: pointer;
      }

      .drawer-main-row {
        display: flex;
        width: 100%;
        margin-bottom: 3px;
      }

      .drawer-main-button {
        flex: 1;
        border: 0;
        background: transparent;
        border-radius: 10px 0 0 10px;
        padding: 12px 10px;
        display: flex;
        align-items: center;
        gap: 8px;
        text-align: left;
        cursor: pointer;
        color: #514c61;
        font-size: 14px;
      }

      .drawer-main-button.active {
        background: #eee8ff;
        color: #5535d9;
        font-weight: 700;
      }

      .drawer-arrow-button {
        width: 42px;
        border: 0;
        background: transparent;
        border-radius: 0 10px 10px 0;
        cursor: pointer;
        color: #817b91;
      }

      .drawer-arrow-button:hover {
        background: #f5f1ff;
      }

      .drawer-sub {
        padding-left: 26px;
        padding-bottom: 5px;
      }

      .drawer-sub button {
        width: 100%;
        border: 0;
        background: transparent;
        color: #777184;
        border-radius: 8px;
        padding: 10px;
        text-align: left;
        cursor: pointer;
        font-size: 13px;
      }

      .drawer-sub button.active {
        background: #eee8ff;
        color: #5535d9;
        font-weight: 700;
      }
    }

    @media (max-width: 420px) {
      .kpi-grid {
        grid-template-columns: 1fr;
      }

      .accounts-summary {
        grid-template-columns: 1fr;
      }
    }
  `;

  // =====================================================
  // DESKTOP NAVIGATION
  // =====================================================

  function renderDesktopNavigation() {
    return navigation.map(function (item) {
      // -------------------------------------------------
      // SINGLE ITEM
      // -------------------------------------------------

      if (item.type === "single") {
        return React.createElement(
          "button",
          {
            key: item.name,
            className:
              active === item.name
                ? "main-nav-button active-main"
                : "main-nav-button",
            onClick: function () {
              openSinglePage(item.name);
            }
          },

          React.createElement(
            "span",
            { className: "nav-left" },

            React.createElement(
              "span",
              { className: "nav-icon" },
              item.icon
            ),

            item.name
          )
        );
      }

      // -------------------------------------------------
      // MAIN SECTION
      // -------------------------------------------------

      const sectionIsActive =
        active === item.name ||
        findParentSection(active) === item.name;

      return React.createElement(
        React.Fragment,
        { key: item.name },

        React.createElement(
          "div",
          {
            className:
              sectionIsActive
                ? "main-nav-row active-row"
                : "main-nav-row"
          },

          // ---------------------------------------------
          // SECTION NAME
          // ---------------------------------------------

          React.createElement(
            "button",
            {
              className:
                sectionIsActive
                  ? "main-nav-button active-main"
                  : "main-nav-button",

              onClick: function () {
                openMainSection(item.name);
              }
            },

            React.createElement(
              "span",
              { className: "nav-left" },

              React.createElement(
                "span",
                { className: "nav-icon" },
                item.icon
              ),

              item.name
            )
          ),

          // ---------------------------------------------
          // ARROW
          // ONLY COLLAPSES / EXPANDS
          // ---------------------------------------------

          React.createElement(
            "button",
            {
              className: "nav-arrow-button",

              onClick: function (event) {
                event.stopPropagation();
                toggleSection(item.name);
              },

              "aria-label":
                expandedSection === item.name
                  ? `Collapse ${item.name}`
                  : `Expand ${item.name}`
            },

            expandedSection === item.name
              ? "▲"
              : "▼"
          )
        ),

        // -----------------------------------------------
        // CHILDREN
        // -----------------------------------------------

        expandedSection === item.name &&
          React.createElement(
            "div",
            { className: "sub-nav" },

            item.children.map(function (child) {
              return React.createElement(
                "button",
                {
                  key: child,

                  className:
                    active === child
                      ? "sub-nav-button active"
                      : "sub-nav-button",

                  onClick: function () {
                    openSubPage(child, item.name);
                  }
                },

                child
              );
            })
          )
      );
    });
  }

  // =====================================================
  // MOBILE NAVIGATION
  // =====================================================

  function renderMobileNavigation() {
    return navigation.map(function (item) {
      // -------------------------------------------------
      // SINGLE ITEM
      // -------------------------------------------------

      if (item.type === "single") {
        return React.createElement(
          "button",
          {
            key: item.name,

            className:
              active === item.name
                ? "drawer-main-button active"
                : "drawer-main-button",

            onClick: function () {
              openSinglePage(item.name);
            }
          },

          React.createElement(
            "span",
            { className: "nav-left" },

            React.createElement(
              "span",
              { className: "nav-icon" },
              item.icon
            ),

            item.name
          )
        );
      }

      // -------------------------------------------------
      // SECTION
      // -------------------------------------------------

      const sectionIsActive =
        active === item.name ||
        findParentSection(active) === item.name;

      return React.createElement(
        React.Fragment,
        { key: item.name },

        React.createElement(
          "div",
          {
            className:
              sectionIsActive
                ? "drawer-main-row active-row"
                : "drawer-main-row"
          },

          // ---------------------------------------------
          // SECTION NAME
          // ---------------------------------------------

          React.createElement(
            "button",
            {
              className:
                sectionIsActive
                  ? "drawer-main-button active"
                  : "drawer-main-button",

              onClick: function () {
                openMainSection(item.name);
              }
            },

            React.createElement(
              "span",
              { className: "nav-left" },

              React.createElement(
                "span",
                { className: "nav-icon" },
                item.icon
              ),

              item.name
            )
          ),

          // ---------------------------------------------
          // MOBILE ARROW
          // ---------------------------------------------

          React.createElement(
            "button",
            {
              className: "drawer-arrow-button",

              onClick: function (event) {
                event.stopPropagation();
                toggleSection(item.name);
              }
            },

            expandedSection === item.name
              ? "▲"
              : "▼"
          )
        ),

        // -----------------------------------------------
        // MOBILE CHILDREN
        // -----------------------------------------------

        expandedSection === item.name &&
          React.createElement(
            "div",
            { className: "drawer-sub" },

            item.children.map(function (child) {
              return React.createElement(
                "button",
                {
                  key: child,

                  className:
                    active === child
                      ? "active"
                      : "",

                  onClick: function () {
                    openSubPage(child, item.name);
                  }
                },

                child
              );
            })
          )
      );
    });
  }

  // =====================================================
  // GLOBAL OVERVIEW
  // =====================================================

  function renderOverview() {
    return React.createElement(
      React.Fragment,
      null,

      React.createElement(
        "div",
        { className: "page-heading" },

        React.createElement(
          "h2",
          null,
          "Overview"
        ),

        React.createElement(
          "p",
          null,
          "Everything at a glance across your financial life."
        )
      ),

      React.createElement(
        "div",
        { className: "kpi-grid" },

        overviewCards.map(function (card) {
          return React.createElement(
            "div",
            {
              className: "kpi",
              key: card[0]
            },

            React.createElement(
              "div",
              { className: "kpi-label" },
              card[0]
            ),

            React.createElement(
              "div",
              { className: "kpi-value" },
              card[1]
            ),

            React.createElement(
              "div",
              { className: "kpi-note" },
              card[2]
            )
          );
        })
      ),

      React.createElement(
        "div",
        { className: "dashboard-grid" },

        React.createElement(
          "div",
          { className: "panel" },

          React.createElement(
            "h3",
            null,
            "Financial Overview"
          ),

          React.createElement(
            "div",
            { className: "panel-subtitle" },
            "Your combined financial picture will appear here."
          ),

          React.createElement(
            "div",
            { className: "chart-placeholder" },
            "Financial chart will be connected to real data."
          )
        ),

        React.createElement(
          "div",
          { className: "panel ai-panel" },

          React.createElement(
            "div",
            { className: "ai-icon" },
            "AI"
          ),

          React.createElement(
            "h3",
            null,
            "AI Finance Assistant"
          ),

          React.createElement(
            "div",
            { className: "ai-text" },
            "Your AI assistant will eventually analyze your finances, investments, markets and trading activity from one place."
          )
        )
      ),

      React.createElement(
        "div",
        { className: "quick-grid" },

        React.createElement(
          "div",
          {
            className: "quick",
            onClick: function () {
              openMainSection("Finance");
            }
          },

          React.createElement(
            "strong",
            null,
            "Finance"
          ),

          React.createElement(
            "span",
            null,
            "Accounts, transactions and cash flow"
          )
        ),

        React.createElement(
          "div",
          {
            className: "quick",
            onClick: function () {
              openMainSection("Wealth");
            }
          },

          React.createElement(
            "strong",
            null,
            "Wealth"
          ),

          React.createElement(
            "span",
            null,
            "Assets, liabilities and net worth"
          )
        ),

        React.createElement(
          "div",
          {
            className: "quick",
            onClick: function () {
              openMainSection("Investments");
            }
          },

          React.createElement(
            "strong",
            null,
            "Investments"
          ),

          React.createElement(
            "span",
            null,
            "Portfolio and investments"
          )
        ),

        React.createElement(
          "div",
          {
            className: "quick",
            onClick: function () {
              openMainSection("AI");
            }
          },

          React.createElement(
            "strong",
            null,
            "AI"
          ),

          React.createElement(
            "span",
            null,
            "AI financial assistant"
          )
        )
      )
    );
  }

  // =====================================================
  // SECTION OVERVIEW PAGE
  // =====================================================

  function renderSectionOverview(sectionName) {
    const iconMap = {
      Finance: "💰",
      Wealth: "💎",
      Investments: "📊",
      Trading: "📈",
      AI: "🤖"
    };

    return React.createElement(
      React.Fragment,
      null,

      React.createElement(
        "div",
        { className: "page-heading" },

        React.createElement(
          "h2",
          null,
          sectionOverviewTitles[sectionName]
        ),

        React.createElement(
          "p",
          null,
          sectionDescriptions[sectionName]
        )
      ),

      React.createElement(
        "div",
        { className: "module-card" },

        React.createElement(
          "div",
          { className: "module-icon" },
          iconMap[sectionName]
        ),

        React.createElement(
          "h3",
          null,
          sectionOverviewTitles[sectionName]
        ),

        React.createElement(
          "p",
          null,
          "This is the main overview for the ",
          sectionName,
          " section. Its dashboard, analytics and real data will be connected here as we build the individual modules."
        )
      )
    );
  }

  // =====================================================
  // ACCOUNTS PAGE
  // =====================================================

  function renderAccounts() {
    const totalBalance = accounts.reduce(
      function (total, account) {
        return total + Number(account.current_balance || 0);
      },
      0
    );

    return React.createElement(
      React.Fragment,
      null,

      // ===================================================
      // ACCOUNTS HEADER
      // ===================================================

      React.createElement(
        "div",
        { className: "accounts-toolbar" },

        React.createElement(
          "div",
          null,

          React.createElement(
            "div",
            { className: "page-heading", style: { marginBottom: 0 } },

            React.createElement(
              "h2",
              null,
              "Accounts"
            ),

            React.createElement(
              "p",
              null,
              "Manage your bank accounts, cash, credit cards and wallets."
            )
          )
        ),

        React.createElement(
          "button",
          {
            className: "add-account-button",
            onClick: function () {
              setAccountsError("");
              setShowAddAccount(function (current) {
                return !current;
              });
            }
          },
          showAddAccount ? "Close" : "+ Add Account"
        )
      ),

      // ===================================================
      // ACCOUNT ERROR
      // ===================================================

      accountsError &&
        React.createElement(
          "div",
          { className: "account-error" },
          accountsError
        ),

      // ===================================================
      // ADD ACCOUNT FORM
      // ===================================================

      showAddAccount &&
        React.createElement(
          "div",
          { className: "account-form-card" },

          React.createElement(
            "h3",
            { className: "account-form-title" },
            "Add Account"
          ),

          React.createElement(
            "div",
            { className: "account-form-grid" },

            React.createElement(
              "div",
              { className: "account-field" },

              React.createElement(
                "label",
                null,
                "Account Name *"
              ),

              React.createElement("input", {
                type: "text",
                placeholder: "e.g. HDFC Salary Account",
                value: accountForm.name,
                onChange: function (event) {
                  updateAccountForm("name", event.target.value);
                }
              })
            ),

            React.createElement(
              "div",
              { className: "account-field" },

              React.createElement(
                "label",
                null,
                "Account Type *"
              ),

              React.createElement(
                "select",
                {
                  value: accountForm.account_type,
                  onChange: function (event) {
                    updateAccountForm(
                      "account_type",
                      event.target.value
                    );
                  }
                },

                React.createElement(
                  "option",
                  { value: "bank" },
                  "Bank Account"
                ),

                React.createElement(
                  "option",
                  { value: "cash" },
                  "Cash"
                ),

                React.createElement(
                  "option",
                  { value: "credit_card" },
                  "Credit Card"
                ),

                React.createElement(
                  "option",
                  { value: "wallet" },
                  "Wallet"
                )
              )
            ),

            React.createElement(
              "div",
              { className: "account-field" },

              React.createElement(
                "label",
                null,
                "Institution"
              ),

              React.createElement("input", {
                type: "text",
                placeholder: "e.g. HDFC Bank",
                value: accountForm.institution,
                onChange: function (event) {
                  updateAccountForm(
                    "institution",
                    event.target.value
                  );
                }
              })
            ),

            React.createElement(
              "div",
              { className: "account-field" },

              React.createElement(
                "label",
                null,
                "Account Number"
              ),

              React.createElement("input", {
                type: "text",
                placeholder: "Optional",
                value: accountForm.account_number,
                onChange: function (event) {
                  updateAccountForm(
                    "account_number",
                    event.target.value
                  );
                }
              })
            ),

            React.createElement(
              "div",
              { className: "account-field" },

              React.createElement(
                "label",
                null,
                "Currency"
              ),

              React.createElement(
                "select",
                {
                  value: accountForm.currency,
                  onChange: function (event) {
                    updateAccountForm(
                      "currency",
                      event.target.value
                    );
                  }
                },

                React.createElement(
                  "option",
                  { value: "INR" },
                  "INR — Indian Rupee"
                ),

                React.createElement(
                  "option",
                  { value: "USD" },
                  "USD — US Dollar"
                ),

                React.createElement(
                  "option",
                  { value: "EUR" },
                  "EUR — Euro"
                ),

                React.createElement(
                  "option",
                  { value: "GBP" },
                  "GBP — British Pound"
                )
              )
            ),

            React.createElement(
              "div",
              { className: "account-field" },

              React.createElement(
                "label",
                null,
                "Opening Balance"
              ),

              React.createElement("input", {
                type: "number",
                step: "0.01",
                placeholder: "0.00",
                value: accountForm.opening_balance,
                onChange: function (event) {
                  updateAccountForm(
                    "opening_balance",
                    event.target.value
                  );
                }
              })
            )
          ),

          React.createElement(
            "div",
            { className: "account-form-actions" },

            React.createElement(
              "button",
              {
                className: "account-cancel-button",
                disabled: accountSaving,
                onClick: function () {
                  resetAccountForm();
                  setShowAddAccount(false);
                }
              },
              "Cancel"
            ),

            React.createElement(
              "button",
              {
                className: "account-save-button",
                disabled: accountSaving,
                onClick: createAccount
              },
              accountSaving ? "Saving..." : "Save Account"
            )
          )
        ),

      // ===================================================
      // ACCOUNT SUMMARY
      // ===================================================

      React.createElement(
        "div",
        { className: "accounts-summary" },

        React.createElement(
          "div",
          { className: "summary-card" },

          React.createElement(
            "div",
            { className: "summary-label" },
            "Total Accounts"
          ),

          React.createElement(
            "div",
            { className: "summary-value" },
            accounts.length
          )
        ),

        React.createElement(
          "div",
          { className: "summary-card" },

          React.createElement(
            "div",
            { className: "summary-label" },
            "Total Balance"
          ),

          React.createElement(
            "div",
            { className: "summary-value" },
            formatMoney(totalBalance, "INR")
          )
        ),

        React.createElement(
          "div",
          { className: "summary-card" },

          React.createElement(
            "div",
            { className: "summary-label" },
            "Status"
          ),

          React.createElement(
            "div",
            { className: "summary-value" },
            accountsLoading ? "Loading..." : "Connected"
          )
        )
      ),

      // ===================================================
      // ACCOUNT LIST
      // ===================================================

      React.createElement(
        "div",
        { className: "accounts-list" },

        accountsLoading
          ? React.createElement(
              "div",
              { className: "account-empty" },
              "Loading accounts..."
            )

          : accounts.length === 0
          ? React.createElement(
              "div",
              { className: "account-empty" },

              React.createElement(
                "strong",
                null,
                "No active accounts yet."
              ),

              React.createElement(
                "div",
                { style: { marginTop: "8px" } },
                "Use + Add Account above to create your first account."
              )
            )

          : accounts.map(function (account) {
              return React.createElement(
                "div",
                {
                  className: "account-card",
                  key: account.id
                },

                React.createElement(
                  "div",
                  { className: "account-name" },
                  account.name
                ),

                React.createElement(
                  "div",
                  { className: "account-type" },
                  accountTypeLabel(account.account_type)
                ),

                React.createElement(
                  "div",
                  { className: "account-balance" },
                  formatMoney(
                    account.current_balance,
                    account.currency
                  )
                ),

                React.createElement(
                  "div",
                  { className: "account-meta" },

                  account.institution
                    ? `Institution: ${account.institution}`
                    : "Institution: —",

                  React.createElement("br"),

                  account.account_number
                    ? `Account: ${account.account_number}`
                    : "Account: —"
                )
              );
            })
      )
    );
  }

   // =====================================================
// CATEGORIES PAGE
// FINANCE CATEGORY MANAGEMENT
// =====================================================

function renderCategories() {
  return React.createElement(
    React.Fragment,
    null,

    // ===================================================
    // PAGE HEADER
    // ===================================================

    React.createElement(
      "div",
      {
        className: "page-heading",
        style: {
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "16px",
          flexWrap: "wrap"
        }
      },

      React.createElement(
        "div",
        null,

        React.createElement("h2", null, "Categories"),

        React.createElement(
          "p",
          null,
          "Organize your income and expense categories."
        )
      ),

      React.createElement(
        "button",
        {
          type: "button",
          onClick: openAddCategoryForm,
          style: {
            border: "none",
            borderRadius: "12px",
            padding: "11px 18px",
            background: "#6d4aff",
            color: "#ffffff",
            fontWeight: "700",
            cursor: "pointer"
          }
        },
        "+ Add Category"
      )
    ),

    // ===================================================
    // SUMMARY CARDS
    // ===================================================

    React.createElement(
      "div",
      {
        style: {
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "14px",
          marginBottom: "18px"
        }
      },

      React.createElement(
        "div",
        { className: "module-card", style: { margin: 0 } },
        React.createElement("strong", null, "Total Categories"),
        React.createElement(
          "div",
          { style: { fontSize: "25px", fontWeight: "800", marginTop: "8px" } },
          categories.length
        )
      ),

      React.createElement(
        "div",
        { className: "module-card", style: { margin: 0 } },
        React.createElement("strong", null, "Income Categories"),
        React.createElement(
          "div",
          { style: { fontSize: "25px", fontWeight: "800", marginTop: "8px" } },
          categories.filter(function (category) {
            return String(category.category_type || "").toLowerCase() === "income";
          }).length
        )
      ),

      React.createElement(
        "div",
        { className: "module-card", style: { margin: 0 } },
        React.createElement("strong", null, "Expense Categories"),
        React.createElement(
          "div",
          { style: { fontSize: "25px", fontWeight: "800", marginTop: "8px" } },
          categories.filter(function (category) {
            return String(category.category_type || "").toLowerCase() === "expense";
          }).length
        )
      )
    ),

    // ===================================================
    // ERROR
    // ===================================================

    categoriesError
      ? React.createElement(
          "div",
          {
            style: {
              background: "#fff1f1",
              color: "#b42318",
              border: "1px solid #ffd0d0",
              borderRadius: "12px",
              padding: "12px 14px",
              marginBottom: "16px"
            }
          },
          categoriesError
        )
      : null,

    // ===================================================
    // CATEGORY LIST
    // ===================================================

    React.createElement(
      "div",
      { className: "module-card" },

      React.createElement(
        "div",
        {
          style: {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "15px"
          }
        },
        React.createElement("h3", { style: { margin: 0 } }, "All Categories"),
        categoriesLoading
          ? React.createElement(
              "span",
              { style: { fontSize: "13px", color: "#777" } },
              "Loading..."
            )
          : null
      ),

      categories.length === 0 && !categoriesLoading
        ? React.createElement(
            "div",
            {
              style: {
                textAlign: "center",
                padding: "35px 15px",
                color: "#777"
              }
            },
            React.createElement(
              "div",
              { style: { fontSize: "42px", marginBottom: "10px" } },
              "📂"
            ),
            React.createElement(
              "h3",
              { style: { margin: "0 0 8px" } },
              "No categories yet"
            ),
            React.createElement(
              "p",
              { style: { margin: 0 } },
              "Create your first income or expense category."
            )
          )
        : React.createElement(
            "div",
            { style: { display: "grid", gap: "10px" } },
            categories.map(function (category) {
              const type = String(category.category_type || "other").toLowerCase();
              const typeLabel =
                type === "income" ? "Income" :
                type === "expense" ? "Expense" : "Other";

              return React.createElement(
                "div",
                {
                  key: category.id,
                  style: {
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: "12px",
                    padding: "15px",
                    border: "1px solid #ece8f5",
                    borderRadius: "14px",
                    background: "#ffffff",
                    flexWrap: "wrap"
                  }
                },

                React.createElement(
                  "div",
                  { style: { flex: "1 1 220px", minWidth: 0 } },
                  React.createElement(
                    "div",
                    { style: { fontWeight: "700", marginBottom: "5px" } },
                    category.name || "Unnamed Category"
                  ),
                  category.description
                    ? React.createElement(
                        "div",
                        { style: { fontSize: "13px", color: "#777" } },
                        category.description
                      )
                    : null
                ),

                React.createElement(
                  "span",
                  {
                    style: {
                      padding: "6px 10px",
                      borderRadius: "999px",
                      fontSize: "12px",
                      fontWeight: "700",
                      background:
                        type === "income" ? "#eaf8ef" :
                        type === "expense" ? "#fff0f0" : "#f1eff8",
                      color:
                        type === "income" ? "#16803c" :
                        type === "expense" ? "#c62828" : "#625b7a"
                    }
                  },
                  typeLabel
                ),

                React.createElement(
                  "div",
                  { style: { display: "flex", gap: "8px" } },

                  React.createElement(
                    "button",
                    {
                      type: "button",
                      onClick: function () {
                        openEditCategoryForm(category);
                      },
                      style: {
                        border: "1px solid #ddd7eb",
                        background: "#ffffff",
                        color: "#4f46a5",
                        borderRadius: "9px",
                        padding: "7px 12px",
                        cursor: "pointer",
                        fontWeight: "700"
                      }
                    },
                    "Edit"
                  ),

                  React.createElement(
                    "button",
                    {
                      type: "button",
                      onClick: function () {
                        setCategoryToDelete(category);
                      },
                      style: {
                        border: "1px solid #ffd0d0",
                        background: "#fff5f5",
                        color: "#c62828",
                        borderRadius: "9px",
                        padding: "7px 12px",
                        cursor: "pointer",
                        fontWeight: "700"
                      }
                    },
                    "Delete"
                  )
                )
              );
            })
          )
    ),

    // ===================================================
    // ADD / EDIT CATEGORY MODAL
    // ===================================================

    showCategoryForm
      ? React.createElement(
          "div",
          {
            style: {
              position: "fixed",
              inset: 0,
              background: "rgba(20, 16, 40, 0.45)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "20px",
              zIndex: 9999
            }
          },

          React.createElement(
            "div",
            {
              style: {
                width: "100%",
                maxWidth: "520px",
                maxHeight: "90vh",
                overflowY: "auto",
                background: "#ffffff",
                borderRadius: "18px",
                padding: "22px",
                boxShadow: "0 20px 60px rgba(0,0,0,0.18)"
              }
            },

            React.createElement(
              "div",
              {
                style: {
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "20px"
                }
              },
              React.createElement(
                "h3",
                { style: { margin: 0 } },
                editingCategory ? "Edit Category" : "Add Category"
              ),
              React.createElement(
                "button",
                {
                  type: "button",
                  onClick: closeCategoryForm,
                  disabled: categorySaving,
                  style: {
                    border: "none",
                    background: "#f2eff8",
                    borderRadius: "10px",
                    width: "36px",
                    height: "36px",
                    cursor: "pointer",
                    fontSize: "20px"
                  }
                },
                "×"
              )
            ),

            React.createElement("label", { style: { display: "block", marginBottom: "6px", fontWeight: "700" } }, "Category Name"),
            React.createElement("input", {
              type: "text",
              value: categoryForm.name,
              onChange: function (event) {
                setCategoryForm(function (current) {
                  return { ...current, name: event.target.value };
                });
              },
              placeholder: "e.g. Groceries",
              style: {
                width: "100%",
                padding: "12px",
                border: "1px solid #ddd7eb",
                borderRadius: "10px",
                marginBottom: "16px",
                fontSize: "15px"
              }
            }),

            React.createElement("label", { style: { display: "block", marginBottom: "6px", fontWeight: "700" } }, "Category Type"),
            React.createElement(
              "select",
              {
                value: categoryForm.category_type,
                onChange: function (event) {
                  setCategoryForm(function (current) {
                    return { ...current, category_type: event.target.value };
                  });
                },
                style: {
                  width: "100%",
                  padding: "12px",
                  border: "1px solid #ddd7eb",
                  borderRadius: "10px",
                  marginBottom: "16px",
                  fontSize: "15px",
                  background: "#ffffff"
                }
              },
              React.createElement("option", { value: "expense" }, "Expense"),
              React.createElement("option", { value: "income" }, "Income"),
              React.createElement("option", { value: "other" }, "Other")
            ),

            React.createElement("label", { style: { display: "block", marginBottom: "6px", fontWeight: "700" } }, "Parent Category"),
            React.createElement(
              "select",
              {
                value: categoryForm.parent_id,
                onChange: function (event) {
                  setCategoryForm(function (current) {
                    return { ...current, parent_id: event.target.value };
                  });
                },
                style: {
                  width: "100%",
                  padding: "12px",
                  border: "1px solid #ddd7eb",
                  borderRadius: "10px",
                  marginBottom: "16px",
                  fontSize: "15px",
                  background: "#ffffff"
                }
              },
              React.createElement("option", { value: "" }, "No Parent Category"),
              categories
                .filter(function (category) {
                  return !(editingCategory && category.id === editingCategory.id);
                })
                .map(function (category) {
                  return React.createElement(
                    "option",
                    { key: category.id, value: String(category.id) },
                    category.name
                  );
                })
            ),

            React.createElement("label", { style: { display: "block", marginBottom: "6px", fontWeight: "700" } }, "Description"),
            React.createElement("textarea", {
              value: categoryForm.description,
              onChange: function (event) {
                setCategoryForm(function (current) {
                  return { ...current, description: event.target.value };
                });
              },
              placeholder: "Optional description",
              rows: 4,
              style: {
                width: "100%",
                padding: "12px",
                border: "1px solid #ddd7eb",
                borderRadius: "10px",
                marginBottom: "20px",
                fontSize: "15px",
                resize: "vertical"
              }
            }),

            categoriesError
              ? React.createElement(
                  "div",
                  {
                    style: {
                      background: "#fff1f1",
                      color: "#b42318",
                      border: "1px solid #ffd0d0",
                      borderRadius: "10px",
                      padding: "10px 12px",
                      marginBottom: "16px"
                    }
                  },
                  categoriesError
                )
              : null,

            React.createElement(
              "div",
              {
                style: {
                  display: "flex",
                  justifyContent: "flex-end",
                  gap: "10px",
                  flexWrap: "wrap"
                }
              },
              React.createElement(
                "button",
                {
                  type: "button",
                  onClick: closeCategoryForm,
                  disabled: categorySaving,
                  style: {
                    border: "1px solid #ddd7eb",
                    background: "#ffffff",
                    borderRadius: "10px",
                    padding: "11px 18px",
                    cursor: "pointer",
                    fontWeight: "700"
                  }
                },
                "Cancel"
              ),
              React.createElement(
                "button",
                {
                  type: "button",
                  onClick: saveCategory,
                  disabled: categorySaving,
                  style: {
                    border: "none",
                    background: "#6d4aff",
                    color: "#ffffff",
                    borderRadius: "10px",
                    padding: "11px 20px",
                    cursor: "pointer",
                    fontWeight: "700"
                  }
                },
                categorySaving
                  ? "Saving..."
                  : editingCategory
                  ? "Update Category"
                  : "Create Category"
              )
            )
          )
        )
      : null,

    // ===================================================
    // DELETE CONFIRMATION
    // ===================================================

    categoryToDelete
      ? React.createElement(
          "div",
          {
            style: {
              position: "fixed",
              inset: 0,
              background: "rgba(20, 16, 40, 0.45)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "20px",
              zIndex: 10000
            }
          },
          React.createElement(
            "div",
            {
              style: {
                width: "100%",
                maxWidth: "420px",
                background: "#ffffff",
                borderRadius: "18px",
                padding: "22px",
                boxShadow: "0 20px 60px rgba(0,0,0,0.18)"
              }
            },
            React.createElement("h3", { style: { marginTop: 0 } }, "Delete Category?"),
            React.createElement(
              "p",
              { style: { color: "#666", lineHeight: "1.5" } },
              `Are you sure you want to delete "${categoryToDelete.name}"?`
            ),
            React.createElement(
              "div",
              { style: { display: "flex", justifyContent: "flex-end", gap: "10px" } },
              React.createElement(
                "button",
                {
                  type: "button",
                  onClick: function () {
                    if (!categoryDeleting) setCategoryToDelete(null);
                  },
                  disabled: categoryDeleting,
                  style: {
                    border: "1px solid #ddd7eb",
                    background: "#ffffff",
                    borderRadius: "10px",
                    padding: "11px 18px",
                    cursor: "pointer",
                    fontWeight: "700"
                  }
                },
                "Cancel"
              ),
              React.createElement(
                "button",
                {
                  type: "button",
                  onClick: function () {
                    deleteCategory(categoryToDelete.id);
                  },
                  disabled: categoryDeleting,
                  style: {
                    border: "none",
                    background: "#d92d20",
                    color: "#ffffff",
                    borderRadius: "10px",
                    padding: "11px 18px",
                    cursor: "pointer",
                    fontWeight: "700"
                  }
                },
                categoryDeleting ? "Deleting..." : "Delete Category"
              )
            )
          )
        )
      : null
  );
}

// =====================================================
  // =====================================================
  // TRANSACTIONS PAGE
  // FULL CRUD + SEARCH + FILTERS
  // =====================================================

  function renderTransactions() {
    // ---------------------------------------------------
    // TRANSACTION TYPE GROUPS
    // These determine how the dashboard totals are shown.
    // ---------------------------------------------------
    const incomeTypes = ["income", "refund", "interest", "dividend"];
    const expenseTypes = ["expense", "withdrawal", "tax", "loan_repayment"];

    // ---------------------------------------------------
    // FILTER TRANSACTIONS
    // ---------------------------------------------------
    const searchValue = transactionSearch.trim().toLowerCase();

    const filteredTransactions = transactions.filter(function (transaction) {
      const type = String(transaction.transaction_type || "").toLowerCase();

      const account = accounts.find(function (item) {
        return Number(item.id) === Number(transaction.account_id);
      });

      const category = categories.find(function (item) {
        return Number(item.id) === Number(transaction.category_id);
      });

      const accountName = account ? String(account.name || "") : "";
      const categoryName = category ? String(category.name || "") : "";

      const searchableText = [
        transaction.description,
        transaction.merchant,
        transaction.reference_number,
        transaction.notes,
        accountName,
        categoryName,
        type
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      const matchesSearch =
        searchValue === "" || searchableText.includes(searchValue);

      const matchesType =
        transactionTypeFilter === "all" ||
        type === transactionTypeFilter;

      const matchesAccount =
        transactionAccountFilter === "all" ||
        String(transaction.account_id) === String(transactionAccountFilter);

      return matchesSearch && matchesType && matchesAccount;
    });

    // ---------------------------------------------------
    // SUMMARY TOTALS
    // ---------------------------------------------------
    const totalIncome = transactions.reduce(function (total, transaction) {
      const type = String(transaction.transaction_type || "").toLowerCase();
      return incomeTypes.includes(type)
        ? total + Number(transaction.amount || 0)
        : total;
    }, 0);

    const totalExpense = transactions.reduce(function (total, transaction) {
      const type = String(transaction.transaction_type || "").toLowerCase();
      return expenseTypes.includes(type)
        ? total + Number(transaction.amount || 0)
        : total;
    }, 0);

    const netCashFlow = totalIncome - totalExpense;

    // ---------------------------------------------------
    // HELPER: ACCOUNT NAME
    // ---------------------------------------------------
    function getTransactionAccountName(transaction) {
      const account = accounts.find(function (item) {
        return Number(item.id) === Number(transaction.account_id);
      });

      return account ? account.name : "Unknown account";
    }

    // ---------------------------------------------------
    // HELPER: CATEGORY NAME
    // ---------------------------------------------------
    function getTransactionCategoryName(transaction) {
      const category = categories.find(function (item) {
        return Number(item.id) === Number(transaction.category_id);
      });

      return category ? category.name : "Uncategorized";
    }

    // ---------------------------------------------------
    // HELPER: TRANSACTION COLOR
    // ---------------------------------------------------
    function getTransactionColor(type) {
      if (incomeTypes.includes(String(type || "").toLowerCase())) {
        return "#16803c";
      }

      if (expenseTypes.includes(String(type || "").toLowerCase())) {
        return "#c62828";
      }

      return "#625b7a";
    }

    // ---------------------------------------------------
    // FORM FIELD FACTORY
    // Keeps the modal consistent and mobile-friendly.
    // ---------------------------------------------------
    function fieldStyle() {
      return {
        width: "100%",
        boxSizing: "border-box",
        border: "1px solid #dedbe8",
        borderRadius: "10px",
        padding: "11px 12px",
        fontSize: "14px",
        background: "#ffffff",
        color: "#222222",
        outline: "none"
      };
    }

    return React.createElement(
      React.Fragment,
      null,

      // =================================================
      // PAGE HEADER
      // =================================================
      React.createElement(
        "div",
        {
          className: "page-heading",
          style: {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "16px",
            flexWrap: "wrap"
          }
        },

        React.createElement(
          "div",
          null,
          React.createElement("h2", null, "Transactions"),
          React.createElement(
            "p",
            null,
            "View and manage your financial transactions."
          )
        ),

        React.createElement(
          "button",
          {
            type: "button",
            onClick: openNewTransactionForm,
            style: {
              border: "none",
              borderRadius: "12px",
              padding: "11px 18px",
              background: "#6d4aff",
              color: "#ffffff",
              fontWeight: "700",
              cursor: "pointer"
            }
          },
          "+ Add Transaction"
        )
      ),

      // =================================================
      // ERROR MESSAGE
      // =================================================
      transactionsError
        ? React.createElement(
            "div",
            {
              style: {
                background: "#fff1f1",
                color: "#b42318",
                border: "1px solid #ffd0d0",
                borderRadius: "12px",
                padding: "12px 14px",
                marginBottom: "16px"
              }
            },
            transactionsError
          )
        : null,

      // =================================================
      // SUMMARY CARDS
      // =================================================
      React.createElement(
        "div",
        {
          style: {
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
            gap: "14px",
            marginBottom: "18px"
          }
        },

        React.createElement(
          "div",
          { className: "module-card", style: { margin: 0 } },
          React.createElement(
            "div",
            { style: { fontSize: "13px", color: "#777" } },
            "Total Transactions"
          ),
          React.createElement(
            "div",
            { style: { fontSize: "25px", fontWeight: "800", marginTop: "7px" } },
            transactions.length
          )
        ),

        React.createElement(
          "div",
          { className: "module-card", style: { margin: 0 } },
          React.createElement(
            "div",
            { style: { fontSize: "13px", color: "#777" } },
            "Income"
          ),
          React.createElement(
            "div",
            {
              style: {
                fontSize: "22px",
                fontWeight: "800",
                marginTop: "7px",
                color: "#16803c"
              }
            },
            formatMoney(totalIncome, "INR")
          )
        ),

        React.createElement(
          "div",
          { className: "module-card", style: { margin: 0 } },
          React.createElement(
            "div",
            { style: { fontSize: "13px", color: "#777" } },
            "Expenses"
          ),
          React.createElement(
            "div",
            {
              style: {
                fontSize: "22px",
                fontWeight: "800",
                marginTop: "7px",
                color: "#c62828"
              }
            },
            formatMoney(totalExpense, "INR")
          )
        ),

        React.createElement(
          "div",
          { className: "module-card", style: { margin: 0 } },
          React.createElement(
            "div",
            { style: { fontSize: "13px", color: "#777" } },
            "Net Cash Flow"
          ),
          React.createElement(
            "div",
            {
              style: {
                fontSize: "22px",
                fontWeight: "800",
                marginTop: "7px",
                color: netCashFlow >= 0 ? "#16803c" : "#c62828"
              }
            },
            formatMoney(netCashFlow, "INR")
          )
        )
      ),

      // =================================================
      // SEARCH + FILTERS
      // =================================================
      React.createElement(
        "div",
        {
          className: "module-card",
          style: {
            marginBottom: "18px"
          }
        },

        React.createElement(
          "div",
          {
            style: {
              display: "grid",
              gridTemplateColumns: "minmax(220px, 2fr) repeat(2, minmax(160px, 1fr))",
              gap: "12px"
            }
          },

          React.createElement("input", {
            type: "search",
            value: transactionSearch,
            onChange: function (event) {
              setTransactionSearch(event.target.value);
            },
            placeholder: "Search transactions...",
            style: fieldStyle()
          }),

          React.createElement(
            "select",
            {
              value: transactionTypeFilter,
              onChange: function (event) {
                setTransactionTypeFilter(event.target.value);
              },
              style: fieldStyle()
            },
            React.createElement("option", { value: "all" }, "All Types"),
            React.createElement("option", { value: "income" }, "Income"),
            React.createElement("option", { value: "expense" }, "Expense"),
            React.createElement("option", { value: "transfer" }, "Transfer"),
            React.createElement("option", { value: "investment" }, "Investment"),
            React.createElement("option", { value: "withdrawal" }, "Withdrawal"),
            React.createElement("option", { value: "refund" }, "Refund"),
            React.createElement("option", { value: "interest" }, "Interest"),
            React.createElement("option", { value: "dividend" }, "Dividend"),
            React.createElement("option", { value: "tax" }, "Tax"),
            React.createElement("option", { value: "loan_repayment" }, "Loan Repayment"),
            React.createElement("option", { value: "other" }, "Other")
          ),

          React.createElement(
            "select",
            {
              value: transactionAccountFilter,
              onChange: function (event) {
                setTransactionAccountFilter(event.target.value);
              },
              style: fieldStyle()
            },
            React.createElement("option", { value: "all" }, "All Accounts"),
            accounts.map(function (account) {
              return React.createElement(
                "option",
                { key: account.id, value: String(account.id) },
                account.name
              );
            })
          )
        )
      ),

      // =================================================
      // TRANSACTION LIST
      // =================================================
      React.createElement(
        "div",
        { className: "module-card", style: { padding: 0, overflow: "hidden" } },

        React.createElement(
          "div",
          {
            style: {
              padding: "18px 20px",
              borderBottom: "1px solid #eeeaf5",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: "10px",
              flexWrap: "wrap"
            }
          },
          React.createElement("h3", { style: { margin: 0 } }, "All Transactions"),
          React.createElement(
            "span",
            { style: { fontSize: "13px", color: "#777" } },
            transactionsLoading
              ? "Loading..."
              : `${filteredTransactions.length} shown`
          )
        ),

        transactionsLoading
          ? React.createElement(
              "div",
              { style: { padding: "40px 20px", textAlign: "center", color: "#777" } },
              "Loading transactions..."
            )
          : filteredTransactions.length === 0
          ? React.createElement(
              "div",
              { style: { padding: "45px 20px", textAlign: "center", color: "#777" } },
              React.createElement(
                "div",
                { style: { fontSize: "42px", marginBottom: "10px" } },
                "💳"
              ),
              React.createElement(
                "h3",
                { style: { margin: "0 0 8px", color: "#222" } },
                transactions.length === 0 ? "No transactions yet" : "No matching transactions"
              ),
              React.createElement(
                "p",
                { style: { margin: 0 } },
                transactions.length === 0
                  ? "Create your first transaction to start tracking your cash flow."
                  : "Try changing the search or filters."
              )
            )
          : React.createElement(
              "div",
              { style: { overflowX: "auto" } },
              React.createElement(
                "div",
                {
                  style: {
                    minWidth: "850px"
                  }
                },

                React.createElement(
                  "div",
                  {
                    style: {
                      display: "grid",
                      gridTemplateColumns: "110px minmax(180px, 1.5fr) minmax(130px, 1fr) minmax(120px, 1fr) 130px 150px",
                      gap: "10px",
                      padding: "12px 20px",
                      background: "#faf9fd",
                      borderBottom: "1px solid #eeeaf5",
                      fontSize: "12px",
                      fontWeight: "800",
                      color: "#777"
                    }
                  },
                  React.createElement("div", null, "DATE"),
                  React.createElement("div", null, "DESCRIPTION"),
                  React.createElement("div", null, "ACCOUNT"),
                  React.createElement("div", null, "CATEGORY"),
                  React.createElement("div", null, "TYPE"),
                  React.createElement("div", null, "AMOUNT / ACTIONS")
                ),

                filteredTransactions.map(function (transaction) {
                  const type = String(transaction.transaction_type || "other").toLowerCase();
                  const amount = Number(transaction.amount || 0);
                  const isIncome = incomeTypes.includes(type);

                  return React.createElement(
                    "div",
                    {
                      key: transaction.id,
                      style: {
                        display: "grid",
                        gridTemplateColumns: "110px minmax(180px, 1.5fr) minmax(130px, 1fr) minmax(120px, 1fr) 130px 150px",
                        gap: "10px",
                        padding: "15px 20px",
                        borderBottom: "1px solid #f0edf6",
                        alignItems: "center"
                      }
                    },

                    React.createElement(
                      "div",
                      { style: { fontSize: "13px", color: "#555" } },
                      transaction.transaction_date
                        ? String(transaction.transaction_date).slice(0, 10)
                        : "—"
                    ),

                    React.createElement(
                      "div",
                      null,
                      React.createElement(
                        "div",
                        { style: { fontWeight: "700", color: "#222" } },
                        transaction.description || transaction.merchant || "Untitled transaction"
                      ),
                      transaction.merchant && transaction.description
                        ? React.createElement(
                            "div",
                            { style: { fontSize: "12px", color: "#888", marginTop: "3px" } },
                            transaction.merchant
                          )
                        : null,
                      transaction.reference_number
                        ? React.createElement(
                            "div",
                            { style: { fontSize: "11px", color: "#999", marginTop: "3px" } },
                            `Ref: ${transaction.reference_number}`
                          )
                        : null
                    ),

                    React.createElement(
                      "div",
                      { style: { fontSize: "13px", color: "#555" } },
                      getTransactionAccountName(transaction)
                    ),

                    React.createElement(
                      "div",
                      { style: { fontSize: "13px", color: "#555" } },
                      getTransactionCategoryName(transaction)
                    ),

                    React.createElement(
                      "span",
                      {
                        style: {
                          display: "inline-flex",
                          width: "fit-content",
                          padding: "5px 9px",
                          borderRadius: "999px",
                          background:
                            incomeTypes.includes(type)
                              ? "#eaf8ef"
                              : expenseTypes.includes(type)
                              ? "#fff0f0"
                              : "#f1eff8",
                          color: getTransactionColor(type),
                          fontSize: "11px",
                          fontWeight: "800"
                        }
                      },
                      transactionTypeLabel(type)
                    ),

                    React.createElement(
                      "div",
                      null,
                      React.createElement(
                        "div",
                        {
                          style: {
                            fontWeight: "800",
                            color: getTransactionColor(type),
                            marginBottom: "6px"
                          }
                        },
                        `${isIncome ? "+" : expenseTypes.includes(type) ? "-" : ""}${formatMoney(amount, transaction.currency || "INR")}`
                      ),

                      React.createElement(
                        "div",
                        { style: { display: "flex", gap: "6px" } },
                        React.createElement(
                          "button",
                          {
                            type: "button",
                            onClick: function () {
                              openEditTransactionForm(transaction);
                            },
                            style: {
                              border: "1px solid #ddd7ee",
                              background: "#ffffff",
                              color: "#5b43c6",
                              borderRadius: "8px",
                              padding: "5px 8px",
                              fontSize: "11px",
                              fontWeight: "700",
                              cursor: "pointer"
                            }
                          },
                          "Edit"
                        ),
                        React.createElement(
                          "button",
                          {
                            type: "button",
                            onClick: function () {
                              setTransactionToDelete(transaction);
                              setTransactionsError("");
                            },
                            style: {
                              border: "1px solid #f1cccc",
                              background: "#fff7f7",
                              color: "#c62828",
                              borderRadius: "8px",
                              padding: "5px 8px",
                              fontSize: "11px",
                              fontWeight: "700",
                              cursor: "pointer"
                            }
                          },
                          "Delete"
                        )
                      )
                    )
                  );
                })
              )
            )
      ),

      // =================================================
      // ADD / EDIT TRANSACTION MODAL
      // =================================================
      showTransactionForm
        ? React.createElement(
            "div",
            {
              style: {
                position: "fixed",
                inset: 0,
                zIndex: 3000,
                background: "rgba(20, 15, 35, 0.45)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                padding: "18px"
              },
              onClick: function (event) {
                if (event.target === event.currentTarget) {
                  closeTransactionForm();
                }
              }
            },

            React.createElement(
              "div",
              {
                style: {
                  width: "min(720px, 100%)",
                  maxHeight: "92vh",
                  overflowY: "auto",
                  background: "#ffffff",
                  borderRadius: "16px",
                  boxShadow: "0 20px 70px rgba(0,0,0,0.25)",
                  padding: "20px"
                }
              },

              React.createElement(
                "div",
                {
                  style: {
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "18px"
                  }
                },
                React.createElement(
                  "div",
                  null,
                  React.createElement(
                    "h3",
                    { style: { margin: 0 } },
                    editingTransaction ? "Edit Transaction" : "Add Transaction"
                  ),
                  React.createElement(
                    "p",
                    { style: { margin: "5px 0 0", fontSize: "13px", color: "#777" } },
                    editingTransaction
                      ? "Update the transaction details."
                      : "Record income, expense, transfer or investment activity."
                  )
                ),
                React.createElement(
                  "button",
                  {
                    type: "button",
                    onClick: closeTransactionForm,
                    disabled: transactionSaving,
                    style: {
                      border: "none",
                      background: "#f2eff8",
                      borderRadius: "9px",
                      width: "34px",
                      height: "34px",
                      cursor: transactionSaving ? "not-allowed" : "pointer",
                      fontSize: "18px"
                    }
                  },
                  "×"
                )
              ),

              transactionsError
                ? React.createElement(
                    "div",
                    {
                      style: {
                        background: "#fff1f1",
                        color: "#b42318",
                        border: "1px solid #ffd0d0",
                        borderRadius: "10px",
                        padding: "10px 12px",
                        marginBottom: "14px",
                        fontSize: "13px"
                      }
                    },
                    transactionsError
                  )
                : null,

              React.createElement(
                "div",
                {
                  style: {
                    display: "grid",
                    gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                    gap: "14px"
                  }
                },

                React.createElement(
                  "label",
                  { style: { display: "grid", gap: "6px" } },
                  React.createElement("span", { style: { fontSize: "12px", fontWeight: "800" } }, "Account *"),
                  React.createElement(
                    "select",
                    {
                      value: transactionForm.account_id,
                      onChange: function (event) {
                        updateTransactionForm("account_id", event.target.value);
                      },
                      style: fieldStyle()
                    },
                    React.createElement("option", { value: "" }, "Select account"),
                    accounts.map(function (account) {
                      return React.createElement(
                        "option",
                        { key: account.id, value: String(account.id) },
                        `${account.name} — ${formatMoney(account.current_balance, account.currency || "INR")}`
                      );
                    })
                  )
                ),

                React.createElement(
                  "label",
                  { style: { display: "grid", gap: "6px" } },
                  React.createElement("span", { style: { fontSize: "12px", fontWeight: "800" } }, "Transaction Type *"),
                  React.createElement(
                    "select",
                    {
                      value: transactionForm.transaction_type,
                      onChange: function (event) {
                        updateTransactionForm("transaction_type", event.target.value);

                        // Clear an incompatible category when switching type.
                        const nextType = event.target.value;
                        if (nextType === "income" || nextType === "expense") {
                          const selectedCategory = categories.find(function (category) {
                            return String(category.id) === String(transactionForm.category_id);
                          });

                          if (
                            selectedCategory &&
                            String(selectedCategory.category_type || "").toLowerCase() !== nextType
                          ) {
                            updateTransactionForm("category_id", "");
                          }
                        }
                      },
                      style: fieldStyle()
                    },
                    React.createElement("option", { value: "expense" }, "Expense"),
                    React.createElement("option", { value: "income" }, "Income"),
                    React.createElement("option", { value: "transfer" }, "Transfer"),
                    React.createElement("option", { value: "investment" }, "Investment"),
                    React.createElement("option", { value: "withdrawal" }, "Withdrawal"),
                    React.createElement("option", { value: "refund" }, "Refund"),
                    React.createElement("option", { value: "interest" }, "Interest"),
                    React.createElement("option", { value: "dividend" }, "Dividend"),
                    React.createElement("option", { value: "tax" }, "Tax"),
                    React.createElement("option", { value: "loan_repayment" }, "Loan Repayment"),
                    React.createElement("option", { value: "other" }, "Other")
                  )
                ),

                React.createElement(
                  "label",
                  { style: { display: "grid", gap: "6px" } },
                  React.createElement("span", { style: { fontSize: "12px", fontWeight: "800" } }, "Amount *"),
                  React.createElement("input", {
                    type: "number",
                    min: "0",
                    step: "0.01",
                    value: transactionForm.amount,
                    onChange: function (event) {
                      updateTransactionForm("amount", event.target.value);
                    },
                    placeholder: "0.00",
                    style: fieldStyle()
                  })
                ),

                React.createElement(
                  "label",
                  { style: { display: "grid", gap: "6px" } },
                  React.createElement("span", { style: { fontSize: "12px", fontWeight: "800" } }, "Currency"),
                  React.createElement("input", {
                    type: "text",
                    value: transactionForm.currency,
                    onChange: function (event) {
                      updateTransactionForm("currency", event.target.value.toUpperCase());
                    },
                    style: fieldStyle()
                  })
                ),

                React.createElement(
                  "label",
                  { style: { display: "grid", gap: "6px" } },
                  React.createElement("span", { style: { fontSize: "12px", fontWeight: "800" } }, "Category"),
                  React.createElement(
                    "select",
                    {
                      value: transactionForm.category_id,
                      onChange: function (event) {
                        updateTransactionForm("category_id", event.target.value);
                      },
                      style: fieldStyle()
                    },
                    React.createElement("option", { value: "" }, "No Category"),
                    categories
                      .filter(function (category) {
                        const categoryType = String(category.category_type || "").toLowerCase();
                        const transactionType = String(transactionForm.transaction_type || "").toLowerCase();

                        if (transactionType === "income") {
                          return categoryType === "income" || categoryType === "other";
                        }

                        if (transactionType === "expense") {
                          return categoryType === "expense" || categoryType === "other";
                        }

                        return true;
                      })
                      .map(function (category) {
                        return React.createElement(
                          "option",
                          { key: category.id, value: String(category.id) },
                          `${category.name}${category.category_type ? ` (${transactionTypeLabel(category.category_type)})` : ""}`
                        );
                      })
                  )
                ),

                React.createElement(
                  "label",
                  { style: { display: "grid", gap: "6px" } },
                  React.createElement("span", { style: { fontSize: "12px", fontWeight: "800" } }, "Transaction Date *"),
                  React.createElement("input", {
                    type: "date",
                    value: transactionForm.transaction_date,
                    onChange: function (event) {
                      updateTransactionForm("transaction_date", event.target.value);
                    },
                    style: fieldStyle()
                  })
                ),

                React.createElement(
                  "label",
                  { style: { display: "grid", gap: "6px" } },
                  React.createElement("span", { style: { fontSize: "12px", fontWeight: "800" } }, "Description"),
                  React.createElement("input", {
                    type: "text",
                    value: transactionForm.description,
                    onChange: function (event) {
                      updateTransactionForm("description", event.target.value);
                    },
                    placeholder: "e.g. Grocery purchase",
                    style: fieldStyle()
                  })
                ),

                React.createElement(
                  "label",
                  { style: { display: "grid", gap: "6px" } },
                  React.createElement("span", { style: { fontSize: "12px", fontWeight: "800" } }, "Merchant"),
                  React.createElement("input", {
                    type: "text",
                    value: transactionForm.merchant,
                    onChange: function (event) {
                      updateTransactionForm("merchant", event.target.value);
                    },
                    placeholder: "e.g. DMart",
                    style: fieldStyle()
                  })
                ),

                React.createElement(
                  "label",
                  { style: { display: "grid", gap: "6px", gridColumn: "1 / -1" } },
                  React.createElement("span", { style: { fontSize: "12px", fontWeight: "800" } }, "Reference Number"),
                  React.createElement("input", {
                    type: "text",
                    value: transactionForm.reference_number,
                    onChange: function (event) {
                      updateTransactionForm("reference_number", event.target.value);
                    },
                    placeholder: "Optional bank reference / UTR",
                    style: fieldStyle()
                  })
                ),

                React.createElement(
                  "label",
                  { style: { display: "grid", gap: "6px", gridColumn: "1 / -1" } },
                  React.createElement("span", { style: { fontSize: "12px", fontWeight: "800" } }, "Notes"),
                  React.createElement("textarea", {
                    rows: 3,
                    value: transactionForm.notes,
                    onChange: function (event) {
                      updateTransactionForm("notes", event.target.value);
                    },
                    placeholder: "Optional notes",
                    style: Object.assign({}, fieldStyle(), { resize: "vertical" })
                  })
                )
              ),

              React.createElement(
                "div",
                {
                  style: {
                    display: "flex",
                    justifyContent: "flex-end",
                    gap: "10px",
                    marginTop: "20px",
                    flexWrap: "wrap"
                  }
                },
                React.createElement(
                  "button",
                  {
                    type: "button",
                    onClick: closeTransactionForm,
                    disabled: transactionSaving,
                    style: {
                      border: "1px solid #ddd7ee",
                      background: "#ffffff",
                      color: "#444",
                      borderRadius: "10px",
                      padding: "10px 16px",
                      fontWeight: "700",
                      cursor: transactionSaving ? "not-allowed" : "pointer"
                    }
                  },
                  "Cancel"
                ),
                React.createElement(
                  "button",
                  {
                    type: "button",
                    onClick: saveTransaction,
                    disabled: transactionSaving,
                    style: {
                      border: "none",
                      background: "#6d4aff",
                      color: "#ffffff",
                      borderRadius: "10px",
                      padding: "10px 18px",
                      fontWeight: "800",
                      cursor: transactionSaving ? "not-allowed" : "pointer"
                    }
                  },
                  transactionSaving
                    ? "Saving..."
                    : editingTransaction
                    ? "Save Changes"
                    : "Create Transaction"
                )
              )
            )
          )
        : null,

      // =================================================
      // DELETE CONFIRMATION MODAL
      // =================================================
      transactionToDelete
        ? React.createElement(
            "div",
            {
              style: {
                position: "fixed",
                inset: 0,
                zIndex: 3100,
                background: "rgba(20, 15, 35, 0.45)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                padding: "18px"
              },
              onClick: function (event) {
                if (event.target === event.currentTarget && !transactionDeleting) {
                  setTransactionToDelete(null);
                }
              }
            },

            React.createElement(
              "div",
              {
                style: {
                  width: "min(430px, 100%)",
                  background: "#ffffff",
                  borderRadius: "16px",
                  padding: "22px",
                  boxShadow: "0 20px 70px rgba(0,0,0,0.25)"
                }
              },

              React.createElement(
                "h3",
                { style: { margin: "0 0 8px" } },
                "Delete Transaction?"
              ),

              React.createElement(
                "p",
                { style: { color: "#666", lineHeight: "1.5", margin: "0 0 18px" } },
                `This will remove transaction #${transactionToDelete.id} from the active transaction list. Continue?`
              ),

              React.createElement(
                "div",
                { style: { display: "flex", justifyContent: "flex-end", gap: "10px" } },
                React.createElement(
                  "button",
                  {
                    type: "button",
                    onClick: function () {
                      if (!transactionDeleting) {
                        setTransactionToDelete(null);
                      }
                    },
                    disabled: transactionDeleting,
                    style: {
                      border: "1px solid #ddd7ee",
                      background: "#ffffff",
                      borderRadius: "10px",
                      padding: "10px 15px",
                      fontWeight: "700",
                      cursor: transactionDeleting ? "not-allowed" : "pointer"
                    }
                  },
                  "Cancel"
                ),
                React.createElement(
                  "button",
                  {
                    type: "button",
                    onClick: function () {
                      deleteTransaction(transactionToDelete.id);
                    },
                    disabled: transactionDeleting,
                    style: {
                      border: "none",
                      background: "#c62828",
                      color: "#ffffff",
                      borderRadius: "10px",
                      padding: "10px 15px",
                      fontWeight: "800",
                      cursor: transactionDeleting ? "not-allowed" : "pointer"
                    }
                  },
                  transactionDeleting ? "Deleting..." : "Delete Transaction"
                )
              )
            )
          )
        : null
    );
  }

  // =====================================================
  // GENERIC MODULE PAGE
  // =====================================================
  // =====================================================

  function renderModulePage() {
    let icon = "📁";

    if (
      active === "Transactions" ||
      active === "Accounts" ||
      active === "Budget" ||
      active === "Cash Flow" ||
      active === "Categories"
    ) {
      icon = "💰";
    }

    if (
      active === "Assets" ||
      active === "Liabilities" ||
      active === "Net Worth" ||
      active === "Insurance" ||
      active === "Real Estate"
    ) {
      icon = "💎";
    }

    if (
      active === "Portfolio" ||
      active === "Stocks" ||
      active === "Mutual Funds" ||
      active === "ETFs" ||
      active === "Bonds" ||
      active === "Gold" ||
      active === "Crypto"
    ) {
      icon = "📊";
    }

    if (
      active === "Markets" ||
      active === "Watchlist" ||
      active === "Screener" ||
      active === "Charts" ||
      active === "Strategies" ||
      active === "Backtesting" ||
      active === "Paper Trading" ||
      active === "Live Trading" ||
      active === "Positions" ||
      active === "Orders"
    ) {
      icon = "📈";
    }

    if (
      active === "AI Chat" ||
      active === "AI Research" ||
      active === "AI Analysis" ||
      active === "AI Predictions" ||
      active === "AI Reports"
    ) {
      icon = "🤖";
    }

    return React.createElement(
      React.Fragment,
      null,

      React.createElement(
        "div",
        { className: "page-heading" },

        React.createElement(
          "h2",
          null,
          active
        ),

        React.createElement(
          "p",
          null,
          getPageDescription()
        )
      ),

      React.createElement(
        "div",
        { className: "module-card" },

        React.createElement(
          "div",
          { className: "module-icon" },
          icon
        ),

        React.createElement(
          "h3",
          null,
          active
        ),

        React.createElement(
          "p",
          null,
          "This module is part of the Finance OS architecture and will be connected to its full functionality without affecting the other modules."
        )
      )
    );
  }

  // =====================================================
  // PAGE ROUTER
  // =====================================================

  function renderPage() {
    // Global overview
    if (active === "Overview") {
      return renderOverview();
    }

    // Main section overview
    if (
      active === "Finance" ||
      active === "Wealth" ||
      active === "Investments" ||
      active === "Trading" ||
      active === "AI"
    ) {
      return renderSectionOverview(active);
    }

// =====================================================
// EXISTING ACCOUNTS PAGE
// =====================================================

if (active === "Accounts") {
  return renderAccounts();
}

// =====================================================
// CATEGORIES PAGE
// =====================================================

if (active === "Categories") {
  return renderCategories();
}

// =====================================================
// TRANSACTIONS PAGE
// =====================================================

if (active === "Transactions") {
  return renderTransactions();
}

// =====================================================
// EVERYTHING ELSE FOR NOW
// =====================================================

return renderModulePage();
  }

  // =====================================================
  // MOBILE QUICK NAVIGATION
  // =====================================================

  const mobileShortcuts = [
    ["Overview", "🏠"],
    ["Finance", "💰"],
    ["Investments", "📊"],
    ["Trading", "📈"],
    ["AI", "🤖"]
  ];

  // =====================================================
  // MAIN RETURN
  // =====================================================

  return React.createElement(
    React.Fragment,
    null,

    // ===================================================
    // GLOBAL STYLES
    // ===================================================

    React.createElement(
      "style",
      null,
      styles
    ),

    // ===================================================
    // MOBILE DRAWER
    // ===================================================

    menuOpen &&
      React.createElement(
        React.Fragment,
        null,

        React.createElement("div", {
          className: "drawer-overlay",

          onClick: function () {
            setMenuOpen(false);
          }
        }),

        React.createElement(
          "aside",
          { className: "drawer" },

          React.createElement(
            "div",
            { className: "drawer-head" },

            React.createElement(
              "div",
              { className: "drawer-brand" },

              "AI ",

              React.createElement(
                "span",
                {
                  style: {
                    color: "#7048ff"
                  }
                },
                "Finance"
              )
            ),

            React.createElement(
              "button",
              {
                className: "drawer-close",

                onClick: function () {
                  setMenuOpen(false);
                }
              },
              "×"
            )
          ),

          renderMobileNavigation()
        )
      ),

    // ===================================================
    // APPLICATION
    // ===================================================

    React.createElement(
      "div",
      { className: "finance-app" },

      // =================================================
      // DESKTOP SIDEBAR
      // =================================================

      React.createElement(
        "aside",
        { className: "finance-sidebar" },

        React.createElement(
          "div",
          { className: "brand" },

          "AI ",

          React.createElement(
            "span",
            null,
            "Finance"
          )
        ),

        renderDesktopNavigation()
      ),

      // =================================================
      // MAIN CONTENT
      // =================================================

      React.createElement(
        "main",
        { className: "finance-main" },

        // ===============================================
        // TOP BAR
        // ===============================================

        React.createElement(
          "header",
          { className: "topbar" },

          React.createElement(
            "div",
            { className: "top-left" },

            React.createElement(
              "button",
              {
                className: "mobile-menu",

                onClick: function () {
                  setMenuOpen(true);
                }
              },
              "☰"
            ),

            React.createElement(
              "div",
              { className: "top-title" },

              React.createElement(
                "small",
                null,
                "AI Finance Trading OS"
              ),

              React.createElement(
                "strong",
                null,
                getPageTitle()
              )
            )
          ),

          React.createElement(
            "div",
            { className: "profile" },
            "N"
          )
        ),

        // ===============================================
        // PAGE CONTENT
        // ===============================================

        React.createElement(
          "section",
          { className: "page" },
          renderPage()
        )
      )
    ),

    // ===================================================
    // MOBILE BOTTOM NAV
    // ===================================================

    React.createElement(
      "nav",
      { className: "mobile-bottom" },

      mobileShortcuts.map(function (item) {
        return React.createElement(
          "button",
          {
            key: item[0],

            className:
              active === item[0] ||
              findParentSection(active) === item[0]
                ? "bottom-item active"
                : "bottom-item",

            onClick: function () {
              openMainSection(item[0]);
            }
          },

          React.createElement(
            "span",
            { className: "bottom-icon" },
            item[1]
          ),

          item[0]
        );
      })
    )
  );
}

export default App;
