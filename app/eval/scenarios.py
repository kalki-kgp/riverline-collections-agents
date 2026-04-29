from __future__ import annotations

from app.core.models import BorrowerProfile, BorrowerScenario


def demo_borrower() -> BorrowerProfile:
    return BorrowerProfile(
        borrower_id="borrower_demo_001",
        name="Ravi Kumar",
        phone="+15551230000",
        partial_account_id="8421",
        amount_due_cents=184250,
        days_past_due=73,
    )


def seeded_scenarios() -> list[BorrowerScenario]:
    return [
        BorrowerScenario(
            scenario_id="S01_cooperative_plan",
            behavior="cooperative",
            stated_position="I can pay monthly but cannot clear the full balance today.",
            financial_situation="stable income, limited monthly surplus",
            likely_resolution="payment_plan",
        ),
        BorrowerScenario(
            scenario_id="S02_combative_no_deal",
            behavior="combative",
            stated_position="I dispute the amount and I am not paying today.",
            financial_situation="income available but unwilling to commit",
            likely_resolution="no_deal",
        ),
        BorrowerScenario(
            scenario_id="S03_evasive_settlement",
            behavior="evasive",
            stated_position="Maybe I can settle if there is a meaningful discount.",
            financial_situation="irregular income, possible lump-sum help from family",
            likely_resolution="settlement",
        ),
        BorrowerScenario(
            scenario_id="S04_confused_plan",
            behavior="confused",
            stated_position="I do not understand what happens next but I can pay something.",
            financial_situation="stable income, poor understanding of collections process",
            likely_resolution="payment_plan",
        ),
        BorrowerScenario(
            scenario_id="S05_distressed_hardship",
            behavior="distressed",
            stated_position="I lost my job and had a medical emergency. I cannot handle pressure now.",
            financial_situation="job loss and medical emergency causing financial distress",
            expected_hardship=True,
            likely_resolution="hardship_referral",
        ),
    ]
