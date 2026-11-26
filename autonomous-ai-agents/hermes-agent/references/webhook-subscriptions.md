# Webhook Subscriptions — Extended Patterns

Create dynamic webhook subscriptions so external services (GitHub, GitLab, Stripe, CI/CD, IoT sensors, monitoring tools) can trigger Hermes agent runs by POSTing events to a URL.

## Setup

The webhook platform must be enabled before subscriptions can be created:
```bash
hermes webhook list
```

If not enabled: `hermes gateway setup` → enable webhooks, or manually add to `config.yaml`:
```yaml
platforms:
  webhook:
    enabled: true
    extra:
      host: "0.0.0.0"
      port: 8644
      secret: "***"
```

Start gateway: `hermes gateway run`. Verify: `curl http://localhost:8644/health`.

## Prompt Templates

Prompts support `{dot.notation}` for accessing nested payload fields:
- `{issue.title}` — GitHub issue title
- `{pull_request.user.login}` — PR author
- `{data.object.amount}` — Stripe payment amount

## Common Patterns

**GitHub: new issues**
```bash
hermes webhook subscribe github-issues \
  --events "issues" \
  --prompt "New GitHub issue #{issue.number}: {issue.title}\n\nAction: {action}\nAuthor: {issue.user.login}\nBody:\n{issue.body}\n\nPlease triage this issue." \
  --deliver telegram \
  --deliver-chat-id "-100123456789"
```

**GitHub: PR reviews**
```bash
hermes webhook subscribe github-prs \
  --events "pull_request" \
  --prompt "PR #{pull_request.number} {action}: {pull_request.title}\nBy: {pull_request.user.login}" \
  --skills "github-code-review" \
  --deliver github_comment
```

**Stripe: payment events**
```bash
hermes webhook subscribe stripe-payments \
  --events "payment_intent.succeeded,payment_intent.payment_failed" \
  --prompt "Payment {data.object.status}: {data.object.amount} cents from {data.object.receipt_email}" \
  --deliver telegram
```

**CI/CD: build notifications**
```bash
hermes webhook subscribe ci-builds \
  --events "pipeline" \
  --prompt "Build {object_attributes.status} on {project.name} branch {object_attributes.ref}" \
  --deliver discord
```

**Direct delivery (no agent, zero LLM cost)**
```bash
hermes webhook subscribe antenna-matches \
  --deliver telegram --deliver-chat-id "123456789" --deliver-only \
  --prompt "🎉 New match: {match.user_name} matched with you!"
```

## Security

- Each subscription gets an auto-generated HMAC-SHA256 secret.
- Static routes from config.yaml cannot be overwritten by dynamic subscriptions.
- Subscriptions persist to `~/.hermes/webhook_subscriptions.json`.

## Troubleshooting

1. Check gateway is running: `systemctl --user status hermes-gateway`
2. Check health: `curl http://localhost:8644/health`
3. Check logs: `grep webhook ~/.hermes/logs/gateway.log | tail -20`
4. Signature mismatch? Verify secret matches.
5. Firewall/NAT? Use a tunnel (ngrok, cloudflared).
