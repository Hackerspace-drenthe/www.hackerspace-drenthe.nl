---
title: "Zelf een nieuwsbericht toevoegen"
menu: "Nieuwsbericht toevoegen"
visible: true
template: handleiding
process:
  markdown: true
  twig: false
---

# Zelf een nieuwsbericht toevoegen

Wil je een activiteit, project of ander nieuws delen op de website? Dat kan met een
pull request (PR). Een PR is een voorstel om jouw bericht aan de website toe te voegen.
Je hoeft de website niet zelf te kunnen bouwen.

## 1. Maak een eigen kopie van de website

1. Ga naar <https://github.com/Hackerspace-drenthe/www.hackerspace-drenthe.nl>.
2. Klik rechtsboven op **Fork** en daarna op **Create fork**.
3. Je hebt nu een eigen kopie van de website op GitHub.

## 2. Maak een bestand voor je bericht

1. Open in jouw kopie de map `user/pages/03.nieuws/`.
2. Kijk naar het hoogste nummer van de bestaande berichten. Het volgende nummer is
   voor jouw bericht. Is het hoogste nummer bijvoorbeeld `046`, gebruik dan `047`.
3. Klik op **Add file** en kies **Create new file**.
4. Geef het bestand een naam zoals
   `user/pages/03.nieuws/047.naam-van-je-bericht/default.md`.
   Gebruik kleine letters en streepjes in de mapnaam.
5. Plak de tekst hieronder en vervang de voorbeeldtekst:

```markdown
---
title: "Open avond in Emmen"
menu: "Open avond in Emmen"
visible: true
template: item
date: "2026-11-23T12:00:00"
publish_date: "2026-11-23T12:00:00"
nieuwsdatum: "2026-12-05"
taxonomy:
  category:
    - nieuws
process:
  markdown: true
  twig: false
---
Kom op zaterdag 5 december naar onze open avond in Emmen!

We beginnen om **19.30 uur**. Iedereen is welkom.

## Waar?

Hackerspace Drenthe in Emmen.

## Vragen?

Stuur ons een [e-mail](mailto:info@hackerspace-drenthe.nl).
```

### Wat moet je aanpassen?

- `title` is de titel van je bericht. Zet de titel tussen aanhalingstekens.
- `menu` mag hetzelfde zijn als `title`.
- `date` en `publish_date` zijn de datum en tijd waarop je het bericht schrijft.
  Gebruik de vorm `jaar-maand-dagTuur:minuut:seconde`.
- `nieuwsdatum` is de datum van de activiteit of het nieuws, in de vorm `jaar-maand-dag`.
- De tekst onder de tweede `---` is je bericht. Je kunt tussenkopjes maken met `##`,
  tekst vet maken met `**sterretjes**` en een link schrijven als
  `[linktekst](https://example.com)`; vervang dit voorbeeldadres door de echte URL.

Gebruik voor een gewone aankondiging de datum van de activiteit bij `nieuwsdatum`.
Gaat je bericht niet over een activiteit op een bepaalde dag? Gebruik dan de datum
waarop het nieuws plaatsvond.

## 3. Sla je bestand op

Scrol naar **Commit changes**. Schrijf bijvoorbeeld `Voeg nieuwsbericht toe` als
toelichting en klik op **Commit changes**. Kies de optie om dit in een nieuwe branch
te zetten en maak daarna de pull request aan.

## 4. Open een pull request

1. Klik op **Contribute** en daarna op **Open pull request**. Soms staat er meteen
   een knop **Compare & pull request**.
2. Geef je PR een korte titel, bijvoorbeeld `Voeg nieuwsbericht over open avond toe`.
3. Schrijf eventueel extra informatie en klik op **Create pull request**.

De PR is nu een voorstel voor de beheerders van de website. Zij kunnen vragen om iets
aan te passen. Je kunt dat doen in dezelfde branch; de PR wordt dan vanzelf bijgewerkt.
Na goedkeuring en samenvoegen verschijnt het bericht op de website.

## Goed om te controleren

- Controleer de spelling, datum, tijd en locatie.
- Gebruik het volgende vrije nummer voor de map.
- Zet het hele bericht in `default.md`.
- Laat de regels bovenaan met `---` staan: daar staan gegevens die de website nodig heeft.
- Heb je een foto? Vraag eerst toestemming om die te gebruiken. Een foto kan als extra
  bestand in dezelfde map worden toegevoegd. Vermeld in je PR dat er een foto bij zit.
