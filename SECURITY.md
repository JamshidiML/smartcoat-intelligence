# Security Policy

Version: 1.0 Draft

---

# Purpose

SmartCoat handles sensitive enterprise knowledge.

This includes materials, formulations, suppliers, customers, prices, production history, quality issues, decision records, and intellectual property.

Security must be treated as an architectural responsibility.

---

# Sensitive Information

Do not commit:

- customer confidential data
- supplier confidential data
- raw production data
- formulation secrets
- pricing files
- personal data
- proprietary test reports
- internal emails
- private keys
- API tokens
- passwords
- credentials
- `.env` files
- raw datasets unless explicitly approved

---

# Local Security

Recommended practices:

- use environment variables for secrets
- do not commit `.env`
- do not commit raw customer/company data
- use `.gitignore`
- remove `.DS_Store`
- review `git status` before every commit
- review `git diff --stat` before every commit

---

# Reporting Security Issues

Security issues should be treated as high priority.

Report suspected security issues privately to the repository owner.

Do not open public issues for secrets, vulnerabilities, or confidential data exposure.

---

# Security Rule

Enterprise knowledge is a strategic asset.

Protect it from the beginning.
