import os
import sys
from dotenv import load_dotenv, find_dotenv
from huggingface_hub import InferenceClient
from openai import OpenAI

# ---------------------------
# Konfigurācija (.env ielāde)
# ---------------------------
# find_dotenv() mēģina atrast .env failu projekta/vecākajās mapēs,
# load_dotenv(...) ielādē vides mainīgos no .env uz os.environ
load_dotenv(find_dotenv())

# Hugging Face un OpenAI konfigurācijas mainīgie
HF_TOKEN = os.getenv("HF_TOKEN")                 # piem., hf_xxx (Hugging Face API tokens)
HF_MODEL = os.getenv("HF_MODEL", "facebook/bart-large-cnn")  # summarization modelis

OPENAI_KEY = os.getenv("OPENAI_API_KEY")         # piem., sk-xxx (OpenAI API atslēga)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")      # OpenAI modelis (teksta ģenerācijai)

# Pārbaudām, vai nepieciešamie mainīgie ir pieejami
missing = []
if not HF_TOKEN:
    # Piezīme: šeit ziņojumā minēts "HF_API_KEY", bet kodā izmantojam "HF_TOKEN".
    # Galvenais, lai .env un šis nosaukums sakrīt.
    missing.append("HF_API_KEY")
if not OPENAI_KEY:
    missing.append("OPENAI_API_KEY")
if missing:
    print("❌ Trūkst .env mainīgie: " + ", ".join(missing))
    sys.exit(1)

# Inicializējam klientus API izsaukumiem
hf_client = InferenceClient(token=HF_TOKEN)      # Hugging Face Inference API klients
openai_client = OpenAI(api_key=OPENAI_KEY)       # OpenAI klients

# ---------------------------
# Palīgfunkcijas
# ---------------------------
def read_text(path: str) -> str:
    """
    Nolasa vienkāršu teksta failu (UTF-8) un atgriež saturu kā string.
    Izmet kļūdu, ja fails nav atrodams vai ir tukšs.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            txt = f.read().strip()
        if not txt:
            raise ValueError("Fails ir tukšs.")
        return txt
    except Exception as e:
        # Neturpinām tālāk, ja ievades fails neder — skaidrs kļūdas paziņojums
        raise RuntimeError(f"Kļūda nolasot '{path}': {e}")

def summarize(text: str) -> str:
    """
    Izveido kopsavilkumu, izmantojot Hugging Face summarization endpointu.
    Te nestrādā 'inputs=' vai 'max_length/min_length' uz vecākām hub versijām,
    tāpēc nododam tikai tekstu un modela nosaukumu.
    """
    try:
        # Pareizais izsaukums: summarization(text, model=...)
        result = hf_client.summarization(text, model=HF_MODEL)

        # Atbilde var būt list/dict/str atkarībā no backend; normalizējam:
        if isinstance(result, list):
            summary = result[0].get("summary_text", "").strip()
        elif isinstance(result, dict):
            summary = result.get("summary_text", "").strip()
        else:
            summary = str(result).strip()

        if not summary:
            raise RuntimeError("Tukšs kopsavilkums no HF API.")
        return summary
    except Exception as e:
        # Iesaiņojam kļūdu ar skaidru kontekstu
        raise RuntimeError(f"Kļūda apkopošanā (HF): {e}")

def ask_int(prompt: str, lo: int, hi: int) -> int:
    """
    Prasa lietotājam veselu skaitli [lo..hi].
    Ja ievade neder — atkārto jautājumu, līdz ievade ir derīga.
    """
    while True:
        raw = input(prompt).strip()
        try:
            n = int(raw)
            if lo <= n <= hi:
                return n
            else:
                print(f"❌ Lūdzu ievadi skaitli no {lo} līdz {hi}!")
        except ValueError:
            print("❌ Tas nav derīgs skaitlis! Mēģini vēlreiz.")


def gen_keywords(text: str, n: int) -> str:
    """
    Ģenerē n atslēgvārdus, izmantojot OpenAI Chat Completions API.
    Atgriež vienu teksta bloku, kur katrs atslēgvārds ir jaunā rindā.
    """
    try:
        resp = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Tu ģenerē īsus, aprakstošus atslēgvārdus latviešu valodā."},
                {"role": "user", "content": f"Izveido TIEŠI {n} atslēgvārdus par šo tekstu (katru jaunā rindā, bez numurācijas):\n\n{text}"},
            ],
            temperature=0.3,  # zemāka temperatūra = precīzāks/mazāk haotisks izvads
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"Kļūda ģenerējot atslēgvārdus (OpenAI): {e}")

def gen_quiz(text: str, n_q: int) -> str:
    """
    Ģenerē n_q jautājumus ar 4 atbilžu variantiem (A–D) un norāda pareizo atbildi.
    1) Palūdzam modelim atdot TIKAI JSON (bez lieka teksta),
    2) Validējam/normalizējam variantus, lai tie vienā jautājumā neatkārtotos,
    3) Sajaucam variantus un izlīdzinām pareizo atbilžu burtus (A/B/C/D rotācija),
    4) Renderējam uz termināli glītā teksta formātā.
    """
    import json, random

    # Norādām stingru atgriežamo formātu (JSON masīvs ar noteiktiem laukiem)
    system_msg = (
        "Tu esi stingrs testu ģenerators. Atgriez TIKAI validu JSON masīvu ar tieši n ierakstiem, "
        "katram: {\"question\": str, \"options\": {\"A\": str, \"B\": str, \"C\": str, \"D\": str}, "
        "\"answer\": \"A\"|\"B\"|\"C\"|\"D\"}. Bez paskaidrojumiem, bez cita teksta."
    )
    user_msg = (
        f"Izveido TIEŠI {n_q} jautājumus latviešu valodā par šo tekstu. "
        "Katram jautājumam jābūt 4 savstarpēji ATŠĶIRĪGIEM variantiem (A–D) un tikai vienai pareizajai atbildei. "
        "Nedublē variantu tekstus vienā jautājumā. "
        "Atbildei 'answer' jābūt tikai burtam A, B, C vai D. "
        "ATBILDI TIKAI AR JSON MASĪVU, BEZ NEKĀDIEM PAPILDU TEKSTIEM.\n\n"
        f"Teksts:\n{text}"
    )

    try:
        # Lūdzam OpenAI striktu JSON atbildi
        resp = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.4,  # mērena radošuma pakāpe
        )
        raw = resp.choices[0].message.content.strip()

        # Parsējam JSON → Python list/dict
        data = json.loads(raw)
        if not isinstance(data, list):
            raise ValueError("JSON nav masīvs")
        # Ja modelis iedod vairāk ierakstu, nogriežam līdz n_q
        data = data[:n_q]

        letters = ["A", "B", "C", "D"]
        lines = []

        for i, item in enumerate(data, start=1):
            # Izgūstam jautājumu, variantus un pareizās atbildes burtu
            q = str(item.get("question", "")).strip()
            opts = item.get("options", {}) or {}
            ans_letter = str(item.get("answer", "")).strip().upper()

            # Iegūstam pareizās atbildes tekstu (ja iespējams)
            correct_text = str(opts.get(ans_letter, "")).strip() if ans_letter in opts else ""

            # 1) Normalizējam variantus un novēršam dublikātus vienā jautājumā
            #    Ja variants tukšs vai atkārtojas, pievienojam nelielu sufiksu, lai padarītu unikālu
            seen = set()
            fixed_opts = {}
            for L in letters:
                t = str(opts.get(L, "")).strip()
                key = t.lower()
                if not t:
                    t = f"— variants {L}"  # aizstājam tukšu ar saprotamu vietturi
                    key = t.lower()
                suffix_n = 2
                while key in seen:
                    t = f"{t} (alternatīva {suffix_n})"
                    key = t.lower()
                    suffix_n += 1
                seen.add(key)
                fixed_opts[L] = t

            # Ja pareizās atbildes teksts pazudis, piesaistām to esošam variantam (vai A)
            if not correct_text or correct_text.lower() not in {fixed_opts[x].lower() for x in letters}:
                correct_text = fixed_opts.get(ans_letter, fixed_opts["A"])

            # 2) Sajaucam variantu secību, lai nerastos stereotipiska kārta
            items_list = [(L, fixed_opts[L]) for L in letters]
            random.shuffle(items_list)  # nejauša secība

            # 3) Rotējam pareizās atbildes burtu pa jautājumiem (A → B → C → D → ...)
            target_letter = letters[(i - 1) % 4]

            # “Pārzīmējam” sajauktos variantus uz jauniem A–D burtiem
            remapped = {}
            for idx, (_, txt) in enumerate(items_list):
                remapped[letters[idx]] = txt

            # Nosakām, pie kura burta pēc remap atrodas pareizās atbildes teksts
            cur_correct_letter = None
            for L in letters:
                if remapped[L].lower() == correct_text.lower():
                    cur_correct_letter = L
                    break
            if cur_correct_letter is None:
                # Ja nav atrasts, pieņemam A kā noklusēto
                cur_correct_letter = "A"
                correct_text = remapped["A"]

            # Ja pareizā nav "target_letter", samainām vietām, lai izlīdzinātu sadalījumu
            if cur_correct_letter != target_letter:
                remapped[cur_correct_letter], remapped[target_letter] = remapped[target_letter], remapped[cur_correct_letter]
                cur_correct_letter = target_letter

            # 4) Sagatavojam izdruku terminālī (glīts, vienkāršs formāts)
            A, B, C, D = remapped["A"], remapped["B"], remapped["C"], remapped["D"]
            lines.append(f"{i}) {q}")
            lines.append(f"A) {A}")
            lines.append(f"B) {B}")
            lines.append(f"C) {C}")
            lines.append(f"D) {D}")
            lines.append(f"Pareizā atbilde: {cur_correct_letter}")
            lines.append("")  # tukša rinda starp jautājumiem

        # Atgriežam vienu teksta bloku (gatavs drukai)
        return "\n".join(lines).strip()

    except Exception:
        # Ja kas neizdodas (JSON nelasāms u.tml.), atgriežam sākotnējo izejas tekstu,
        # lai programma nekristu; lietotājs redzēs, kas atnāca no modeļa
        return raw if 'raw' in locals() else "Neizdevās izveidot viktorīnu."

# ---------------------------
# Programmas gaita (terminālī)
# ---------------------------
def main():
    # 1) Nolasām ievades tekstu no input.txt un parādam priekšskatījumu
    text = read_text("input.txt")
    print("\n=== Teksts veiksmīgi ielādēts! ===\n")
    print(text[:500] + ("..." if len(text) > 500 else ""))
    print("\n----------------------------------------")

    # 2) Izveidojam kopsavilkumu (HF)
    print("\nApkopo tekstu (Hugging Face)...\n")
    summary = summarize(text)
    print("🧾 Kopsavilkums:\n")
    print(summary)

    # 3) Prasam atslēgvārdu skaitu (1–10), validējam ievadi
    try:
        n_keywords = ask_int("\nCik atslēgvārdus ģenerēt? (1–10): ", 1, 10)
    except RuntimeError as e:
        print("❌", e)
        sys.exit(1)

    # 4) Ģenerējam atslēgvārdus ar OpenAI un izdrukājam
    print("\nĢenerē atslēgvārdus (OpenAI)...\n")
    keywords_block = gen_keywords(text, n_keywords)
    print("🔹 Atslēgvārdi:\n")
    print(keywords_block)

    # 5) Prasam jautājumu skaitu (1–10) un ģenerējam viktorīnu ar OpenAI
    try:
        n_questions = ask_int("\n❓ Cik testjautājumus ģenerēt? (1–10): ", 1, 10)
    except RuntimeError as e:
        print("❌", e)
        sys.exit(1)

    print(f"\nĢenerē {n_questions} testjautājumus (OpenAI)...\n")
    quiz_block = gen_quiz(text, n_q=n_questions)
    print(quiz_block)

    print("\nViss izdevās! Programma pabeidza darbu veiksmīgi.\n")

# Standarta “entry point” — sākam izpildi ar main()
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Lietotājs pārtrauca ar Ctrl+C
        print("\n❗ Pārtraukts ar Ctrl+C")
        sys.exit(1)
    except Exception as e:
        # Noķer jebkuru neparedzētu kļūdu, lai terminālī būtu skaidrs paziņojums
        print(f"\n❌ Neapstrādāta kļūda: {e}")
        sys.exit(1)
