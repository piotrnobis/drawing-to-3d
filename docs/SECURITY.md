# Security

This is both a real concern and a graded side challenge ("most secure build", Aikido). Keep the repo clean from the start; retrofitting security is painful mid-hackathon.

## Threat model

### 1. Executing model-generated code (the big one)
The pipeline runs **CadQuery code produced by an LLM**. That is **arbitrary code execution**. It is the single most important risk in this project.

**Rule:** generated code runs **only** through the sandboxed runner, never via `exec`/`eval` in the app process. The runner must:
- run in a **separate subprocess**,
- enforce a **hard timeout**,
- use a **clean environment** that does **not** inherit `GEMINI_API_KEY` or any other secret,
- write only to a **scratch temp directory**,
- have **no network access** where feasible (a container is the stronger option; note it if not used).

### 2. Secrets
- API keys live in `.env` only. `.env` is git-ignored. `.env.example` lists variable names with no values.
- Never hardcode, print, or log keys. If a key is ever committed, **rotate it immediately** (revoke in AI Studio, issue a new one).

### 3. Untrusted uploads
- Validate uploaded drawings: allowed image types only, enforced **max file size**, reject malformed input early.
- Inline image payloads to Gemini are capped (≈20 MB per request); enforce before sending.

### 4. Web surface (once the API/UI exist)
- **CORS** restricted to localhost in dev, not `*`.
- Sensible security headers.
- No secrets or internal paths in error responses.

### 5. Dependencies
- **Pin everything** and commit lockfiles.
- Keep the dependency set **minimal**; every package is attack surface and a potential finding.
- Avoid unmaintained packages.

## Aikido side challenge — how to submit

1. Create a free Aikido account.
2. Connect our Git provider (GitHub).
3. Connect this repository.
4. Let it scan; address findings (the items above should keep it clean).
5. **Screenshot the security report** clearly showing the number and categories of issues. That screenshot is the submission artifact.

Do this **before the final hour**, so there is time to fix anything it flags.

## Reporting a concern

Spotted something risky? Flag it in the team channel and add a `# SECURITY:` comment at the relevant line. Don't sit on it.