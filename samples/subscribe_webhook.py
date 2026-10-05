"""Register an illustrative HTTPS callback for pet activity notifications.
The sandbox records the subscription but never sends outbound callbacks.
"""
from client import post

subscription = {
    "pet_id": "corgi_98231",
    "callback_url": "https://example.org/corgly/pet-activity",
    "events": ["pet.activity.detected"],
}
post("/webhooks/subscribe", subscription)
