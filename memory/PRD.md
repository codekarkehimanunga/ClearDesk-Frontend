# ClearDesk Product Requirements

## Original problem statement
ClearDesk is a B2B SaaS platform for contractors, consultancies, construction companies, and other large tender-based organizations to manage contract-governed email correspondence. It connects to the user’s mailbox, processes relevant emails with document attachments, automatically organizes them by project, classifies the communication type, and checks each message against the project’s master contract and previous conversation history. The system identifies contractual risks, incorrect claims, missed obligations, and response deadlines, then prioritizes correspondence in a central action queue called The Docket. It can also generate contract-backed reply drafts using verified excerpts from the original contract, while keeping the user in control through mandatory review and approval before anything is sent.

## Architecture decisions
- React frontend with FastAPI backend and the configured external API URL.
- Seeded demo workspace with rule-based contract checks; no sign-in or external mailbox credentials for MVP.
- Demo docket data is served by `/api/dashboard`; review actions use `PATCH /api/docket/{item_id}`.
- MongoDB starter connection remains available for future persisted workspace state.

## User personas
Senior managers, project directors, commercial heads, contract managers, and executives handling large-scale projects.

## Core requirements (static)
- Central action queue called The Docket
- Project grouping, correspondence classification, risk level, deadlines, status, contract excerpt, and attachment visibility
- Mandatory user action before reply drafting or review completion
- Calm, premium, light professional interface with responsive mobile navigation

## Implemented
- 2026-08-21: ClearDesk executive dashboard with sidebar, workspace/project context, portfolio stats, weekly insight strip, filters, search field, docket list, and correspondence detail panel.
- 2026-08-21: Seeded West Quay, Harbour Point, and Riverside correspondence with contract-backed risk explanations and attachment metadata.
- 2026-08-21: Working mark-reviewed and draft-reply status actions, responsive mobile navigation, desktop/mobile verification, and 404 handling for unknown docket IDs.

## Prioritized backlog
- P0: Persist per-workspace docket state in MongoDB.
- P1: Add Gmail and Microsoft 365 mailbox connection flows.
- P1: Add contract and attachment upload/parsing.
- P1: Add verified AI reply drafting with GPT 5.6 Terra after credentials are configured.
- P2: Add contract clause search and AI assistant chat.
- P2: Add outbound approval/send workflow and complete communication history.

## Next tasks
1. Replace seeded mailbox data with a mailbox connector and ingestion pipeline.
2. Add contract document upload, clause indexing, and project linking.
3. Introduce GPT 5.6 Terra for risk explanations and reply drafts behind mandatory approval.
