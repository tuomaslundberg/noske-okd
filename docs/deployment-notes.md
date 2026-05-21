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

**Issues resolved during Session 2:**
- `runAsUser: 1001` rejected — namespace UID range is `[1001230000, 1001239999]`; fix: remove `runAsUser`, keep `runAsNonRoot: true` only
- CPU limit:request ratio cap of 5× — raised request from 500m to 1 CPU
- Image architecture mismatch — built on Apple Silicon (arm64); cluster is x86_64; fix: `docker build --platform linux/amd64`
- GHCR image was private — made package public
- `BROWSER_URL_BONITO` had `/bonito` suffix — crystal appends `/bonito/run.cgi` itself; correct value is base URL only: `https://noske-turkunlp-noske-dev.apps.lumi-k.eu`

**Note on re-auth:** `oc` tokens expire (~24h). Re-authenticate via OKD web console → username → Copy login command. LUMI-K uses SSO so CLI-only re-auth is not possible.

---

## Next session plan — corpus loading

Three interlocking pieces; bucket creation unblocks the other two.

### A. LUMI-O bucket (prerequisite for everything)
- Enable LUMI-O at my.csc.fi if not already active (first-time setup)
- Create a bucket (e.g. `turkunlp-noske-corpora`)
- Configure rclone on LUMI-C with LUMI-O credentials
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
