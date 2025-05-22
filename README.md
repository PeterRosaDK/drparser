# JSON til SRT-konverter

Dette Python-script er et GUI-værktøj skrevet med PyQt5, der gør det muligt at konvertere talegenkendelsesdata i JSON-format (f.eks. fra Speechmatics) til undertekster i SRT-format.

## 🧠 Funktioner

- 🎯 Indlæs JSON-filer manuelt eller via drag’n’drop
- 📊 Udregner gennemsnitlig confidence score for **alle** ord (inkl. 1.0)
- 👀 Viser JSON-input og genereret SRT-output i realtid
- 👯‍♂️ Sammenlægger undertekster fra samme speaker, hvis de er tæt nok (≤ 7 sek.)
- 💾 Gem SRT direkte fra GUI’en
- 📝 Tilføjer metadata (filnavn, sprog, konfiguration, confidence) som første blok i underteksten

## 🚀 Sådan bruger du det

1. Start programmet:
   ```bash
   python scriptnavn.py
   ```

2. Indlæs din JSON-fil:
   - Klik på **"Hent JSON-talegenkendelse"**
   - Eller: **drag’n’drop** en `.json`-fil direkte ind i vinduet

3. Klik på **"Konverter til undertekster med Confidence Score"**

4. (Valgfrit) Tjek "Slå tekster sammen" hvis du vil gruppere replikker

5. Klik på **"Gem som SRT-fil"** for at eksportere underteksten

## 🔧 Afhængigheder

Du skal have følgende pakker installeret:

- `PyQt5`
- `pysrt`
- `numpy`

Installer dem hurtigt via pip:
```bash
pip install PyQt5 pysrt numpy
```

## 📄 Licens

MIT-licens. Brug, del og tilpas alt det du vil 💖

---

✨ Lavet med kærlighed af **Peter Bjerre Rosa** – fordi undertekster fortjener lidt AI-magi 😘
