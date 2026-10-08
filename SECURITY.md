# Security

## Reporting a vulnerability

Report vulnerabilities privately, not in a public issue. Use GitHub's private vulnerability reporting on this repository (Security tab, "Report a vulnerability"), or email deukwoong.woo@a2sys.ai.

Include the tag or commit you installed, the command you ran, and what you observed. Fixes are released as a new tag on `main`.

## Scope

jevfetch fetches any URL it is given, follows redirects, and sends the page text and the question to the TypeSafe API. These are documented behaviors (see "Privacy and security" in README.md), not vulnerabilities. A report is in scope when it shows a way to make jevfetch do something the README does not describe, such as reading a file it did not download or sending data anywhere other than the page's host and the TypeSafe API.
