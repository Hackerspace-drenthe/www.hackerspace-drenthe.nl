# Vandaag lokaal uitvoeren

## Stap 1 - XML en media klaarzetten

- Zet de MediaWiki XML export op een lokale padlocatie.
- Optioneel: zet geëxporteerde mediafiles in een aparte map.

## Stap 2 - Eerste controle met dry-run

python3 scripts/wiki_migration/migrate_mediawiki_to_grav.py \
  --xml /pad/naar/wiki-export.xml \
  --out-root user/pages/08.wiki \
  --source-base-url https://wiki.hackerspace-drenthe.nl/wiki \
  --dry-run

Controleer:

- INCLUDED_CONTENT_PAGES
- EXCLUDED_PAGES
- MISSING_IMAGES

## Stap 3 - Werkelijke migratie

python3 scripts/wiki_migration/migrate_mediawiki_to_grav.py \
  --xml /pad/naar/wiki-export.xml \
  --out-root user/pages/08.wiki \
  --source-base-url https://wiki.hackerspace-drenthe.nl/wiki \
  --media-dir /pad/naar/wiki-media

## Stap 4 - Lokale validatie

python3 scripts/wiki_migration/validate_wiki_migration.py \
  --wiki-root user/pages/08.wiki

## Stap 4b - Ontbrekende media ophalen via API

Als je bij stap 4 missing images ziet:

python3 scripts/wiki_migration/download_wiki_media.py \
  --wiki-root user/pages/08.wiki

Draai daarna stap 4 opnieuw.

## Stap 4c - Subpagina-indexen verversen

Na herindeling in submappen:

python3 scripts/wiki_migration/index_wiki_children.py \
  --wiki-root user/pages/08.wiki

Draai daarna stap 4 opnieuw.

## Stap 5 - Handmatige correctieronde

- Corrigeer inhoud waar nodig.
- Zet status op approved voor gereviewde pagina's.
- Vul reviewed_by en reviewed_at in.

## Stap 6 - Strenge eindvalidatie

python3 scripts/wiki_migration/validate_wiki_migration.py \
  --wiki-root user/pages/08.wiki \
  --require-approved

## Stap 7 - Voorbereiden grote PR

- Voeg migratierapport toe uit _migration map.
- Voeg aantallen toe: gemigreerd, uitgesloten, missing images opgelost.
- Vraag bestuurlijke go/no-go review aan.
