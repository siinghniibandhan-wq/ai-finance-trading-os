import React, { useState } from "react";
import { API_BASE_URL } from "./api";
import {
  ArrowRight, ArrowUpRight, BarChart3, BrainCircuit, Check, ChevronDown,
  CircleDollarSign, CreditCard, Goal, Menu, ShieldCheck, Sparkles, Wallet,
  X, TrendingUp, PieChart, ReceiptText, Layers3, Moon, Sun
} from "lucide-react";
import "./landing.css";

const plans = [
  { name: "Starter", price: 1999, tagline: "Build better money habits", popular: false, features: ["Accounts and transaction tracking", "Budgets and expense categories", "Investment portfolio tracking", "Financial dashboard", "Core planning tools", "Email support"] },
  { name: "Professional", price: 5999, tagline: "For active money managers", popular: true, features: ["Everything in Starter", "Advanced portfolio analytics", "Financial goals and planning", "Expanded market insights", "All available themes", "AI assistant tools", "Tax organisation tools", "Razorpay payment support"] },
  { name: "Enterprise", price: 9999, tagline: "Deeper insights in one workspace", popular: false, features: ["Everything in Professional", "Advanced financial analytics", "Research Playground access", "Advanced AI financial analysis", "Expanded research tools", "Priority support"] },
];
const features = [
  { icon: Wallet, title: "Money, organised", text: "Bring accounts, transactions, budgets and bills into one clear workspace." },
  { icon: TrendingUp, title: "Invest with context", text: "Track holdings and investment transactions alongside your broader finances." },
  { icon: BrainCircuit, title: "AI financial assistant", text: "Ask questions and explore insights. AI access will be limited to authorised data and your plan." },
  { icon: Goal, title: "Plan what matters", text: "Set goals, follow your progress and make your next financial milestone visible." },
  { icon: BarChart3, title: "See the full picture", text: "Use dashboards and analytics to understand cash flow, savings and portfolio trends." },
  { icon: ReceiptText, title: "Tax-ready organisation", text: "Keep relevant financial information organised to support tax planning." },
];
const themes = ["Default", "Light", "Dark", "Aurora", "Emerald", "Ocean", "Sunset", "Minimal", "Retro Terminal", "Glass"];
const faqs = [
  ["What is Financial OS?", "A personal finance workspace designed to bring money management, investments, planning, analytics and AI-assisted insights together."],
  ["Can other users see my financial data?", "The intended platform design gives each account its own private financial environment. User-level access controls must be enforced by the backend before public launch."],
  ["Which billing periods will be available?", "Monthly, half-yearly (6 months) and annual (12 months) billing are planned. Half-yearly and annual prices will be displayed once finalised."],
  ["Can I change the theme?", "Yes. The planned Appearance settings include the current Default theme, Light, Dark and seven additional styles. Theme availability depends on your plan."],
  ["Does the AI give guaranteed investment advice?", "No. AI responses can be incomplete or incorrect and do not guarantee investment outcomes. Always review important decisions independently."],
];

export default function LandingPage() {
  const [billing] = useState("monthly");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [faqOpen, setFaqOpen] = useState(0);
  const [theme, setTheme] = useState("Default");
  const [showAllThemes, setShowAllThemes] = useState(false);
  const [demoMode, setDemoMode] = useState("overview");
  const [isLight, setIsLight] = useState(false);
  const [checkoutPlan, setCheckoutPlan] = useState(null);
  const [customerName, setCustomerName] = useState("");
  const [customerEmail, setCustomerEmail] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [checkoutBusy, setCheckoutBusy] = useState(false);
  const [checkoutMessage, setCheckoutMessage] = useState("");
  const prices = { monthly: [1999, 5999, 9999], halfYearly: [null, null, null], annually: [null, null, null] };
  const billingLabel = billing === "monthly" ? "/ month" : billing === "halfYearly" ? "/ 6 months" : "/ year";
  const displayedThemes = showAllThemes ? themes : themes.slice(0, 5);
  const goApp = () => { window.location.href = "/login"; };
  const goPlans = () => document.getElementById("plans")?.scrollIntoView({ behavior: "smooth" });
  const startCheckout = (plan) => {
    setCheckoutPlan(plan);
    setCheckoutMessage("");
  };
  const ensureRazorpayScript = () => new Promise((resolve, reject) => {
    if (window.Razorpay) return resolve();
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Unable to load secure checkout. Please try again."));
    document.body.appendChild(script);
  });
  const payForPlan = async (event) => {
    event.preventDefault();
    if (!checkoutPlan || checkoutBusy) return;
    setCheckoutBusy(true);
    setCheckoutMessage("");
    try {
      await ensureRazorpayScript();
      const orderResponse = await fetch(`${API_BASE_URL}/api/payments/create-order`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          plan: checkoutPlan.name.toLowerCase(),
          customer_name: customerName.trim(),
          customer_email: customerEmail.trim(),
          customer_phone: customerPhone.trim() || null,
        }),
      });
      const order = await orderResponse.json().catch(() => ({}));
      if (!orderResponse.ok) throw new Error(order.detail || "Could not start payment. Please contact support.");
      const razorpay = new window.Razorpay({
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        name: "Financial OS",
        description: `${checkoutPlan.name} plan`,
        order_id: order.order_id,
        prefill: { name: customerName.trim(), email: customerEmail.trim(), contact: customerPhone.trim() },
        notes: { plan: checkoutPlan.name },
        theme: { color: "#8b5cf6" },
        handler: async (response) => {
          try {
            const verifyResponse = await fetch(`${API_BASE_URL}/api/payments/verify`, {
              method: "POST",
              headers: { "Content-Type": "application/json", Accept: "application/json" },
              body: JSON.stringify({
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
              }),
            });
            const verified = await verifyResponse.json().catch(() => ({}));
            if (!verifyResponse.ok) throw new Error(verified.detail || "Payment verification failed. Contact support before retrying.");
            setCheckoutMessage("Payment verified. Keep your payment ID: " + response.razorpay_payment_id + ". For plan activation, contact support if your workspace is not updated.");
          } catch (error) {
            setCheckoutMessage(error.message || "Payment was submitted but could not be verified. Please contact support with your payment ID.");
          } finally {
            setCheckoutBusy(false);
          }
        },
        modal: { ondismiss: () => setCheckoutBusy(false) },
      });
      razorpay.on("payment.failed", (response) => {
        setCheckoutMessage(response.error?.description || "Payment did not complete. Please try again.");
        setCheckoutBusy(false);
      });
      razorpay.open();
    } catch (error) {
      setCheckoutMessage(error.message || "Unable to start checkout.");
      setCheckoutBusy(false);
    }
  };

  return <div className={`fos-site ${isLight ? "fos-site-light" : ""}`}>
    <header className="fos-nav">
      <a className="fos-brand" href="#top" aria-label="Financial OS home"><span className="fos-brand-mark"><Layers3 size={21}/></span><span>Financial<span className="fos-brand-accent">OS</span><small>YOUR MONEY. ONE WORKSPACE.</small></span></a>
      <nav className={`fos-nav-links ${mobileOpen ? "fos-nav-open" : ""}`}>
        <a href="#features" onClick={() => setMobileOpen(false)}>Features</a><a href="#how-it-works" onClick={() => setMobileOpen(false)}>How it works</a><a href="#themes" onClick={() => setMobileOpen(false)}>Themes</a><a href="#plans" onClick={() => setMobileOpen(false)}>Pricing</a><a href="#faq" onClick={() => setMobileOpen(false)}>FAQ</a>
        <button className="fos-mobile-login" onClick={goApp}>Log in <ArrowRight size={16}/></button>
      </nav>
      <div className="fos-nav-actions"><button className="fos-icon-button" aria-label="Toggle preview appearance" onClick={() => setIsLight(!isLight)}>{isLight ? <Moon size={17}/> : <Sun size={17}/>}</button><button className="fos-login" onClick={goApp}>Log in</button><button className="fos-cta fos-cta-small" onClick={goPlans}>Explore plans <ArrowUpRight size={16}/></button></div>
      <button className="fos-menu" onClick={() => setMobileOpen(!mobileOpen)} aria-label="Toggle navigation">{mobileOpen ? <X/> : <Menu/>}</button>
    </header>

    <main id="top">
      <section className="fos-hero fos-container">
        <div className="fos-hero-copy"><div className="fos-eyebrow"><span className="fos-live-dot"/> YOUR FINANCIAL LIFE, CONNECTED</div><h1>Make your money<br/>make <span>more sense.</span></h1><p className="fos-hero-text">A clearer view of your money, investments and goals—with planning tools and AI-assisted insights in one financial workspace.</p><div className="fos-hero-actions"><button className="fos-cta" onClick={goApp}>Get started <ArrowRight size={18}/></button><button className="fos-secondary" onClick={goPlans}>Compare plans <ArrowUpRight size={17}/></button></div><div className="fos-hero-trust"><span><ShieldCheck size={16}/> Private-by-design architecture</span><span><Sparkles size={16}/> AI-assisted insights</span></div></div>
        <div className="fos-preview-wrap"><div className="fos-preview-glow"/><div className="fos-preview-window"><div className="fos-preview-top"><div className="fos-window-dots"><i/><i/><i/></div><span>FINANCIAL OS <b>/</b> OVERVIEW</span><span className="fos-preview-status">DEMO</span></div><div className="fos-preview-body"><aside className="fos-mini-sidebar"><div className="fos-mini-logo"><Layers3 size={15}/></div>{[Wallet, BarChart3, PieChart, Goal, Sparkles].map((Icon, i) => <span className={i === 0 ? "active" : ""} key={i}><Icon size={15}/></span>)}</aside><div className="fos-mini-content"><div className="fos-mini-heading"><div><small>MONDAY, OCTOBER 12</small><h3>{demoMode === "overview" ? "Your financial overview" : demoMode === "investments" ? "Investment snapshot" : "Spending insights"}</h3></div><span className="fos-mini-avatar">U</span></div><div className="fos-mini-cards"><div><small>Total net worth</small><strong>₹12,45,300</strong><em>↗ 8.4% <span>this year</span></em></div><div><small>Investments</small><strong>₹8,20,450</strong><em>↗ 5.2% <span>this month</span></em></div></div><div className="fos-mini-chart"><div className="fos-mini-chart-head"><span>{demoMode === "spending" ? "Monthly spending" : "Net worth trend"}</span><span>6 MONTHS⌄</span></div><div className="fos-chart-bars">{[33,48,39,60,52,74,62,88,68,96,79,100,83,91].map((h,i)=><i key={i} style={{height:`${h}%`}}/>)}</div><div className="fos-chart-labels"><span>May</span><span>Jun</span><span>Jul</span><span>Aug</span><span>Sep</span><span>Oct</span></div></div><div className="fos-mini-bottom"><div><span>Monthly savings rate</span><strong>28%</strong><div className="fos-progress"><i/></div></div><div><span>Top category</span><strong>Housing <small>32% of spend</small></strong></div></div></div></div><div className="fos-demo-tabs"><button className={demoMode === "overview" ? "selected" : ""} onClick={() => setDemoMode("overview")}>Overview</button><button className={demoMode === "investments" ? "selected" : ""} onClick={() => setDemoMode("investments")}>Investments</button><button className={demoMode === "spending" ? "selected" : ""} onClick={() => setDemoMode("spending")}>Spending</button></div></div><div className="fos-floating-note"><span><Sparkles size={15}/></span><div><strong>One connected picture</strong><small>Money · Investing · Planning</small></div></div></div>
        <div className="fos-hero-footnote">Illustrative sample data shown for demonstration. Not a live account.</div>
      </section>

      <section className="fos-value-strip"><div className="fos-container fos-value-inner"><span>BUILT FOR YOUR WHOLE FINANCIAL PICTURE</span><b><CircleDollarSign/> Money</b><b><TrendingUp/> Invest</b><b><Goal/> Plan</b><b><BrainCircuit/> AI insights</b><b><BarChart3/> Analytics</b></div></section>

      <section className="fos-section fos-container" id="features"><div className="fos-section-head"><div><div className="fos-eyebrow">ONE WORKSPACE, MORE CLARITY</div><h2>Your finances are connected.<br/><span>Your tools should be, too.</span></h2></div><p>Move beyond scattered spreadsheets and disconnected apps. Bring your everyday money, investments and future plans into one view.</p></div><div className="fos-feature-grid">{features.map(({icon:Icon,title,text},i)=><article className="fos-feature-card" key={title}><span className={`fos-feature-icon fos-feature-icon-${i}`}><Icon size={22}/></span><h3>{title}</h3><p>{text}</p><span className="fos-feature-number">0{i+1}</span></article>)}</div></section>

      <section className="fos-how-section" id="how-it-works"><div className="fos-container"><div className="fos-section-head fos-section-head-center"><div><div className="fos-eyebrow">A SIMPLE START</div><h2>From scattered numbers<br/>to <span>a clearer next step.</span></h2></div><p>Start with your own workspace, choose the tools that fit your needs, and build a financial routine that works for you.</p></div><div className="fos-steps"><article><span>01</span><div className="fos-step-icon"><CreditCard/></div><h3>Choose your plan</h3><p>Compare features and select a subscription that suits your financial routine.</p></article><div className="fos-step-line"/><article><span>02</span><div className="fos-step-icon"><Wallet/></div><h3>Bring your finances together</h3><p>Organise accounts, transactions, investments and goals in your workspace.</p></article><div className="fos-step-line"/><article><span>03</span><div className="fos-step-icon"><Sparkles/></div><h3>Learn from your numbers</h3><p>Explore dashboards, planning tools and AI-assisted insights as available in your plan.</p></article></div></div></section>

      <section className="fos-theme-section fos-container" id="themes"><div className="fos-section-head"><div><div className="fos-eyebrow">MAKE IT YOURS</div><h2>Your workspace.<br/><span>Your kind of focus.</span></h2></div><p>Choose a visual style that fits how you like to work. The current Financial OS Default theme stays available alongside the Light theme and other styles.</p></div><div className="fos-theme-layout"><div className={`fos-theme-preview fos-theme-${theme.toLowerCase().replaceAll(" ", "-")}`}><div className="fos-theme-preview-nav"><span className="fos-theme-dot-logo"><Layers3 size={16}/></span><b>Financial OS</b><span className="fos-theme-user">U</span></div><div className="fos-theme-preview-main"><small>YOUR OVERVIEW</small><h3>{theme} theme</h3><p>Everything you need, in your style.</p><div className="fos-theme-stat-row"><div><small>Net worth</small><strong>₹12,45,300</strong></div><div><small>Monthly savings</small><strong>28%</strong></div></div><div className="fos-theme-fake-chart">{[40,52,44,66,57,72,60,88,74,96].map((n,i)=><i key={i} style={{height:`${n}%`}}/>)}</div><div className="fos-theme-lines"><i/><i/><i/></div></div></div><div className="fos-theme-options"><div className="fos-theme-options-head"><div><h3>Choose your look</h3><p>Preview a style</p></div><button onClick={() => setShowAllThemes(!showAllThemes)}>{showAllThemes ? "Show fewer" : "View all 10"} <ArrowRight size={14}/></button></div><div className="fos-theme-list">{displayedThemes.map((t,i)=><button key={t} className={`fos-theme-choice ${theme===t?"chosen":""}`} onClick={()=>setTheme(t)}><span className={`fos-theme-swatch fos-swatch-${t.toLowerCase().replaceAll(" ","-")}`}><i/><i/><i/></span><span><strong>{t}</strong><small>{["Current Financial OS look","Bright and clean","Low-glare focus","Purple-pink gradients","Nature-inspired green","Calm professional blue","Warm gradient accents","Simple and quiet","Terminal-inspired","Translucent surfaces"][i]}</small></span>{theme===t && <Check size={17}/>}</button>)}</div><p className="fos-theme-note">Theme preview only. Your selected theme will be saved in Settings once user accounts and preferences are connected.</p></div></div></section>

      <section className="fos-pricing-section" id="plans"><div className="fos-container"><div className="fos-section-head fos-section-head-center"><div><div className="fos-eyebrow">STRAIGHTFORWARD PLANS</div><h2>Start small. Grow <span>with confidence.</span></h2></div><p>Choose the level of tools that fits you today. You can compare what each plan is intended to include before subscribing.</p></div><div className="fos-billing-switch" role="group" aria-label="Billing period"><button className={billing==="monthly"?"active":""} onClick={()=>setBilling("monthly")}>Monthly</button><button className={billing==="halfYearly"?"active":""} onClick={()=>setBilling("halfYearly")}>Half-yearly <small>6 months</small></button><button className={billing==="annually"?"active":""} onClick={()=>setBilling("annually")}>Annually <small>12 months</small></button></div><div className="fos-plan-grid">{plans.map((plan,i)=><article className={`fos-plan-card ${plan.popular?"fos-plan-popular":""}`} key={plan.name}>{plan.popular&&<div className="fos-popular-label">MOST POPULAR</div>}<div className="fos-plan-top"><span className={`fos-plan-icon fos-plan-icon-${i}`}>{i===0?<Wallet/>:i===1?<TrendingUp/>:<Sparkles/>}</span><h3>{plan.name}</h3><p>{plan.tagline}</p></div><div className="fos-price">{prices[billing][i] ? <><strong>₹{prices[billing][i]}</strong><span>{billingLabel}</span></> : <><strong className="fos-price-tbd">Coming soon</strong><span>{billingLabel}</span></>}</div>{billing!=="monthly"&&<p className="fos-price-note">{billing==="halfYearly"?"6-month billing price to be finalised":"Annual billing price to be finalised"}</p>}<button className={plan.popular?"fos-cta fos-plan-button":"fos-plan-button fos-plan-button-outline"} onClick={() => billing === "monthly" ? startCheckout(plan) : setCheckoutMessage("Only monthly checkout is currently available. Please select Monthly to continue.")}> {billing==="monthly"?`Choose ${plan.name}`:"Monthly checkout only"} <ArrowRight size={16}/></button><div className="fos-plan-divider"/><p className="fos-includes">WHAT'S INCLUDED</p><ul>{plan.features.map(f=><li key={f}><Check size={15}/>{f}</li>)}</ul></article>)}</div><p className="fos-pricing-footnote">Prices shown are monthly plan prices in INR. Half-yearly and annual billing are not available yet. Plan access is subject to confirmation and activation by support.</p></div></section>

      <section className="fos-privacy-section fos-container" id="privacy"><div className="fos-privacy-icon"><ShieldCheck size={27}/></div><div><div className="fos-eyebrow">PRIVACY IS PART OF THE DESIGN</div><h2>Your financial world should stay <span>yours.</span></h2><p>Financial OS is being built around account-level data separation and controlled access. The backend must enforce ownership on every request, and AI should only receive the information needed for an authorised task. Final privacy commitments will reflect the deployed implementation and provider terms.</p></div><div className="fos-privacy-points"><span><Check/> Individual user workspaces</span><span><Check/> Controlled AI data access</span><span><Check/> Subscription-based permissions</span></div></section>

      <section className="fos-faq-section fos-container" id="faq"><div className="fos-section-head"><div><div className="fos-eyebrow">GOOD QUESTIONS</div><h2>Know before<br/><span>you get started.</span></h2></div><p>Some capabilities and subscription rules are still being built. We aim to make the details clear before you purchase.</p></div><div className="fos-faq-list">{faqs.map(([q,a],i)=><article className={`fos-faq-item ${faqOpen===i?"open":""}`} key={q}><button onClick={()=>setFaqOpen(faqOpen===i?-1:i)}><span>{q}</span><ChevronDown size={19}/></button>{faqOpen===i&&<p>{a}</p>}</article>)}</div></section>

      <section className="fos-final-cta fos-container"><div className="fos-final-glow"/><div className="fos-eyebrow">YOUR NEXT STEP STARTS HERE</div><h2>Make room for a clearer<br/><span>financial future.</span></h2><p>Bring your money, investments and plans into one connected workspace.</p><button className="fos-cta" onClick={goApp}>Create your account <ArrowRight size={18}/></button><small>Secure checkout is available for monthly plans. Plan activation may require support confirmation.</small></section>
      <section className="fos-contact-section fos-container" id="contact">
        <div className="fos-contact-copy"><div className="fos-eyebrow">WE'RE HERE TO HELP</div><h2>Questions? <span>Talk to us.</span></h2><p>Contact Financial OS support for account, billing, payment, or plan-activation questions.</p></div>
        <div className="fos-contact-actions"><a className="fos-contact-card" href="tel:+917644841104"><strong>Call us</strong><span>+91 76448 41104</span></a><a className="fos-contact-card" href="https://wa.me/917644841104" target="_blank" rel="noreferrer"><strong>WhatsApp</strong><span>Chat with support</span></a></div>
        <p className="fos-company-note">Financial OS is part of KPMC Enterprises.</p>
      </section>
    </main>
    {checkoutPlan && <div className="fos-checkout-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && !checkoutBusy) setCheckoutPlan(null); }}>
      <section className="fos-checkout-modal" role="dialog" aria-modal="true" aria-labelledby="fos-checkout-title">
        <button type="button" className="fos-checkout-close" aria-label="Close checkout" disabled={checkoutBusy} onClick={() => setCheckoutPlan(null)}>×</button>
        <div className="fos-eyebrow">SECURE PAYMENT BY RAZORPAY</div><h2 id="fos-checkout-title">Subscribe to {checkoutPlan.name}</h2>
        <p className="fos-checkout-price">₹{checkoutPlan.price.toLocaleString("en-IN")} <span>/ month</span></p>
        <p className="fos-checkout-note">Pay securely using UPI, credit/debit cards, or net banking. Your payment will be verified by our server.</p>
        <form onSubmit={payForPlan} className="fos-checkout-form">
          <label>Full name<input required maxLength="150" autoComplete="name" value={customerName} onChange={e => setCustomerName(e.target.value)} /></label>
          <label>Email address<input required type="email" maxLength="255" autoComplete="email" value={customerEmail} onChange={e => setCustomerEmail(e.target.value)} /></label>
          <label>Phone number (optional)<input type="tel" maxLength="20" autoComplete="tel" value={customerPhone} onChange={e => setCustomerPhone(e.target.value)} /></label>
          {checkoutMessage && <p className="fos-checkout-message" role="status">{checkoutMessage}</p>}
          <button className="fos-cta fos-checkout-submit" type="submit" disabled={checkoutBusy}>{checkoutBusy ? "Connecting to Razorpay…" : "Continue to payment"} <ArrowRight size={17}/></button>
        </form>
        <small className="fos-checkout-legal">By continuing, you agree to contact support for subscription activation or payment issues. Payments are processed by Razorpay.</small>
      </section>
    </div>}
    <footer className="fos-footer"><div className="fos-container fos-footer-main"><a className="fos-brand" href="#top"><span className="fos-brand-mark"><Layers3 size={20}/></span><span>Financial<span className="fos-brand-accent">OS</span><small>YOUR MONEY. ONE WORKSPACE.</small></span></a><p>One workspace for money management, investing and planning.</p><div className="fos-footer-links"><a href="#features">Features</a><a href="#plans">Pricing</a><a href="#faq">FAQ</a><a href="#privacy">Privacy</a><a href="#contact">Contact</a></div></div><div className="fos-container fos-footer-bottom"><span>© {new Date().getFullYear()} Financial OS. All rights reserved.</span><span>Part of KPMC Enterprises · Illustrative previews only. Not investment advice.</span></div></footer>
  </div>;
}
