Financial OS targeted fixes — file locations

1. frontend/src/App.jsx
   - Persists the selected sidebar page in localStorage so refresh restores the same tab.
   - Adds visible Asset Class and Product Type controls to the existing Portfolio investment form.
   - Sends selected asset_class/product_type metadata to the existing investment API and restores those values when editing.
   - Preserves existing app navigation and form fields.

2. frontend/src/main.jsx
   - Adds a React render error boundary so a component crash shows an error message instead of a completely blank page.
   - This is a diagnostic guard; it does not prove the original Account Subscription rendering cause is fixed.

Only replace these two files at the same paths. Keep the rest of the repository unchanged.
