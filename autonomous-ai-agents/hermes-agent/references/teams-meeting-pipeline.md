# Teams Meeting Pipeline

The `hermes teams-pipeline` CLI manages Microsoft Teams meeting summaries, transcripts, and Graph webhook subscriptions.

## Prerequisites

Set in `~/.hermes/.env`:
```bash
MSGRAPH_TENANT_ID=...
MSGRAPH_CLIENT_ID=...
MSGRAPH_CLIENT_SECRET=...
```

## Commands

```bash
# Status & inspection
hermes teams-pipeline validate              # config snapshot
hermes teams-pipeline token-health          # Graph token status
hermes teams-pipeline list                  # recent meeting jobs
hermes teams-pipeline list --status failed  # only failed jobs
hermes teams-pipeline show <job-id>         # full detail
hermes teams-pipeline subscriptions         # current Graph webhook subscriptions

# Re-running / debugging
hermes teams-pipeline run <job-id>          # replay stored job
hermes teams-pipeline fetch --meeting-id <id>   # dry-run

# Subscription management
hermes teams-pipeline subscribe --resource communications/onlineMeetings/getAllTranscripts ...
hermes teams-pipeline renew-subscription <sub-id> --expiration <iso-8601>
hermes teams-pipeline delete-subscription <sub-id>
hermes teams-pipeline maintain-subscriptions           # renew near-expiry
```

## Critical Pitfall: Graph subscriptions expire in 72 hours

Microsoft Graph caps webhook subscriptions at 72 hours and will NOT auto-renew. Set up automated renewal via a cron job at 12-hour intervals.

If the user reports "the pipeline worked yesterday but nothing is arriving today":
1. `hermes teams-pipeline subscriptions` — check for expired entries
2. Recreate with `subscribe`
3. Set up automated renewal via `hermes cron add` or systemd timer
