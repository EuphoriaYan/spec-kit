# GitCode Host Contract

GitCode is a supported host when an authenticated repository integration,
browser session, or API transport is available. Its official REST API uses the
base URL `https://api.gitcode.com/api/v5` and exposes Issue, Issue comment,
Pull Request, PR comment, file, label, and review operations.

## Capability Probe

Before a remote read or write:

1. Confirm the target URL is HTTPS on `gitcode.com` and resolves to the current
   repository. Reject lookalike, loopback, link-local, private-network, and
   metadata hosts.
2. Prefer an authenticated repository integration or the user's existing
   authenticated browser session.
3. For direct API access, obtain the credential from the configured secret
   environment variable. Never request that it be pasted into chat, store it in
   repository files, print it, or place it in a command line or logged URL.
4. Perform a read-only request for the target Issue or PR. Continue only when
   the returned owner, repository, number, and HTML URL match the request.
5. Declare the available operations separately: read, create, comment, label,
   and review. Read access does not imply write access.

The official API documents access tokens as a query parameter for several
repository endpoints. A transport that cannot keep query strings out of logs
must not use that form. Use an integration/browser, a verified redacting
transport, or `output-only` instead.

## Verified Write

After creating or updating an Issue, PR, label, comment, or review, read the
resource back and verify its number, repository, state, title/body hash where
applicable, and canonical `https://gitcode.com/...` URL. Only then report
`published`. A timeout, ambiguous response, failed read-back, or missing URL is
`blocked` or `output-only`, never success.

The documented repository endpoints include:

- `GET /repos/{owner}/{repo}/issues/{number}`;
- `POST /repos/{owner}/issues` with the repository supplied as documented;
- `GET /repos/{owner}/{repo}/pulls/{number}`;
- `POST /repos/{owner}/{repo}/pulls`;
- the corresponding Issue/PR comment, label, file, and review endpoints.

Consult the current official GitCode OpenAPI documentation before sending a
write because request shapes can change independently of this extension.

## Deterministic Fallback

When the capability probe fails, emit the complete title/body/comment and its
exact destination under the appropriate `Paste Into ...` heading. Record which
condition is missing and which remote facts were not checked. Manual posting is
a transport step; it does not weaken any approval or review gate.
