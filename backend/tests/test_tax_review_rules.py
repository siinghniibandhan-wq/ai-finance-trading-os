"""A tax section is complete only when confirmed AND nothing is pending."""
from app.tax_review_rules import REVIEW_SECTIONS, section_status


def test_not_confirmed_is_incomplete():
    done, reason = section_status(False, 0)
    assert done is False and "Confirm" in reason


def test_pending_items_block_even_when_confirmed():
    done, reason = section_status(True, 2)
    assert done is False and "2 entries are" in reason


def test_single_pending_wording():
    assert "1 entry is" in section_status(True, 1)[1]


def test_confirmed_with_nothing_pending_is_complete():
    assert section_status(True, 0)[0] is True


def test_none_pending_count_is_treated_as_zero():
    assert section_status(True, None)[0] is True


def test_sections_are_the_two_report_sections():
    assert REVIEW_SECTIONS == ("tds_advance_tax", "deductions_exemptions")
