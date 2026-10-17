# Razorpay setup for Financial OS

The public pricing page uses Razorpay Checkout for monthly plan payments. The backend creates fixed-amount orders and verifies the Razorpay payment signature; the Razorpay secret is never sent to the browser.

## Required backend environment variables

Set these on the backend hosting service (not in frontend environment variables):

- `RAZORPAY_KEY_ID` — Razorpay API key ID.
- `RAZORPAY_KEY_SECRET` — corresponding API key secret.

Use Razorpay **Test Mode** keys first. Complete a successful test payment, verify that `POST /api/payments/verify` returns `verified: true`, and only then replace them with live-mode keys after the Razorpay account is activated for live payments.

The frontend uses the existing `VITE_API_BASE_URL` setting (or the API URL currently configured in `frontend/src/api.js`) to call the backend.

## Current plan prices

- Starter: ₹1,999 per month
- Professional: ₹5,999 per month
- Enterprise: ₹9,999 per month

The backend independently fixes these amounts; it does not trust an amount submitted by the browser.

## Important operational note

Successful payments are recorded in the `payment_orders` database table. This integration verifies and records payment, but does not automatically grant application entitlements or create recurring Razorpay subscriptions. Until subscription entitlement/renewal handling is implemented, support may need to activate the plan after confirming the payment. Do not advertise annual/half-yearly billing as available.

Contact details shown on the public website:
- Phone: +91 76448 41104
- WhatsApp: https://wa.me/917644841104
- Company: Financial OS is part of KPMC Enterprises.
