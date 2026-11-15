# Link check

Checked: 2026-11-15 08:07 UTC. The check gets each source address and compares the SHA-256 with the ledger.

**Result: 21 of 23 addresses give the same file.**

| Version | Result | Address |
|---|---|---|
| `xai-draft-2025-02-10` | same file | <https://web.archive.org/web/20250210221647id_/https://x.ai/documents/2025.02.10-RMF-Draft.pdf> |
| `xai-draft-2025-02-20` | same file | <https://data.x.ai/2025.02.20-RMF-Draft.pdf> |
| `xai-2025-08-20` | same file | <https://web.archive.org/web/20250821224133id_/https://data.x.ai/2025-08-20-xai-risk-management-framework.pdf> |
| `xai-2025-12-30` | same file | <https://data.x.ai/2025-12-31-xai-frontier-artificial-intelligence-framework.pdf> |
| `xai-2026-06-30` | HTTP 404 | <https://media.x.ai/v1/website/xai-frontier-artificial-intelligence-framework-30-june-2026-99c40684.pdf> |
| `anthropic-v1.0` | same file | <https://www-cdn.anthropic.com/1adf000c8f675958c2ee23805d91aaade1cd4613/responsible-scaling-policy.pdf> |
| `anthropic-v2.0` | same file | <https://www-cdn.anthropic.com/616dee633636e5bd309cb73aed8622e80fe47839.pdf> |
| `anthropic-v2.1` | same file | <https://web.archive.org/web/20250401013032id_/https://www-cdn.anthropic.com/080b003762c270d033dc2ea1153b9df665078da1.pdf> |
| `anthropic-v2.2` | same file | <https://www-cdn.anthropic.com/872c653b2d0501d6ab44cf87f43e1dc4853e4d37.pdf> |
| `anthropic-v3.0` | same file | <https://www-cdn.anthropic.com/e670587677525f28df69b59e5fb4c22cc5461a17.pdf> |
| `anthropic-v3.1` | same file | <https://www-cdn.anthropic.com/files/4zrzovbb/website/bf04581e4f329735fd90634f6a1962c13c0bd351.pdf> |
| `anthropic-v3.2` | same file | <https://cdn.sanity.io/files/4zrzovbb/website/28c6241900d90410628a8a2003a5572faae4365a.pdf> |
| `anthropic-v3.3` | same file | <https://cdn.sanity.io/files/4zrzovbb/website/c11e84981d0a7281a1b229f3fa6af0da66eaf43f.pdf> |
| `anthropic-v3.4` | same file | <https://cdn.sanity.io/files/4zrzovbb/website/0bacdc8440ea96e62a8766d99ebe1d4eea6d5f3a.pdf> |
| `google-v1.0` | same file | <https://deepmind-media.storage.googleapis.com/DeepMind.com/Blog/introducing-the-frontier-safety-framework/fsf-technical-report.pdf> |
| `google-v2.0` | same file | <https://web.archive.org/web/20250205011727id_/https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/updating-the-frontier-safety-framework/Frontier%20Safety%20Framework%202.0.pdf> |
| `google-v3.0` | same file | <https://deepmind-media.storage.googleapis.com/DeepMind.com/Blog/strengthening-our-frontier-safety-framework/frontier-safety-framework_3.pdf> |
| `google-v3.1` | same file | <https://deepmind-media.storage.googleapis.com/DeepMind.com/Blog/strengthening-our-frontier-safety-framework/frontier-safety-framework_3-1.pdf> |
| `meta-v1.1` | DIFFERENT FILE b375e2302d1b | <https://web.archive.org/web/20250213105620id_/https://ai.meta.com/static-resource/meta-frontier-ai-framework/> |
| `meta-v2` | same file | <https://ai.meta.com/static-resource/Meta_Advanced-AI-Scaling-Framework-v2> |
| `meta-v2.1` | same file | <https://research.meta.ai/static/meta-superintelligence-scaling-framework> |
| `openai-beta` | same file | <https://cdn.openai.com/openai-preparedness-framework-beta.pdf> |
| `openai-v2` | same file | <https://web.archive.org/web/20250415191354id_/https://cdn.openai.com/pdf/18a02b5d-6b67-4cec-ab64-68cdfbddebcd/preparedness-framework-v2.pdf> |

- `same file`: the address works, and the bytes have the hash that the ledger records.
- `DIFFERENT FILE`: the address works, but the bytes are different. A person must look.
- `HTTP 403` or `no answer`: the site refused the check. Open the address in a browser.
