# grounding-sandbox

Probes that check an agent's claims against the real system instead of trusting its words.

An agent says "I wrote the row", "the PR is merged" or "CI is green". A probe asks the real system and returns true only if the claim holds.

| File | What |
|---|---|
| `s2-agent/SPEC.md` | The probe contract: kinds, target fields, and what "true" means |
| `s2-agent/probes.py` | `probe(kind, target) -> bool` for D1 rows, KV keys, R2 objects, GitHub PRs and GitHub Actions runs |
| `tasks.py` | The task set used to score probes against agent claims |

## Use

```sh
export CF_TOKEN=...            # Cloudflare API token, read access
export CLOUDFLARE_ACCOUNT_ID=...
cd s2-agent && python3 -c "from probes import probe; print(probe('gh_pr', {'repo': 'owner/repo', 'number': 1, 'expect': 'merged'}))"
```

`gh` must be logged in for the GitHub probes.

## Status

Research. Run outputs and session logs are not in this repo.

MIT licensed.
