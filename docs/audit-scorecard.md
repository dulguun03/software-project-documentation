# Bhatti code sample quality audit

Local self-audit, 1–5 stars. Scope: the complete runnable project, including shared client and assets.
These scores are review judgments, not an independent peer grade or production verification.

| Sample | Explained | Concise | Clear | Usable | Trustworthy | Mean |
|---|---:|---:|---:|---:|---:|---:|
| upload_photo.py | 5 | 4 | 5 | 5 | 4 | 4.6 |
| translate_bark.py | 5 | 4 | 5 | 5 | 4 | 4.6 |
| subscribe_webhook.py | 5 | 5 | 5 | 5 | 4 | 4.8 |
| assistant_workflow.py | 5 | 4 | 5 | 5 | 4 | 4.6 |
| client.py (supporting transport) | 4 | 4 | 5 | 5 | 4 | 4.4 |

Total 115/125 = 92%, mean 4.60/5.00. Mandatory Corg.ly subset: 70/75 = 93.33%, mean 4.67/5.00.

Explained: each executable sample starts with purpose and prerequisites. The shared client has
a module description; full setup lives in README. Concise: multipart construction is centralized,
but standard-library encoding adds unavoidable transport boilerplate. Clear: descriptive names,
explicit paths and HTTP timeouts. Usable: every sample ran with included assets and no Python
package installation. No generic foo/bar payloads; callback uses an explicitly illustrative domain.

Trustworthy: HTTP status and JSON were captured from the running local mock in
`evidence/sample-responses.json`. The webhook returned 201. No production Corg.ly endpoint,
real bark interpretation, callback delivery, Google OAuth or Google writes were tested.
Trustworthy is therefore 4/5, and “live payload” means a real response from the local mock.

Refactoring decisions: declare the sandbox base URL and token in one place; locate assets relative
to script files; let Python set the multipart boundary header correctly; add request timeouts;
fail on HTTP errors; print the actual returned payload rather than a manually composed response.

The original Chad source code was not supplied. These are replacement samples for the three
specified endpoints, not a claimed line-by-line audit of unseen legacy code. Embedded Redoc
samples reuse these same source files. No duplicate code sample is counted twice.

Principle names and page references come from the Sprint 05 handout: Explained p.87,
Concise p.90, Clear p.92, Usable p.93, Trustworthy p.94. The complete textbook was not supplied.
