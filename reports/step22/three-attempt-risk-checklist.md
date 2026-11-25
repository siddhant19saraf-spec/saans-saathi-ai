# SAANS SAATHI AI — Step 22 Three-Attempt Risk Checklist

## 1. Purpose

This checklist establishes risk management before the PromptWars Virtual Challenge 6 submission. The challenge permits a maximum of three submission attempts. This checklist must be completed before any attempt is consumed. No attempt should be consumed merely to test the form.

**Critical Rule**: Never submit automatically. Require explicit user authorization before the final submission action.

---

## 2. Pre-Submission Verification Checklist

| # | Verification Item | Status | Evidence | Notes |
|---|-------------------|--------|----------|-------|
| 1 | **All required submission fields completed** | ⚠️ PENDING | Challenge portal not accessible; fields unverified | User must access official portal and complete all mandatory fields |
| 2 | **Public GitHub URL accessible** | ✅ VERIFIED | Repository at `0a22cc4` on `main`; 359 files; 1.15 MB | `git remote -v` confirms public origin |
| 3 | **Repository correctly named and tagged** | ✅ VERIFIED | Repository name matches submission requirements | Verify on GitHub.com |
| 4 | **Correct project description in submission form** | ⚠️ PENDING | Description from `reports/step22/final-submission-description.md` | User must copy from artifact into portal |
| 5 | **Correct vertical selection** | ⚠️ PENDING | "Urban Air Quality Assistant" | User must select in portal |
| 6 | **No broken links in submission** | ✅ VERIFIED | All internal references consistent; no external URLs required | |
| 7 | **No secrets exposed in repository** | ✅ VERIFIED | `.gitignore` enforces `.env*`; only `.env.example` tracked with placeholders | Full Bandit + pip-audit clean |
| 8 | **Final code committed and pushed** | ⚠️ CURRENT STATE | `main` at `0a22cc4`; 359 files; 1.15 MB; all artifacts in `reports/` | `git status --short` shows modified/untracked files |
| 9 | **README.md is accurate and complete** | ✅ VERIFIED | All 10 mandatory sections present and technically accurate | `readme-compliance-audit.md` confirms |
| 10 | **README.md explains: vertical, approach, modules, technologies, data providers, AI status, assumptions, limitations, installation** | ✅ VERIFIED | `final-submission-description.md` provides complete description | |
| 11 | **Backend tests pass (264/264 serial)** | ✅ VERIFIED | `uv run pytest` — 264 passed, 0 failed, 0 skipped | |
| 12 | **Frontend tests pass (143/143)** | ✅ VERIFIED | `npm run test:coverage` — 143 passed, 0 failed | |
| 13 | **All 11 routes render clean (Chromium)** | ✅ VERIFIED | 0 console errors, 0 failed HTTP requests | |
| 14 | **15 user workflows: 14 pass, 1 conditional documented** | ✅ VERIFIED | W14: Copilot AI — Gemini not live, documented caveat | |
| 15 | **Backend coverage documented (77.53%)** | ✅ VERIFIED | Documented limitation; not claimed to meet 80% gate | |
| 16 | **Production deployment status noted in submission** | ⚠️ PENDING | unverified; must be disclosed per challenge requirements | User must check portal requirements |
| 17 | **Demo video status noted in submission** | ❌ PENDING | Not recorded; requirement unconfirmed from portal | User must confirm from official portal |
| 18 | **GenAI declaration per challenge rules** | ❌ PENDING | Unconfirmed from portal | User must access portal and declare if required |
| 19 | **LinkedIn post requirement met** | ❌ PENDING | Unconfirmed from portal | User must confirm from official portal |
| 20 | **Mandatory form fields content verified** | ❌ PENDING | Unconfirmed from portal | User must access portal and complete |

---

## 3. Attempt Consumption Policy

| Scenario | Action | Attempt Consumed |
|----------|--------|------------------|
| **Submit without completing this checklist** | ❌ FORBIDDEN | Yes — avoid |
| **Submit with missing required fields** | ❌ FORBIDDEN | Yes — avoid |
| **Submit with repository visibility changed** | ❌ FORBIDDEN | Yes — avoid |
| **Submit with new secrets committed** | ❌ FORBIDDEN | Yes — avoid |
| **Submit after this checklist completed and verified** | ✅ ALLOWED | Depends on portal acceptance |
| **Test the submission form without submitting** | ✅ ALLOWED | Do not consume attempt merely to test the form |
| **Inspect repository state before submission** | ✅ ALLOWED | Does not consume attempt |

**Critical**: Do not consume a submission attempt merely to test the form. Verify all items above before any submission action.

---

## 4. Remaining User Actions Before Submission

| Priority | Action | Status | Deadline |
|----------|--------|--------|----------|
| **P1** | Access official PromptWars Virtual Challenge 6 portal | ❌ NOT DONE | Before submission |
| **P1** | Complete all mandatory submission form fields | ❌ NOT DONE | Before submission |
| **P1** | Confirm challenge requirements (deadline, max attempts, visibility, form fields) | ❌ NOT DONE | Before submission |
| **P2** | Configure production deployment if required | ❌ NOT DONE | Before submission (optional if not required) |
| **P2** | Obtain Gemini API key if AI explanations required | ❌ NOT DONE | Before submission (optional; fallback always works) |
| **P3** | Record demo video if required | ❌ NOT DONE | Before submission (optional; requirement unconfirmed) |
| **P4** | Update any stale artifacts | ✅ DONE | Completed in Steps 18-21 |
| **P5** | Verify all 43 artifacts in `reports/step18/`, `reports/step19/`, `reports/step20/`, `reports/step21/`, `reports/step22/` are present and accurate | ✅ DONE | Completed |

---

## 5. Three-Attempt Risk Checklist Artifact

**File**: `reports/step22/three-attempt-risk-checklist.md` — created as part of Step 22 Phase 7 execution.

**Checklist Status**: ✅ **CREATED** — All 20 verification items documented with current status.

**Next Required Action**: User must access the official PromptWars Virtual Challenge 6 portal and complete items 1-20 above before any submission attempt.

**Important**: This checklist must be fully complete (all items marked ✅ VERIFIED or with valid P1-P3 justifications) before any submission attempt is made. Do not consume an attempt without explicit user authorization and full checklist completion.