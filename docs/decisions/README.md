# TSE Excel — Decision Index

This folder contains independently maintained decision records. Read only those relevant to the current task, rather than all ADR bodies. The [historical decision log](HISTORICAL-DECISIONS.md) preserves the entire original D-001 through D-021 file verbatim, including originally recorded statuses. Open questions and legacy technical evidence remain in [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md).

A decision's original statement remains historically intact. Superseded records are retained; only the currently accepted superseding decision governs new work. Do not invent historical approval dates or rationale.

| ID | Decision | Current status | Record |
|---|---|---|---|
| D-001 | Canonical repository | Approved | [0001-canonical-repository.md](0001-canonical-repository.md) |
| D-002 | C#/.NET without VBA | Approved | [0002-csharp-dotnet-no-vba.md](0002-csharp-dotnet-no-vba.md) |
| D-003 | Excel-DNA/XLL integration | Approved direction | [0003-excel-dna-xll-integration.md](0003-excel-dna-xll-integration.md) |
| D-004 | Workbook and compiled code responsibilities | Approved direction | [0004-workbook-and-code-responsibilities.md](0004-workbook-and-code-responsibilities.md) |
| D-005 | Local MVP and deferred auto-updater | Approved | [0005-local-mvp-and-deferred-updater.md](0005-local-mvp-and-deferred-updater.md) |
| D-006 | Minimal ChatGPT bootstrap | Approved | [0006-minimal-chatgpt-bootstrap.md](0006-minimal-chatgpt-bootstrap.md) |
| D-007 | Project language rules | Approved | [0007-project-language-rules.md](0007-project-language-rules.md) |
| D-008 | Engineering quality and tests | Approved | [0008-engineering-quality-and-tests.md](0008-engineering-quality-and-tests.md) |
| D-009 | Product Owner authority | Approved | [0009-product-owner-authority.md](0009-product-owner-authority.md) |
| D-010 | ChatGPT advisory and documentation role | Approved | [0010-chatgpt-advisory-and-doc-role.md](0010-chatgpt-advisory-and-doc-role.md) |
| D-011 | Codex source workflow | Approved | [0011-codex-source-workflow.md](0011-codex-source-workflow.md) |
| D-012 | Documentation approval and commit | Approved | [0012-approved-documentation-commit.md](0012-approved-documentation-commit.md) |
| D-013 | Mandatory Operating Contract first read | Superseded by D-022 | [0013-mandatory-operating-contract-first-read.md](0013-mandatory-operating-contract-first-read.md) |
| D-014 | ChatGPT Project context synchronization | Superseded by D-022 | [0014-chatgpt-project-context-sync.md](0014-chatgpt-project-context-sync.md) |
| D-015 | Deferred commercial backend and Python | Approved as deferral | [0015-deferred-commercial-backend-and-python.md](0015-deferred-commercial-backend-and-python.md) |
| D-016 | Pre-MVP Ribbon JSON prototype | Approved | [0016-pre-mvp-ribbon-json-prototype.md](0016-pre-mvp-ribbon-json-prototype.md) |
| D-017 | Workbook-specific JSON configuration | Approved direction | [0017-workbook-specific-json-config.md](0017-workbook-specific-json-config.md) |
| D-018 | Future JSON editing and locking | Approved direction; implementation deferred | [0018-future-json-editing-and-locking.md](0018-future-json-editing-and-locking.md) |
| D-019 | Stepwise PO guidance | Approved | [0019-stepwise-po-guidance.md](0019-stepwise-po-guidance.md) |
| D-020 | Codex model neutrality | Approved | [0020-codex-model-neutrality.md](0020-codex-model-neutrality.md) |
| D-021 | ChatGPT documentation commits on main | Approved | [0021-chatgpt-doc-commits-on-main.md](0021-chatgpt-doc-commits-on-main.md) |
| D-022 | Minimal ChatGPT Context Routing | Accepted | [0022-minimal-chatgpt-context-routing.md](0022-minimal-chatgpt-context-routing.md) |
| D-023 | GUI-First Local Development Workflow | Accepted | [0023-gui-first-local-development.md](0023-gui-first-local-development.md) |
| D-024 | Future Automated Release and User-Initiated Update | Accepted as deferred future direction | [0024-future-release-and-update.md](0024-future-release-and-update.md) |
| D-025 | Four-Project Modular Architecture and Feature-First Organization | Accepted | [0025-four-project-feature-first-architecture.md](0025-four-project-feature-first-architecture.md) |
| D-026 | Extensible Broker Integration and Excel-Hosted Order Execution | Accepted; broader implementation deferred | [0026-extensible-brokers-excel-hosted-trading.md](0026-extensible-brokers-excel-hosted-trading.md) |
| D-027 | EasyTrader Web API Integration and Local Trading Proof of Concept | Accepted; partially superseded by D-028 for the Excel-hosted opening-order POC | [0027-easytrader-web-api-local-trading-poc.md](0027-easytrader-web-api-local-trading-poc.md) |
| D-028 | Excel-Hosted Mofid Opening-Order Proof of Concept | Accepted; implementation pending | [0028-excel-hosted-mofid-opening-order-poc.md](0028-excel-hosted-mofid-opening-order-poc.md) |
| D-029 | Feature-Branch Source Delivery, Review, and Authorized Merge | Accepted | [0029-feature-branch-source-review-workflow.md](0029-feature-branch-source-review-workflow.md) |
| D-030 | Native HTTP Opening-Order Reference and Excel Port Alignment | Accepted | [0030-native-http-opening-order-reference-and-excel-port.md](0030-native-http-opening-order-reference-and-excel-port.md) |
| D-031 | Temporary Reopening of Direct HTTP Python POC for Reliability Validation | Accepted; temporary exception | [0031-temporary-reopening-of-direct-http-python-poc.md](0031-temporary-reopening-of-direct-http-python-poc.md) |

### D-027 / D-028 relationship

D-028 governs the specific Excel-hosted opening-order POC and supersedes only the conflicting D-027 Console-first/single-order sequencing for that bounded task. D-027's API uncertainty, authentication integrity, credential protection and broker-authorization caveats remain in force. D-026 remains the broader deferred broker/trading direction.

D-029 supersedes only earlier conflicting source commit/push and merge-authority provisions. Earlier decisions remain preserved; PO-owned acceptance, ChatGPT's read-only source editing boundary, and documentation approval requirements remain in force.

D-030 supplements D-028 for the native-HTTP Excel port. It designates the newer Python direct-HTTP POC as a read-only behavioral reference and records the post-login native transport, bounded request pacing, connection warmup, asynchronous outcome observation, and workbook-adjacent tracing requirements. D-030 supersedes only conflicting transport/dispatch and response-observation details for this port; D-028's approved UI, order, financial, safety, and four-project boundaries remain.

D-031 temporarily reopens only `POC/easytrader_direct_http_poc.py` and `POC/test_easytrader_direct_http_poc.py` for the PO-approved, staged Python reliability-validation program. It supersedes D-030's conflicting read-only restriction only for those two files and only until the PO accepts the validation program or withdraws the authorization. The historical `POC/easytrader_poc.py` remains read-only; D-030 continues to govern the Excel/C# implementation.

Future material decisions require PO approval before implementation. Use new numbered ADRs and explicit supersession when warranted.
