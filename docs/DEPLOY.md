# Stare deployment guide (AWS EC2, single instance)

This is the production walkthrough for the Streamlit app and FastAPI
backend. The Next.js landing page deploys separately to AWS Amplify
(see Phase 4 follow-up).

The whole stack runs on **one t3.small instance** (2 vCPU, 2 GB RAM,
~$15/month on-demand) behind Caddy with auto-issued Let's Encrypt
certs. Total wall-clock from a fresh AWS account to a working
`https://<domain>/` is about 25 minutes, most of which is the corpus
upload.

---

## 0. Prerequisites

On your laptop:

- AWS account with permission to launch EC2 + edit Route 53 (or whatever
  DNS provider you use)
- The Stare repo cloned locally with `data/raw/`, `data/processed/`, and
  `data/cached/chroma_db/` populated from Phases 1 and 2
- An SSH key pair you can attach to the EC2 instance
- A domain you control, with an A-record ready to point at the
  instance's elastic IP

---

## 1. Launch the EC2 instance

AWS Console → EC2 → Launch instance:

| Field           | Value                                              |
|-----------------|----------------------------------------------------|
| Name            | `stare-prod`                                       |
| AMI             | Ubuntu Server 22.04 LTS (HVM), SSD                 |
| Instance type   | `t3.small`                                         |
| Key pair        | (your SSH key)                                     |
| Storage         | 30 GB gp3                                          |

**Security group rules (inbound):**

| Type   | Protocol | Port | Source       | Purpose                  |
|--------|----------|------|--------------|--------------------------|
| SSH    | TCP      | 22   | Your IP/32   | Admin access             |
| HTTP   | TCP      | 80   | 0.0.0.0/0    | Plain HTTP + ACME        |
| HTTPS  | TCP      | 443  | 0.0.0.0/0    | Production traffic       |
| HTTPS  | UDP      | 443  | 0.0.0.0/0    | HTTP/3 (QUIC), optional  |

After launch, allocate an **Elastic IP** and associate it with the
instance so the public IP survives reboots.

---

## 2. Point DNS at the instance

In Route 53 (or your DNS provider):

```
stare.example.com.  A  300  <elastic-ip>
```

DNS propagation usually completes in a few minutes. Confirm with:

```bash
dig +short stare.example.com
```

---

## 3. SSH in and bootstrap

```bash
ssh -i ~/.ssh/your-key.pem ubuntu@<elastic-ip>
```

Inside the instance:

```bash
curl -fsSL https://raw.githubusercontent.com/mbharuya1/stare/main/scripts/deploy_ec2.sh \
  | bash
```

This installs Docker + the compose plugin, adds `ubuntu` to the
`docker` group, and clones the repo to `~/stare`. The script is
idempotent, so re-running it is safe.

**Log out and back in** after the first run so the docker group
membership takes effect:

```bash
exit
ssh -i ~/.ssh/your-key.pem ubuntu@<elastic-ip>
```

---

## 4. Upload the corpus

From your laptop (NOT the instance) at the repo root:

```bash
rsync -avzP --partial \
    ./data/raw/ ./data/processed/ ./data/cached/ \
    ubuntu@<elastic-ip>:/home/ubuntu/stare/data/
```

Roughly 2 GB. On a typical home connection it takes 10–15 minutes.

If you would rather not ship the raw CAP archives, omit `./data/raw/`.
The backend only reads from `data/processed/scotus_cases.jsonl` and
`data/cached/chroma_db/`.

---

## 5. Fill in secrets

Back on the EC2 instance:

```bash
nano ~/stare/docker/.env
```

Required:

```
DOMAIN=stare.example.com
ACME_EMAIL=you@example.com
ANTHROPIC_API_KEY=sk-ant-...
LANGSMITH_API_KEY=ls__...        # optional, tracing off if blank
USE_RERANKER=true
LANDING_URL=https://stare.example.com
```

---

## 6. Bring the stack up

```bash
cd ~/stare
docker compose -f docker/docker-compose.yml --env-file docker/.env up -d
```

First build takes 5–10 minutes (torch + transformers wheels are large).
Subsequent restarts are cached and start in seconds.

Watch the rollout:

```bash
docker compose -f docker/docker-compose.yml logs -f
```

Useful subcommands:

```bash
docker compose -f docker/docker-compose.yml ps              # container status
docker compose -f docker/docker-compose.yml restart caddy   # reload Caddy
docker compose -f docker/docker-compose.yml exec backend bash
```

---

## 7. Verify

From your laptop:

```bash
curl --verbose https://stare.example.com/api/health
# Expect: HTTP/2 200 and a JSON body with "status":"ok"

open https://stare.example.com/
# Streamlit loads. Try a sample chip → full answer card renders.
```

If `/api/health` succeeds but `/` shows a Caddy error page, the
backend is up but Streamlit is not yet ready. Wait 30 seconds and
retry — Streamlit takes longer to start than FastAPI.

If you get a cert error in the first minute or two, Caddy is still
negotiating with Let's Encrypt. Caddy retries automatically.

---

## 8. Day-2 operations

**Update to a new release:**

```bash
ssh ubuntu@<elastic-ip>
cd ~/stare
git pull
docker compose -f docker/docker-compose.yml --env-file docker/.env build
docker compose -f docker/docker-compose.yml --env-file docker/.env up -d
```

**Rotate the Anthropic key:**

```bash
nano ~/stare/docker/.env       # change ANTHROPIC_API_KEY=
docker compose -f docker/docker-compose.yml --env-file docker/.env up -d backend
```

**Tail logs:**

```bash
docker compose -f docker/docker-compose.yml logs --tail 200 backend
docker compose -f docker/docker-compose.yml logs --tail 200 caddy
```

**Back up the index** (cron-friendly):

```bash
aws s3 sync ~/stare/data/cached/chroma_db/ s3://stare-snapshots/$(date +%F)/
```

---

## 9. Troubleshooting

| Symptom                                | Likely cause                                | Fix                                                                                  |
|----------------------------------------|---------------------------------------------|--------------------------------------------------------------------------------------|
| `permission denied` running docker     | Group change not yet applied                | Log out and back in                                                                  |
| Cert error in browser                  | DNS not yet propagated, or ACME rate-limited | Wait 5 min, then `docker compose restart caddy`                                      |
| Backend `503 collection empty`         | data/cached/chroma_db/ missing or empty     | Re-run the rsync from step 4                                                         |
| Streamlit blank page                   | Frontend container restarting               | `docker compose logs frontend-app`                                                   |
| OOM kill on backend                    | t3.small is too small for embedding rebuild | Either don't rebuild on prod, or temporarily upsize to t3.medium                     |
