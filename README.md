# Hackerspace Drenthe website

Content and config for [hackerspace-drenthe.nl](https://www.hackerspace-drenthe.nl), a
[Grav CMS](https://getgrav.org/) site. Grav core
itself is **not** in this repo — it comes from the `lscr.io/linuxserver/grav` Docker image.
Everything here lives under `user/`, the directory Grav reserves for site content, config, themes
and plugins.

## Running locally

```sh
docker compose -f docker-compose-dev.yml up
```

Open [http://localhost:8080](http://localhost:8080).

- Bind-mounts `./user` into the container, so edits to `user/pages`, `user/config`, etc. show up
  on refresh — no rebuild needed (clear the Grav cache from the admin panel if a change doesn't
  appear).
- `user/data` and `user/accounts` (runtime/generated data) use named Docker volumes instead, kept
  out of the repo.

`docker-compose.yml` (no `-dev`) is the **production** file — builds an image with `user/` baked
in and wires up Traefik + SMTP. Don't use it for local testing.

## `user/pages` structure

Grav has no database — every page is a folder on disk.

```
user/pages/
├── 01.home/
│   ├── default.md            # content + YAML frontmatter
│   └── featured-home.jpg     # image used by the page
├── 02.organisatie/
│   ├── default.md
│   └── 01.wat-is-een-hackerspace/   # child page/route
│       └── default.md
├── 03.nieuws/
│   ├── default.md            # the news listing page
│   ├── 001.some-article/
│   │   └── default.md        # one article per numbered folder
│   └── ...
├── 04.projecten/             # promoted community projects
├── 05.werkplaats/             # workshop and facilities
├── 06.lidmaatschap/
├── 07.contact/
└── 08.wiki/                  # imported wiki content
```

- **One folder per page.** Folder name (minus numeric prefix) becomes the URL slug, e.g.
  `05.werkplaats/` → `/werkplaats/`.
- **Leading number = sort order only**, not part of the URL. Keep sibling prefixes unique. The
  main-menu order is Nieuws, Projecten, Werkplaats, Lidmaatschap, Contact.
- **`default.md`** = content file: YAML frontmatter (`title`, `menu`, `visible`, `lead_image`,
  ...) then Markdown/HTML body.
- **Images sit next to the `default.md` that uses them**, optionally under an `images/` subfolder
  for pages with many assets.
- **Nested folders = nested pages** (child routes). `03.nieuws` uses this for every article.
- **`visible: false`** hides a page from menus without deleting it.

Other folders under `user/`: `config/` (site YAML config + `security-private.php`, untracked,
never commit it), `themes/` (Twig theme), `plugins/` (installed plugins), `accounts/`/`data/`
(runtime data, git-ignored).

## Forgot your local admin password

Admin accounts are stored in the `accounts` named volume, not in the repo. Reset it by removing
that volume and letting Grav's setup flow recreate an account:

```sh
docker compose -f docker-compose-dev.yml down
docker volume ls | grep accounts        # find the volume name, e.g. hackerspace-drenthe-nl_accounts
docker volume rm <name-from-above>
docker compose -f docker-compose-dev.yml up
```

This only wipes local admin accounts — it doesn't touch `user/pages` or anything else in the repo.
Grav will prompt you to create a new admin account on next login.

## Automated checks

GitHub Actions runs on every pull request and push. It checks for duplicate Grav routes, broken
local Markdown/HTML links, missing local media, and invalid redirects. On pull requests, changed
visible pages with `source_url` migration metadata must have `status: approved`, `reviewed_by`,
and `reviewed_at` set.

Run the site checks locally:

```sh
python3 scripts/validate_site.py
python3 scripts/wiki_migration/validate_wiki_migration.py --wiki-root user/pages/08.wiki
python3 scripts/check_live_news_duplicates.py http://localhost:8080
```

## Upgrading

- **Plugins/themes**: upgrade via the Grav admin backend as normal — they live in `user/`, so
  changes are picked up and should be committed.
- **Grav core**: do *not* upgrade via the backend. The image is pinned by digest in `Dockerfile`
  and `docker-compose-dev.yml`. Update that digest deliberately in a pull request, then run local
  smoke tests and CI before merging.

## Deploy guard (prevent duplicate news after renames)

When news folders are renumbered/renamed, a deploy method that only copies files (without deleting
removed paths) can leave stale folders on the server. Grav then sees both old and new folders,
which can duplicate items.

Use a deploy sync with delete semantics and clear cache after deploy.

```sh
LIVE_HOST=user@server \
LIVE_PATH=/opt/www.hackerspace-drenthe.nl \
./scripts/deploy_with_delete_example.sh
```

To verify live output quickly:

```sh
python3 scripts/check_live_news_duplicates.py https://hackerspace-drenthe.nl
```

Expected output after a healthy deploy:

- `NEWS_DUPLICATE_ROUTES=0`