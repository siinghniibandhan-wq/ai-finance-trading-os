"""Pure rules for deciding whether a tax-report section is complete.

No web or database imports, so these can be tested on their own.
A section is complete only when the owner has confirmed it AND nothing
is still waiting for review. The app never decides this by itself.
"""

REVIEW_SECTIONS = ("tds_advance_tax", "deductions_exemptions")


def section_status(confirmed, pending_count):
    """Return (is_complete, plain-language reason)."""
    pending = int(pending_count or 0)
    if pending > 0:
        noun = "entry is" if pending == 1 else "entries are"
        return False, f"{pending} {noun} still waiting for review. Verify or delete them."
    if not confirmed:
        return False, "Confirm that you have entered everything for this section."
    return True, "Confirmed by you, with nothing waiting for review."
