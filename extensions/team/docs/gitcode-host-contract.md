# GitCode Host Contract

GitCode is usable through an authenticated repository integration, browser, or
its official `https://api.gitcode.com/api/v5` REST API.

Before remote access:

1. accept only HTTPS `gitcode.com` targets for the current repository;
2. prefer an integration or authenticated browser;
3. load API credentials only from the configured secret environment variable;
   never paste, persist, print, or place them in a logged command/URL;
4. read the Issue or PR and verify owner, repository, number, and canonical URL;
5. distinguish read, create, comment, label, and review capabilities.

GitCode documents query-string tokens for some endpoints. Do not use that form
unless the transport guarantees redaction. Fall back to an integration,
browser, or `output-only`.

After every write, read the resource back and verify its repository, number,
state, canonical URL, and changed content. Report `published` only after this
check. Otherwise emit the complete paste-ready content, missing condition, and
unchecked remote facts. Consult the current official OpenAPI request shape
before each write.
