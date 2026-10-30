# Probe spec

Write one Python 3.12 file, `probes.py`, using only the standard library and the `gh` CLI (already logged in). It must define `probe(kind: str, target: dict) -> bool`, returning True only when the real system matches the claim, and False otherwise, including when the thing does not exist. Never raise. Cloudflare account id is `29db7c74093386544fed8046ef083a4b`. A Cloudflare API token is in the environment variable `CF_TOKEN` (base URL `https://api.cloudflare.com/client/v4`). For R2, use the wrangler CLI at `npx wrangler` with `--remote` and env `CLOUDFLARE_ACCOUNT_ID`, because the token cannot read R2 objects over REST.

Kinds and target fields:

- `d1_row`: `{database_id, table, id, expect: {column: value, ...}}`. True if the row with that `id` exists and every expected column equals its value.
- `kv_key`: `{namespace_id, key, expect}`. True if the key exists and its value equals `expect`.
- `r2_object`: `{bucket, key, expect}`. True if the object exists and its body equals `expect`.
- `gh_pr`: `{repo, number, expect: "merged"}`. True if the pull request is merged.
- `gh_actions`: `{repo, sha, expect: "success"}`. True if every completed workflow run for that exact commit concluded `success` and at least one exists.
