from pathlib import Path


DECISION_PACKET = Path("docs/carbon-promotion-decision-packet.md")
CUTOVER_GUIDE = Path("docs/carbon-promotion-cutover-guide.md")


def test_promotion_decision_packet_links_required_evidence_sources():
    content = DECISION_PACKET.read_text(encoding="utf-8")

    for reference in {
        "carbon-handoff-parity.md",
        "carbon-real-workbook-parity-evidence.md",
        "carbon-manual-uat-evidence-index.md",
        "carbon-uat-session-worksheet.md",
        "carbon-accessibility-uat-results-template.md",
        "carbon-hosted-operations-readiness.md",
        "carbon-operations-runbook.md",
        "carbon-promotion-cutover-guide.md",
    }:
        assert reference in content


def test_promotion_decision_packet_requires_core_gate_answers():
    content = DECISION_PACKET.read_text(encoding="utf-8")

    for gate in {
        "workbook intake, save/load, planning, preflight, preview, and ZIP export",
        "output match Streamlit contracts",
        "without facilitator help",
        "keyboard-only and screen-reader users",
        "hosted health checks, logs, alerts, retention, backup/restore",
        "Streamlit reachable as fallback",
        "blocker/high issues",
    }:
        assert gate in content


def test_promotion_decision_packet_keeps_default_promotion_conservative():
    content = DECISION_PACKET.read_text(encoding="utf-8")

    assert "Streamlit remains the supported production UI and rollback path" in content
    assert "Pilot with Streamlit fallback" in content
    assert "Is Carbon approved as the default UI? | No" in content
    assert "/Users/" not in content


def test_cutover_guide_links_decision_packet():
    content = CUTOVER_GUIDE.read_text(encoding="utf-8")

    assert "Carbon Promotion Decision Packet" in content
    assert "carbon-promotion-decision-packet.md" in content
