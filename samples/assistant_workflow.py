"""Propose, review-confirm and simulate one Calendar action, then read history.
This fixture is pre-reviewed for the automated demo; a real UI must ask the user.
"""
from client import post

command = {
    "session_id": "session_anu_01",
    "transcript": "Schedule the Sprint 05 review on 6 October at 10 AM.",
    "intent": "calendar.create",
    "event": {"title": "First API experiment", "start": "2026-10-06T10:00:00+08:00",
              "end": "2026-10-06T10:30:00+08:00", "timezone": "Asia/Ulaanbaatar"},
}
proposal = post("/commands", command)
action_id = proposal["action_id"]
confirmation = {"session_id": "session_anu_01", "payload_version": proposal["payload_version"]}
# post(f"/actions/{action_id}/confirm", confirmation)
post(f"/actions/{action_id}/execute", confirmation)
post("/contacts/search", {"query": "Anu"})
post("/sessions/history", {"session_id": "session_anu_01"})
