# Bleenky demo deployment

Dedicated repository for the three static grooming concepts. Edit `site/` here for future Hostinger deployments. This is a snapshot of the prepared upload package; edits to older workspace copies do not automatically sync into this repository.

The booking interactions remain simulated. No live dashboard, customer records, prospect research, credentials or database is included.

## One-time connection

1. Repository: `nlachgar/bleenky` (public, selected by the owner). This directory contains only demo source and deployment tooling. Do not push the whole parent Bleenky workspace.
2. In Hostinger, confirm your plan supports SSH/rsync, enable SSH Access and select the actual destination for the demos. Create that destination directory if necessary. Back up any existing site before first deployment.
3. Create a dedicated SSH deployment key pair. Add its public key to the Hostinger account's authorized SSH keys. Save its private key only as the GitHub Actions secret below; never commit it or paste it into chat.
4. Obtain the server's known_hosts entry and compare its fingerprint with the fingerprint in Hostinger's SSH Access panel. `ssh-keyscan -p PORT HOST` can collect the entry, but independently confirm the fingerprint before trusting it. Nonstandard ports appear as `[HOST]:PORT` in known_hosts.
5. Under GitHub repository **Settings → Secrets and variables → Actions**, configure the following.

| Type | Name | Value |
| --- | --- | --- |
| Secret | `HOSTINGER_HOST` | SSH hostname or IP from hPanel |
| Secret | `HOSTINGER_USER` | SSH account username |
| Secret | `HOSTINGER_PORT` | Port from hPanel (often 65002; confirm it) |
| Secret | `HOSTINGER_SSH_KEY` | Complete private deployment key |
| Secret | `HOSTINGER_KNOWN_HOSTS` | Verified SSH known_hosts entry |
| Variable | `HOSTINGER_TARGET_DIR` | Exact existing absolute destination directory |
| Variable | `DEMO_BASE_URL` | `https://demos.bleenky.com/` (selected destination) |
| Variable | `HOSTINGER_DEPLOY_ENABLED` | Leave unset until the destination and credentials are ready, then set `true` |

Example destination: `/home/u123456789/domains/bleenky.com/public_html/demos`. Use your actual hPanel path, not this example. A separately configured demo subdomain may have a different root. Never target the main marketing homepage unless deliberately replacing it.

6. Set `HOSTINGER_DEPLOY_ENABLED=true`, then immediately run **Actions → Validate and deploy demos → Run workflow** on `main`, leaving **dry_run checked**. Avoid pushing other changes to main during initial configuration. Inspect the proposed transfers and destination.
7. Run it again with **dry_run unchecked** for the first upload. Check all four public pages, images, mobile layout and simulated booking flow.

## Ongoing changes

- Edit the HTML/CSS/JavaScript/images in `site/`.
- Develop on a `codex/…` branch. Pull requests validate assets and JavaScript but cannot deploy.
- Merge approved changes into `main`; GitHub automatically uploads changed files after validation.
- To stop automatic deployment, set `HOSTINGER_DEPLOY_ENABLED=false`.
- Manual runs default to dry-run and do not change the website.

## Checks and recovery

Run `python3 scripts/validate.py` locally. The workflow also uses `node --check` for JavaScript syntax. SSH host identity is verified; private key files exist only in a temporary runner directory. Successful uploads are checked against all four public HTML files.

The transfer preserves unrelated files and does not delete remote files. Consequently, intentionally removing or renaming a page requires separately removing its old remote copy after review. Replaced files are saved outside the web root under `~/.bleenky-deploy-backups/`, grouped by destination and workflow run. These are changed-file backups, not full site backups.

For normal content rollback, revert the unwanted Git commit on main; the next deployment restores the old tracked content. Newly added remote files are not automatically removed. An upload is not a fully atomic site swap; failed uploads or live verification failures require checking the site before retrying. No database changes are performed.

## Current setup status

Deployment is connected and enabled for `https://demos.bleenky.com/`. On November 20, 2026, the GitHub Actions dry run and live deployment succeeded, including all four public HTML checks. Changes pushed to `main` now validate and deploy automatically. See [the first successful live run](https://github.com/nlachgar/bleenky/actions/runs/44809330824).

References: [Hostinger SSH setup](https://www.hostinger.com/support/1583645-how-to-enable-ssh-access-in-hostinger/), [Hostinger rsync](https://www.hostinger.com/support/how-to-use-rsync-to-sync-files-and-directories-at-hostinger/), [GitHub Actions secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets).
