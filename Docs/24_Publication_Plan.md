# 24. English documentation and repository publication

**Date:** 2026-11-15. **Status:** scope and approach approved by the project owner in conversation.

## Approved design

Publish an English project overview and documentation covering purpose, current status, procedures, tools, workflows, bibliography, original data pages, generative-AI use and potential benefits. Preserve source identifiers, stable document paths and existing application work.

### Approaches

| Approach | Trade-off | Decision |
|---|---|---|
| Upload the entire local research archive | Includes approximately 8 GB, incomplete downloads and avoidable redistribution/privacy risks | Rejected |
| Publish documentation, reproducible scripts, catalogs and manifests; omit raw research data and private history | Smaller, reviewable repository; readers restore originals from linked archives | Approved |

Public documentation is edited into an English reference edition rather than a line-by-line reproduction of every earlier planning paragraph. Historical planning is identified as such; original Spanish working documents are preserved locally before editing.

## Publication plan

1. Inspect existing docs, source metadata and actual application capabilities.
2. Preserve a local pre-edit documentation copy.
3. Publish English README, dossier, application/data procedures and AI disclosure.
4. Exclude private tooling/history, secrets, temporary outputs and raw research downloads.
5. Check documentation links, source IDs, staged file sizes and sensitive information.
6. Run applicable application tests/build when publishing the existing prototype snapshot; do not claim scientific validation from software tests.
7. Commit and push non-destructively to the configured repository; verify the remote commit.

## Non-goals and risks

No new application behavior, data acquisition campaign, feature-completion claim or safety certification is introduced by this documentation task. The full historical model-use inventory, source URL availability and third-party asset rights still require human confirmation.
