# Wiki migratie lokaal

Deze map bevat tooling om contentpagina's uit een MediaWiki XML export lokaal naar Grav te migreren.

## Scope

- Alleen contentpagina's uit de hoofdnamespace (ns=0).
- Beheer- en systeempagina's worden uitgesloten.
- Pagina's worden als draft aangemaakt voor review/correctie.

## Bestanden

- migrate_mediawiki_to_grav.py: converteert XML naar Grav pagina's.
- validate_wiki_migration.py: valideert links, assets en frontmatter.
- download_wiki_media.py: haalt ontbrekende mediafiles op via de wiki API.
- index_wiki_children.py: maakt/ververst automatische subpagina-indexen in parent default.md en slaat pagina's over die al in de tekst erboven genoemd worden.

## 1) Dry-run

Voer eerst een dry-run uit om aantallen te controleren:

python3 scripts/wiki_migration/migrate_mediawiki_to_grav.py \
  --xml /pad/naar/wiki-export.xml \
  --out-root user/pages/08.wiki \
  --source-base-url https://wiki.hackerspace-drenthe.nl/wiki \
  --dry-run

## 2) Echte migratie

python3 scripts/wiki_migration/migrate_mediawiki_to_grav.py \
  --xml /pad/naar/wiki-export.xml \
  --out-root user/pages/08.wiki \
  --source-base-url https://wiki.hackerspace-drenthe.nl/wiki

Als je media lokaal hebt geëxporteerd:

python3 scripts/wiki_migration/migrate_mediawiki_to_grav.py \
  --xml /pad/naar/wiki-export.xml \
  --out-root user/pages/08.wiki \
  --source-base-url https://wiki.hackerspace-drenthe.nl/wiki \
  --media-dir /pad/naar/wiki-media

## 3) Validatie

python3 scripts/wiki_migration/validate_wiki_migration.py \
  --wiki-root user/pages/08.wiki

## 4) Ontbrekende media automatisch ophalen

Als je geen losse media-export hebt, kun je ontbrekende media direct downloaden:

python3 scripts/wiki_migration/download_wiki_media.py \
  --wiki-root user/pages/08.wiki

## 5) Subpagina-indexen bijwerken na herstructurering

Als je pagina's naar submappen verplaatst, update dan automatisch de index in parent-pagina's:

python3 scripts/wiki_migration/index_wiki_children.py \
  --wiki-root user/pages/08.wiki

Na redactionele review kun je streng valideren op approved status:

python3 scripts/wiki_migration/validate_wiki_migration.py \
  --wiki-root user/pages/08.wiki \
  --require-approved

## Output

Migratie schrijft rapporten naar:

- user/pages/08.wiki/_migration/migration_report.json
- user/pages/08.wiki/_migration/redirects.csv

Deze kun je gebruiken voor PR-onderbouwing en redirect-inrichting.
