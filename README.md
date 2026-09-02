# Hackerspace Drenthe Website

This repository contains the Grav-based website for Hackerspace Drenthe:

- Production site: https://www.hackerspace-drenthe.nl
- CMS: Grav 2.x
- Theme: Quark2 (customized)

## Purpose

This project is the migrated and customized website from the original WordPress content, including:

- Static pages (home, organisatie, werkplaats, lidmaatschap, contact)
- News archive and news detail pages
- Homepage events block based on event dates in news posts
- Localized media assets for stable image rendering

## Requirements

- PHP 8.3+
- Standard Grav PHP extensions (including gd)

## Local Development

Run all commands from the Grav root folder:

```bash
cd /path/to/grav-admin
```

Start local server:

```bash
php -S 127.0.0.1:8001 system/router.php
```

Open:

- Site: http://127.0.0.1:8001
- Admin: http://127.0.0.1:8001/admin

Clear cache after content/template changes:

```bash
php bin/grav clearcache
```

## Content Structure

- Main pages: user/pages
- News landing page: user/pages/03.nieuws/default.md
- News items: user/pages/03.nieuws/<item>/default.md
- Theme templates: user/themes/quark2/templates
- Theme styles: user/themes/quark2/css/theme.css

## Events on Homepage

The homepage renders an events block using news items.

Used fields in a news item frontmatter:

- nieuwsdatum: event start date (YYYY-MM-DD)
- nieuwsdatum_eind: optional event end date (YYYY-MM-DD)

Behavior:

- Single-day event: shown from nieuwsdatum onward.
- Multi-day event: shown until nieuwsdatum_eind.

Example:

```yaml
nieuwsdatum: "2026-10-01"
nieuwsdatum_eind: "2026-10-31"
```

## Image Conventions

To keep images stable and visible across pages:

- Generic pages can define lead_image in frontmatter.
- News overview uses card images from page media.
- News cards fallback to a default news image when an item has no local card image.
- News page hero can be set with hero_image.

Recommended per-page media setup:

- Put featured page image in the page root folder.
- Keep inline article images under the page folder (root or images subfolder).

## Git Branches

- Active collaboration branch: main
- Default branch on remote: master

If both branches must stay aligned, push both explicitly when releasing.

## Upstream Grav Documentation

General Grav docs are available at:

- https://learn.getgrav.org

## License

See LICENSE.txt.
