# Error Ledger — Bruno Falqueto (MATHutrice)

Every error of my Fork production, kept in the fork itself: the Error Ledger issues on EPF-MDE/MATHutrice were closed as not planned on 12 November 2026, and the fork is now the evidence project. One entry per look at production; each entry is a commit.

Fork production: `https://bonru-mathutrice-production.azurewebsites.net`, as its production signals report it.

- **PostHog project:** "Default project", EU region (project 360276).
- **Saved query:** `Production errors by issue, with users reached`, on the dashboard `Fork production`.
- **Fork:** https://github.com/Bonru/MATHutrice. Production only receives an image staging already ran, through the Promotion (`.github/workflows/promote.yml`).
- An error's rate is its count of exceptions divided by the time from `first_seen` to `last_seen`.

## Entry 1 — 23 November 2026, 11:15 UTC

The saved query's rows, every column (`types` and `message` added, `message` cut at 80 characters):

| issue | types | message | exceptions | users | first_seen | last_seen |
|---|---|---|---|---|---|---|
| 01a207e0-2c0a-7640-8f8e-b75b92a57858 | AuthenticationError | Error code: 401 - {'detail': 'Invalid API Key'} | 3 | 1 | 2026-11-23T10:07:40Z | 2026-11-23T10:39:31Z |
| 01a207c7-51a5-72c2-af97-15bd7ac25290 | APIConnectionError, UnsupportedProtocol | Connection error. / Request URL is missing an 'http://' or 'https://' protocol | 1 | 1 | 2026-11-23T09:40:29Z | 2026-11-23T09:40:29Z |
| 01a20814-1f2c-7a51-951c-93df50098b73 | RateLimitError | Error code: 429 - Rate limit exceeded | 1 | 1 | 2026-11-23T11:04:24Z | 2026-11-23T11:04:24Z |
| 01a20815-94dc-7291-88aa-befcd353969d | RateLimitError | Error code: 429 - Rate limit exceeded | 1 | 1 | 2026-11-23T11:05:57Z | 2026-11-23T11:05:57Z |

The one user is my own account, `bruno.falquetobusato@epfedu.fr`, signed in to Fork production with the production key. No simulated user had reached it yet.

### Ranking, by users reached and rate

| Rank | Error | Users | Exceptions | Rate | Blast radius |
|---|---|---|---|---|---|
| 1 | `AuthenticationError` 401 | 1 | 3 | 3 in 31 min 51 s ≈ **5.7 per hour** | every LLM call: questions, grading, chat, evaluation. No student can train while it lasts |
| 2 | `APIConnectionError` / `UnsupportedProtocol` | 1 | 1 | one occurrence, no rate | every LLM call, as for rank 1 |
| 3 | `RateLimitError` 429 (two issues, one cause) | 1 | 2 | 2 in 1 min 33 s, during one burst of tests | the LLM calls made above the account's limit, while it is exceeded |

### What caused each, and what was done

1. **`AuthenticationError` 401 — fixed.** The `LLM_API_KEY` secret of the `production` and `staging` GitHub Environments did not hold a valid Mistral key. Fix: a new Mistral key, stored in both environments, then deployed through the pipeline: staging by re-running its deploy, production by the Promotion [run 45160964305](https://github.com/Bonru/MATHutrice/actions/runs/45160964305) (10:58 UTC). **After the deploy:** no 401 since 10:39:31. At 11:06:11, a grading call from Fork production went through the gateway and answered `200 OK` (PostHog Logs, `production`).
2. **`APIConnectionError` / `UnsupportedProtocol` — fixed.** The `LLM_BASE_URL` secret of `production` did not hold the gateway URL: the client found no `https://` in it. Fix: the secret set to the URL the Instructor gave, then the Promotion [run 45149650848](https://github.com/Bonru/MATHutrice/actions/runs/45149650848) (09:43 UTC). **After the deploy:** no `APIConnectionError` since 09:40:29; the next calls reached the gateway (they failed on the key, rank 1).
3. **`RateLimitError` 429 — left for later, deliberately.** Data: 2 exceptions, 1 user, both inside 93 seconds, both caused by my own burst of test requests (a positioning test makes 11 LLM calls in a row), right after many retries while fixing ranks 1 and 2. The free Mistral plan allows 30 requests a minute (read from `x-ratelimit-limit-req-minute`, 25 September 2026). With no student traffic, it reached nobody but me, and a single grading call one minute later went through. **What would make me fix it:** a second user reached, or the rate rising during a session slot. My Design Document's numbers say it will: 30 students starting a 20-question test make 1,200 calls against 30 a minute. The fix then belongs in the LLM client seam (`mathutrice/llm_client.py`), which every call goes through.

### What I would look at first

Rank 1: the most exceptions, the highest rate, and a blast radius of every LLM feature. Its fix is deployed and confirmed by production data. Next, I watch rank 3, the one whose cause is still in place.
