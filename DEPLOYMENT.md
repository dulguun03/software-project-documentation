# Deployment status and instructions

No repository or hosting account was supplied. No public URL or remote commit is claimed.
The generated `public/` directory includes bundled Swagger assets and standalone Redoc pages.

## Recommended: docs and sandbox together

Use a Python/container host with an HTTPS reverse proxy. Upload this project and run
`python server.py --host 0.0.0.0 --port 8080`, or build the included Dockerfile.
Set the host's HTTP port to 8080. Run the service as an unprivileged process behind the host's
HTTPS endpoint. This is a disposable lab demo with a public token and in-memory state;
use only synthetic data and restart it to reset the state.

If the provider assigns a base URL, append `/swagger/`, `/redoc.html`, and `/corgly-redoc.html`.
The OpenAPI `/v1` server uses the same origin, so no cross-origin setup is required.
Verify Authorize and each request through Swagger, including the 201 webhook response.
Record the actual assigned URLs and deployment date in `evidence/public-deployment.md`.
Do not treat these path suffixes as already deployed URLs.

## GitHub repository and CI

Create or choose your course repository, add the contents of this folder at its root,
and commit the files. The included CI validates both YAML specs, executes all four samples,
and builds both renderers. A workflow file is provided; no GitHub run has occurred here.
Preserve `package-lock.json` so the same tool versions are installed in CI.

## Optional: GitHub Pages for reading only

In repository Settings > Pages, choose GitHub Actions. Run the manual
“Publish documentation to GitHub Pages” workflow. Its output provides the real Pages URL.
Pages serves files only: it cannot execute the Python sandbox. With the supplied `/v1`
server, Try-It-Out will fail on Pages. Thus Pages alone does not satisfy the full lab rubric.
For a functional public sandbox, prefer the same-origin service described above. If splitting
hosts, replace OpenAPI server URLs with the real HTTPS API origin, rebuild docs, and implement
an explicit CORS policy before claiming completion.

## Publication acceptance check

- Both public renderer URLs load from another browser/session.
- Swagger authorization plus POST /commands returns HTTP 200.
- Confirm then execute returns a simulated resource ID; an unconfirmed action returns 409.
- Corg.ly photo, audio, and subscription return 200, 200, and 201.
- Redoc displays navigation, schemas, examples and search results.
- Save screenshots and actual URLs. Link the successful CI run and repository commit.

Current status: local checks completed; public deployment, remote commit and hosted CI pending.
