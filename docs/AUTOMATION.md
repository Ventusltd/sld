# Publication and autonomous refresh

`pages.yml` validates the source files against their checked-in hashes, regenerates
the deterministic catalogue, verifies the exact GPU receipt, builds the allowlisted
static site, and tests it in Chromium. Only a successful `main` run can deploy.
Pull requests run on GitHub-hosted machines and cannot publish. The hosted workflow
does not claim to run CUDA: it checks the receipt produced on the local GPU.

The receipt binds the library, source lock, furnace program, and photon output
with SHA-256. The verifier checks component identity and dimensions, independent
channels, CPU reference sample count, threshold fixtures, injected-error detection,
unique gap domains, complete classification counts, and zero disagreements.
These are declared bounding-box layout checks, not electrical certification.
Hash receipts bind inputs; they are not a cryptographic attestation of GPU execution.

## Local controller

Run with the existing Python environment containing NumPy and CuPy:

```powershell
powershell.exe -NoProfile -File scripts/refresh_local.ps1 `
  -Repository C:\path\to\sld `
  -OutputRoot E:\path\to\sld-refresh `
  -Python E:\path\to\venv\Scripts\python.exe
```

The controller requires a clean `main` checkout with the exact `Ventusltd/sld`
origin. It fast-forwards, creates an isolated candidate worktree on the output
drive, verifies pinned downloads, rebuilds, and tests. A missing or stale furnace
receipt triggers a new bounded GPU run. `-ForceFurnace` explicitly reruns an
unchanged input set. Only validated generated outputs enter the commit. An ordinary
push rejects concurrent changes; it never force-pushes. GitHub Actions then tests
the website and publishes without another manual step.

Schedule the command hourly in Windows Task Scheduler using the existing logged-on
user and existing Git credentials. Set “Do not start a new instance” and a bounded
execution limit. The controller also takes an exclusive filesystem lock. No runner
service, new credentials, or security setting changes are required. Output consists
of one temporary candidate worktree and one bounded furnace result directory;
the worktree is removed in `finally`, and results are overwritten on the next run.

Pinned upstream URLs and hashes are deliberately not upgraded autonomously. A
changed upstream download fails closed and requires a reviewed manifest/lock update.
Trusted commits changing inputs trigger GPU regeneration at the next local run.
Unchanged accepted inputs produce no commit and no repeated GPU work. Failed fetch,
test, furnace, build, push, or hosted browser checks leave the last successful Pages
deployment live. Check the scheduled task's last result and GitHub Actions for failures.
The task only runs while the configured user/machine is available.

Publication uses the [GitHub Pages custom workflow contract](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
The repository Pages source must be configured to GitHub Actions. No self-hosted
runner is configured by this repository; the local controller executes trusted main
only, never pull-request code.
