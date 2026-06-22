# LUMI-K / NoSketchEngine Deployment — Session Handoff Prompt

## Who you are talking to

Tuomas is an NLP researcher at TurkuNLP. He has completed two hands-on sessions covering OKD platform verification, image patching, and a full manifest deployment cycle. He is technically strong (NLP/ML background, familiar with HPC/CSC infrastructure), prefers concise and professional responses, and wants genuine understanding — not just things that work. Follow the "explain before you apply" principle: briefly explain the K8s/OKD concept each new object instantiates before writing it.

---

## The project

Deploying **NoSketchEngine** (a corpus query web interface) on **LUMI-K** as a **Fin-CLARIAH deliverable**. Externally accessible, persistent, maintainable.

**Deliverable deadline:** November 2026 (exact slot TBC). No urgency, but steady progress expected.

---

## Session 1 progress (2026-04-23) — completed

**Platform verified:**
- `oc` CLI installed; authenticated to `https://api.v1.lumi-k.eu:6443` as `tlundber`
- Storage classes confirmed: `rook-ceph-fs` (CephFS, RWX) ✅, `rook-ceph-block` (default, RWO), `lvms-local` (RWO, no replication)
- Dev namespace `turkunlp-noske-dev` created (throwaway; linked to project 462000999)
- LimitRange auto-applied: container defaults 1 CPU / 2 GiB RAM; max 8 CPU / 16 GiB RAM / 100 GiB per PVC
- No ResourceQuota in dev namespace
- Admission webhook requires `lumi_project: XXXXXXXX` in namespace description field

**OKD non-root image patch — done:**
- Patch files: `projects/noske-okd/Dockerfile.okd` + `projects/noske-okd/run_lighttpd.sh`
- Patch: `chown 0:0 + chmod g=u` on all runtime-writable dirs; `chmod g=u /etc/passwd`; entrypoint UID injection
- Validated locally: `docker run --user 12345` — lighttpd started clean, served on 8080 ✅
- Patched image pushed to `ghcr.io/tuomaslundberg/noske-okd:latest`

**Production namespace:** pending new LUMI project allocation (old project 462000999 CPU quota exhausted on HPC side — LUMI-K itself unaffected). Tuomas to ask Veronika.

---

## Session 2 progress (2026-04-27) — completed

**All 5 manifests written, applied, and validated. App is live.**

- `manifests/01-pvc.yaml` — 10 GiB CephFS PVC for corpus data ✅
- `manifests/02-configmap.yaml` — manatee registry for placeholder corpus "test" ✅
- `manifests/03-deployment.yaml` — init container compiles dummy corpus; main NSE container ✅
- `manifests/04-service.yaml` — ClusterIP on port 8080 ✅
- `manifests/05-route.yaml` — Edge TLS Route, auto-TLS ✅

**Live URL:** `https://noske-turkunlp-noske-dev.apps.lumi-k.eu`

**Dev verification (2026-06-03):** 6/6 checks pass — see `docs/verify-prompt-result.md`. Corpus: 4.1M words, real Finnish text. Concordance, wordlist, and structural attribute filtering (`lang="fin_Latn"`) all functional. ~59% of docs are fin_Latn (expected; HPLT shard is multilingual).

**Issues resolved during Session 2:**
- `runAsUser: 1001` rejected — namespace UID range is `[1001230000, 1001239999]`; fix: remove `runAsUser`, keep `runAsNonRoot: true` only
- CPU limit:request ratio cap of 5× — raised request from 500m to 1 CPU
- Image architecture mismatch — built on Apple Silicon (arm64); cluster is x86_64; fix: `docker build --platform linux/amd64`
- GHCR image was private — made package public
- `BROWSER_URL_BONITO` had `/bonito` suffix — crystal appends `/bonito/run.cgi` itself; correct value is base URL only: `https://noske-turkunlp-noske-dev.apps.lumi-k.eu`

**Note on re-auth:** `oc` tokens expire (~24h). Re-authenticate via OKD web console → username → Copy login command. LUMI-K uses SSO so CLI-only re-auth is not possible.

---

## Session 3 progress (2026-06-03) — complete ✅

**Fully deployed and live.**

**New files:**
- `scripts/to_vert.py` — converts HPLT v3 JSONL to manatee vertical (whitespace tokenization; doc metadata: id, lang, url)
- `scripts/compile_and_upload.sh` — end-to-end wrapper: generate vert → Apptainer compilecorp → rclone upload
- `registry/hplt_toy` — manatee registry source of truth (mirrored into ConfigMap)
- `manifests/00-secret.yaml` — K8s Secret template for LUMI-O credentials (gitignored; fill before applying)

**Modified files:**
- `Dockerfile.okd` — added rclone RPM install (needed in init container)
- `manifests/02-configmap.yaml` — replaced "test" registry with hplt_toy
- `manifests/03-deployment.yaml` — init container now downloads pre-compiled corpus from LUMI-O via rclone; Secret env injection; CORPLIST → "hplt_toy"

**HPLT v3 JSONL format note:** Each JSONL line is a shard record `{filename, documents: [...]}`. Doc fields are abbreviated: `u`=URL, `lang`=list (primary first), `id`=doc ID, `text`=body. First shard has 1198 docs.

**Image rebuild required before applying manifests:**
```bash
docker build --platform linux/amd64 -t ghcr.io/tuomaslundberg/noske-okd:latest -f Dockerfile.okd .
docker push ghcr.io/tuomaslundberg/noske-okd:latest
```

**Infrastructure notes from session 3:**
- `singularity` is at `/usr/bin/singularity` on LUMI-C; no module load needed (`apptainer` not available)
- `oc` installed to `~/.local/bin/` on LUMI-C; manifests applied from LUMI directly
- LUMI-O bucket `turkunlp-noske-corpora` created and populated
- LUMI-O keys valid until 2027-05-25; stored in `manifests/00-secret.yaml` (gitignored)

---

## Session 4 (2026-06-23) — complete ✅

**Production deployment live.**

- **Prod namespace:** `turkunlp-noske-prod` (LUMI project 462001491, lifetime to 2027-05-28)
- **Prod URL:** `https://noske-turkunlp-noske-prod.apps.lumi-k.eu`
- **Corpus:** `hplt_toy` (placeholder; real corpora load post-vacation)
- **LUMI-O:** new bucket `turkunlp-noske-corpora` under project 462001491; `hplt_toy` copied from 462000999 bucket
- **Verification:** 6/6 checks pass

**Infrastructure notes:**
- `oc new-project` with `--description` flag handles admission webhook — no web console needed
- Prod secret (`manifests/prod/00-secret.yaml`) is gitignored; namespace field must match prod namespace (gotcha: copying from dev template leaves `turkunlp-noske-dev` — fix before applying)
- LUMI-O keys for 462001491 generated at my.csc.fi; configured via `module load lumio && lumio-conf`

---

## Sprint: Go live — load real corpora (post-vacation)

**Gate:** Corpus selection meeting with Erik and Veronika. Prod namespace is already running with `hplt_toy`; this sprint is a data operation on the live instance, not a new deployment.

### Steps per corpus
1. `scripts/compile_and_upload.sh` — generates vertical, compiles via Singularity, uploads to LUMI-O
2. Add registry entry to `manifests/prod/02-configmap.yaml`; add corpus name to `CORPLIST`
3. `oc apply -f manifests/prod/02-configmap.yaml manifests/prod/03-deployment.yaml`
4. `oc rollout restart deployment/noske -n <prod-ns>`
5. Verify with Chrome extension

---

## Previous session plan — corpus loading (completed Session 3)

Three interlocking pieces; bucket creation unblocks the other two.

### A. LUMI-O bucket (prerequisite for everything)
1. On LUMI-C, configure rclone (keys already generated — have access-key-id and secret-access-key ready from `00-secret.yaml`):
   ```bash
   module load lumio
   lumio-conf   # follow prompts; paste project number + keys when asked
   ```
   This writes `~/.config/rclone/rclone.conf` with remote `lumi-462000999-private`.
2. Create the bucket from LUMI-C:
   ```bash
   rclone mkdir lumi-462000999-private:turkunlp-noske-corpora
   ```
3. Verify:
   ```bash
   rclone lsd lumi-462000999-private:
   ```
- **Start here.**

### B. OKD side (can proceed once bucket + credentials exist)
- New manifest `manifests/00-secret.yaml` — K8s Secret holding LUMI-O access key + secret key
- Update `manifests/03-deployment.yaml` init container: replace dummy `compilecorp` block with
  `rclone copy s3:turkunlp-noske-corpora/<corpname>/ /var/lib/manatee/data/<corpname>/`
- Keep the "skip if PVC already populated" guard — restarts should not re-copy
- Update ConfigMap (`02-configmap.yaml`) with real corpus name replacing "test"
- Update `CORPLIST` env var in Deployment

### C. Corpus compilation on LUMI-C (parallel to B; best done in a VSCode remote session)
- **HPLT paths TBD** — Tuomas to locate the ~1M-per-lang HPLT samples on LUMI scratch
  before starting this track. Likely under `/scratch/project_462000999/tlundber/`.
- Steps once paths are known:
  1. Write a minimal manatee registry file for the chosen corpus
  2. Run `compilecorp --no-ske <corpname> <vertfile>` on LUMI-C
  3. Upload compiled corpus dir to LUMI-O bucket with rclone

### Remaining hardening (later)
- [ ] Custom domain + TLS if needed
- [ ] PVC deletion protection
- [ ] Production namespace under new LUMI project (ask Veronika)
- [ ] Fin-CLARIAH deliverable report (template: projects/fin-clariah-deliverable-report-template.txt)

---

## Key facts

- **Image:** `ghcr.io/tuomaslundberg/noske-okd:latest` (public GHCR, x86_64)
- **Port:** 8080 (lighttpd)
- **Corpus data mount:** `/var/lib/manatee/data` — PVC (`noske-corpus`, rook-ceph-fs)
- **Registry config mount:** `/var/lib/manatee/registry` — ConfigMap (`noske-registry`)
- **Env vars:** `CORPLIST` (space-separated corpus names), `BROWSER_URL_BONITO` (base URL — no `/bonito` suffix)
- **UID range:** `[1001230000, 1001239999]` — do not pin `runAsUser`
- **CPU ratio cap:** 5× limit:request
- **PVC max:** 100 GiB per LimitRange

---

## Related files

- `nosketchengine-lumi-k-feasibility.md` — full feasibility doc
- `projects/noske-okd/Dockerfile.okd` — OKD image patch
- `projects/noske-okd/run_lighttpd.sh` — patched entrypoint
- `projects/noske-okd/manifests/` — all 5 manifests
- `projects/fin-clariah-deliverable-report-template.txt` — deliverable report template
