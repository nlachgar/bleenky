# Bleenky website deployment

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

## Main marketing site

`marketing/` is the canonical source for https://bleenky.com/. The older `bleenky-website/upload/` package is an archive and does not sync automatically. The `site/` directory continues to serve https://demos.bleenky.com/.

The same workflow deploys demos first, then marketing. Both use the existing SSH secrets and deployment-enabled variable; no Hostinger GitHub app or extra secrets are needed. For marketing, `DEPLOY_SITE=marketing` requires the configured demo destination to be exactly `/home/USER/domains/bleenky.com/public_html/demos` and derives its parent as the root destination. Marketing uploads exclude `/demos/` and never delete remote files. Each destination has a separate changed-file backup directory outside the web root.

The main marketing site is public: `marketing/config.js` uses `reviewMode: false`, the inquiry email is hello@bleenky.com, the website-only offer is $29/month after 30 free days with no setup fee and cancellation anytime, and search indexing is enabled for the homepage, service guide, and privacy page. Preview banners are removed. A sitemap lists those three canonical URLs; demos and the 404 page retain noindex. Search engines decide when to crawl and index the site. Booking has separate scope and pricing. Trial dates and paid continuation are confirmed manually. The offer has no first-five customer limit. Billing and automated trials remain on hold. Demo links now use the branded subdomain; salon sign-in still uses the existing Sites platform.

Validate with `python3 scripts/validate.py --marketing`. Manual workflow runs default to dry-run for both destinations. Public verification checks the homepage, service guide, privacy page and 404 document. This does not constitute a new mobile/browser interaction audit. The root `.htaccess` sets the index and 404 handler without changing demo routing. Rollback by reverting the relevant source commit; deleting a newly introduced remote file still requires separate review.

## Fictional marketing demos

The marketing page and demo collection link to Marlow & Moss (`marlow-moss/`), Clovercoat (`clovercoat/`), and Puddle & Puff (`puddle-puff/`). These are invented demonstration brands with no real contact details. Original prospect-specific demos remain at their existing URLs but are not linked from the marketing collection. Marketing preview screenshots are rendered from the fictional versions.

## Interest form

Primary contact CTAs open a native dialog containing the interest form; hello@bleenky.com remains a secondary mailto link. The dialog supports Escape, backdrop/close-button dismissal, keyboard focus containment and return, draft preservation, and direct #contact links from other pages. It scrolls within the viewport on small screens; the page bottom contains a compact invitation rather than an embedded form. `marketing/contact.php` sends a fixed-recipient notification with the validated visitor address as Reply-To. Once private credentials are configured it uses authenticated Hostinger SMTP through PHPMailer, port 465 with certificate verification. Before initial setup only, it retains PHP mail. SMTP errors or invalid credentials never fall back to PHP mail. A successful send means the server accepted the message; inbox placement still needs testing. No SMTP password is stored in source.

The endpoint validates input, uses secure same-site session cookies and CSRF tokens, a honeypot, request-size limits and per-IP/global throttling. It stores only hashes and timestamps in a private `.bleenky-contact-state` directory outside the web root; old entries expire after one hour and are pruned on subsequent accepted submissions. No inquiry bodies are stored on disk by the app. Mail remains in the inbox under the owner's retention practices. Failed submissions preserve entered values and show a direct email fallback. `php scripts/test_contact.php` tests backend behavior without sending messages.


### Private SMTP setup

The Hostinger home directory `/home/u496265211/.bleenky-mail` has mode 0700. It contains PHPMailer dependencies, CLI-only `setup.php`, and (after activation) `config.json` with mode 0600. None are inside `public_html`; GitHub deployment does not touch them. `mail-runtime/composer.lock` records the installed dependency version. Never put credentials in Git, browser JavaScript, logs, command arguments, or chat.

From the local checkout, run `python3 scripts/configure_smtp.py` directly in Terminal. The helper uses hidden password prompts and sends the credentials through stdin over SSH with the existing pinned host key. Server setup tests TLS and SMTP authentication without sending email, then atomically saves the private config. A failed login leaves existing configuration intact. Rerun the helper after changing the mailbox password. After activation, submit one labeled inquiry through the live form and verify inbox placement and Reply-To.

Server recovery: create the private directory with mode 0700; copy `mail-runtime/composer.json` and `composer.lock` into it, then run `composer install --no-dev --no-plugins --no-scripts --prefer-dist` and `composer audit --no-dev` there. Copy `scripts/setup_smtp.php` to that directory as `setup.php` with mode 0600. Deploy the current contact endpoint before running the password helper. Do not place this directory in the public upload package. To pause sending, retain the config and disable the form; deleting the config returns to the pre-activation PHP-mail behavior.
