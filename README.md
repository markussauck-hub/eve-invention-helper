# EVE Invention Helper

Web-Version des Invention Helpers (gleicher Stand wie die Desktop-Version):
Blueprint wählen → benötigte Datacores, Erfolgschance inkl. Decryptor, Skills,
Bauteile des T2-Items und die Materialien zum Bauen der Bauteile – jeweils mit
Multibuy-Knopf für den EVE-Markt. Look & Feel: LincolnSoft-Styleguide mit
Nebel- und Sternenhintergrund.

## Aufbau

| Datei | Zweck |
|---|---|
| `index.html` | Die komplette Seite (HTML/CSS/JS, keine Abhängigkeiten) |
| `build_data.py` | Lädt den Fuzzwork-SDE-Dump und erzeugt `invention.json` |
| `.github/workflows/pages.yml` | Baut die Daten und veröffentlicht auf GitHub Pages – bei jedem Push, jeden Dienstag und manuell |

`invention.json` wird **nicht** eingecheckt, die Action baut sie bei jedem Deploy frisch.
Nach einem EVE-Patch aktualisiert sich die Seite also spätestens am nächsten Dienstag von allein.

## Einrichtung (einmalig)

1. Auf GitHub ein neues **öffentliches** Repository anlegen, z. B. `eve-invention-helper`.
2. Alle Dateien hochladen – inklusive `.github/workflows/pages.yml`.
   Der Web-Upload ignoriert den versteckten Ordner `.github` manchmal. Dann die Datei über
   *Add file → Create new file* mit genau dem Pfad `.github/workflows/pages.yml` anlegen.
3. **Settings → Pages → Build and deployment → Source: „GitHub Actions"** auswählen.
4. Tab **Actions** → Workflow „Build & Deploy" → *Run workflow*.
5. Nach ca. 1–2 Minuten ist die Seite erreichbar unter
   `https://<dein-github-name>.github.io/eve-invention-helper/`

## Lokal testen

```bash
python build_data.py              # erzeugt ./invention.json
python -m http.server 8000        # dann http://localhost:8000 öffnen
```

Per Doppelklick (`file://`) funktioniert die Seite nicht, weil der Browser dann
`invention.json` nicht laden darf.

## Bedienung

- Suche nach T1-BP, T2-BP oder Produktname, mehrere Begriffe möglich.
- **Enter** wählt den ersten Treffer, **↑ / ↓** blättert durch die Liste.
- **Bauteile → Spalte BAU:** festlegen, was du selbst baust. Standard: T2-Komponenten bauen,
  R.A.M. und das T1-Item kaufen. Die Auswahl gilt für alle Blueprints.
- Tags: **SALVAGE** (Bergungsmaterial), **PI** (Planetary Interaction), **KAUFEN** (nicht baubar bzw. abgewählt).
- Skill-Level, Decryptor, Anzahl Jobs, Komponenten-ME und Bau-Auswahl werden im Browser gespeichert.
- Oben mittig: Wechsel zum [EVE Price Checker](https://markussauck-hub.github.io/eve-price-checker/) – das T2-Produkt wird gleich mitgenommen.
- Jeder Blueprint hat einen Direktlink, z. B. `…/#39581` für Hammerhead II.
- Struktur- und Rig-Boni sind nicht eingerechnet.

## Datenquelle

[Fuzzwork SDE-Dump](https://www.fuzzwork.co.uk/dump/latest/csv/) (CSV).
EVE Online und alle zugehörigen Inhalte © CCP hf.
