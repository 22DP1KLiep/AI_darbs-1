# AI_darbs-1
# Teksta apstrādes programma (Hugging Face)

Šī Python programma lasa tekstu no faila `summary.txt`, apstrādā to ar Hugging Face modeļiem un terminālī attēlo:

* kopsavilkumu,
* atslēgvārdus,
* viktorīnas jautājumus ar atbildēm.

Programma izstrādāta mācību nolūkā, lai demonstrētu teksta apstrādi ar mākslīgo intelektu un API izmantošanu.

---

## Funkcionalitāte

Programma veic sekojošus soļus:

1. Nolasa tekstu no `summary.txt`
2. Ģenerē īsu kopsavilkumu
3. Pieprasa ievadīt atslēgvārdu skaitu (1–10)
4. Ģenerē atslēgvārdus
5. Pieprasa jautājumu skaitu (1–10)
6. Izveido viktorīnas jautājumus ar pareizo atbildi
7. Attēlo visu terminālī

Terminālis pirms katras sadaļas tiek notīrīts, lai rezultāts būtu pārskatāms.

---

## Instalācija

### 1. Klonēt projektu

```bash
git clone <repo>
cd <mape>
```

### 2. Virtuālā vide

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# vai
source .venv/bin/activate   # Linux/Mac
```

### 3. Instalēt bibliotēkas

```bash
pip install -r requirements.txt
```

---

## API konfigurācija

Izveidot `.env` failu ar Hugging Face tokenu:

```
HF_API_KEY=jusu_token
```

Tokenu var iegūt: [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

---

## Lietošana

Ievietot tekstu failā `summary.txt`

Palaist programmu:

```bash
python main.py
```

Programma jautās:

* cik atslēgvārdus ģenerēt (1–10)
* cik viktorīnas jautājumus (1–10)

Rezultāti tiks parādīti terminālī.

---

## Prasības

* Python 3.10+
* Hugging Face konts un API token
* Bibliotēkas no `requirements.txt`

---

## Mērķis

Šis projekts paredzēts:

* darbam ar AI teksta apstrādi,
* pieredzes iegūšanai ar Hugging Face API,
* praktiskam termināļa programmas pielietojumam.

---

## Pieejamā funkcionalitāte

| Funkcija          | Apraksts                              |
| ----------------- | ------------------------------------- |
| Teksta nolasīšana | Automātiski no `summary.txt`          |
| Kopsavilkums      | Īss teksta pārstāsts                  |
| Atslēgvārdi       | Lietotājs izvēlas skaitu              |
| Viktorīna         | 4 atbilžu varianti un pareizā atbilde |
| Termināļa UI      | Attīrīts skats katrā solī             |

---

## Autors

Projekts izstrādāts studiju vajadzībām, izmantojot Python un Hugging Face API.

---

## Nobeigums

Programma demonstrē praktisku pieeju AI izmantošanai teksta apstrādē un var tikt paplašināta ar:

* datu saglabāšanu failos,
* web saskarni,
* citiem valodas modeļiem.

---
