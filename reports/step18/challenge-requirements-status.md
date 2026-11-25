# SAANS SAATHI AI — Challenge Requirements Status

## Current Status: UNCONFIRMED

The following challenge-specific requirements cannot be confirmed from within this execution environment. The PromptWars Virtual Challenge 6 portal is not accessible. User must verify these from the official challenge portal.

| Requirement | Status | Notes |
|-------------|--------|-------|
| **Deadline** | ❌ UNCONFIRMED | Date by which submission must be complete |
| **Maximum attempts** | ❌ UNCONFIRMED | Number of submission attempts allowed |
| **GitHub visibility** | ❌ UNCONFIRMED | Repository must be public/private; visibility requirements |
| **Deployment URL** | ❌ UNCONFIRMED | Live app URL required (Vercel/Render/GitHub Pages) |
| **Demo video** | ❌ UNCONFIRMED | Required video showing actual working features |
| **GenAI declaration** | ❌ UNCONFIRMED | Whether Gemini/API key usage must be declared |
| **Changes description format** | ❌ UNCONFIRMED | Required format for listing code changes |
| **LinkedIn post requirement** | ❌ UNCONFIRMED | Whether a LinkedIn post is mandatory after submission |
| **Mandatory form fields** | ❌ UNCONFIRMED | Specific form fields and required content |
| **Submission format** | ❌ UNCONFIRMED | ZIP, GitHub link, or other submission method |
| **Leaderboard visibility** | ❌ UNCONFIRMED | Whether submission appears on public leaderboard |
| **Prize eligibility** | ❌ UNCONFIRMED | Whether submission is eligible for awards |
| **Judging criteria weights** | ❌ UNCONFIRMED | If available, weights for each evaluation category |

## Required User Actions

Before completing the external submission, the user must:

1. **Access the official PromptWars Virtual Challenge 6 portal** and confirm:
   - Submission deadline
   - Maximum number of attempts
   - GitHub repository visibility requirements (public/private)
   - Whether a live deployment URL is required
   - Whether a demo video is mandatory
   - Required genAI/API key declaration format
   - Required changes description format
   - Whether a LinkedIn post is required after submission
   - All mandatory form fields and their content requirements
   - Submission method (ZIP upload, GitHub link, form, etc.)

2. **If deployment URL is required**:
   - Configure `render.yaml` for Render deployment
   - Or configure `vercel.json` for Vercel deployment
   - Or configure `Procfile` for alternative hosting
   - Deploy the application and obtain a public URL
   - Verify the deployed application works (smoke test)

3. **If demo video is required**:
   - Follow the demo-video-guide.md
   - Record 3-5 minute video of actual working features
   - No API keys displayed
   - No fabricated metrics
   - Show real features end-to-end
   - Upload video to YouTube/Vimeo and obtain URL

4. **If Gemini API key is required for evaluation**:
   - Obtain Gemini API key
   - Configure it in the application
   - Re-run AI quality evaluation to verify live responses
   - Note: deterministic fallback always functional without key

5. **Complete all mandatory form fields** with actual URLs and descriptions:
   - GitHub repository URL
   - Live deployment URL (if required)
   - Demo video URL (if required)
   - Changes description (format per challenge requirements)
   - Any other required fields

## Known Submission Requirements from Prior Phases

Based on the existing `docs/CHALLENGE_REQUIREMENTS.md` and `docs/FINAL_SUBMISSION_READINESS.md`:

| Field | Current State | Required Action |
|-------|--------------|----------------|
| GitHub URL | `0a22cc4` on `main`; 359 files; 2.45 MB | Confirm public/private requirement; repository is at current state |
| Live app URL | `http://localhost:3000` (development only) | If required: deploy and obtain URL |
| Demo video | Not recorded | If required: produce per guide |
| Changes description | Not documented | If required: list actual changes from baseline |
| LinkedIn post | Not confirmed | If required: post after submission |
| Form fields | UNCONFIRMED | Portal-specific fields |

## Next Steps

**User must**:
1. Access the official challenge portal
2. Confirm all UNCONFIRMED requirements listed above
3. Complete any required actions (deploy, demo video, form fields)
4. Update `docs/CHALLENGE_REQUIREMENTS.md` with confirmed status
5. Update `docs/FINAL_SUBMISSION_READINESS.md` with final verdict after confirmation

This document will be superseded once the user confirms requirements from the official portal.