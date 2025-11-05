import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# Ielādē .env, kur glabājas privātais API atslēgas kods
load_dotenv()
HF_TOKEN = os.getenv("HF_API_KEY") or os.getenv("HUGGINGFACE_TOKEN") or os.getenv("HF_TOKEN")


MODEL = "google/gemma-2-2b-it"

# Funkcija, kas notīra termināli, lai viss smuki izskatās
def clear():
    os.system("cls" if os.name == "nt" else "clear")

# Funkcija drošai skaitļa ievadei
def ask_int(prompt, min_val, max_val):
    while True:
        try:
            val = int(input(prompt))
            if min_val <= val <= max_val:
                return val
            print(f"Ievadi skaitli {min_val}-{max_val}.")
        except:
            print("Nepareiza ievade. Mēģini vēlreiz.")

# Nolasa tekstu no faila
# (man viss ir vienmēr summary.txt)
def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().strip()
            if not text:
                raise ValueError("fails tukšs")
            return text
    except Exception as e:
        print(f"KĻŪDA: nevar nolasīt failu — {e}")
        exit()

# Funkcija saziņai ar AI modeli
# Vispirms mēģina text mode, ja nē — chat
def hf(prompt, max_tokens=300, temp=0.2):
    try:
        client = InferenceClient(model=MODEL, token=HF_TOKEN)
        out = client.text_generation(prompt, max_new_tokens=max_tokens, temperature=temp)
        return out.strip()
    except Exception:
        try:
            client = InferenceClient(model=MODEL, token=HF_TOKEN)
            r = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temp
            )
            return r.choices[0].message.content.strip()
        except Exception as e:
            print("\nAI NAV PIEEJAMS. PĀRBAUDI TOKENU VAI MODELI!\n")
            print(f"Detaļas: {e}\n")
            exit()

# Teksta saīsināšana
def summarize(text):
    prompt = f"Saīsini šo tekstu 4–6 teikumos:\n\n{text[:5000]}"
    return hf(prompt)

# Ģenerē atslēgvārdus
def extract_keywords(text, n):
    prompt = (
        f"Ģenerē {n} galvenos atslēgvārdus latviski.\n"
        "Katru atslēgvārdu atgriez JAUNĀ rindā, bez numuriem:\n\n"
        f"{text[:5000]}"
    )
    raw = hf(prompt, 200)
    lines = [x.strip("-•., ").strip() for x in raw.splitlines() if x.strip()]
    
    # izfiltrējam dublikātus un atdodam tikai vajadzīgo skaitu
    uniq = []
    for w in lines:
        if len(uniq) >= n: break
        if w.lower() not in [u.lower() for u in uniq]:
            uniq.append(w)
    return uniq[:n]

# Ģenerē viktorīnas jautājumus
# pēc principa: viens AI zvans — viens jautājums,
# lai mazāk kļūdu ar JSON
def generate_quiz(text, n):
    quiz = []
    base = (
        "Izveido 1 īsu viktorīnas jautājumu par tekstu LATVISKI:\n"
        "Formāts:\n"
        "Q: jautājums\nA) ...\nB) ...\nC) ...\nD) ...\nCorrect: A/B/C/D\n\n"
        f"Teksts:\n{text[:5000]}"
    )

    for i in range(n):
        out = hf(base, 300)
        lines = [l.strip() for l in out.splitlines() if l.strip()]
        q_line = next((l for l in lines if l.lower().startswith("q:")), None)
        opts = [l[3:].strip() for l in lines if l[:2] in ("A)", "B)", "C)", "D)")]
        correct = next((l.split(":")[1].strip() for l in lines if l.lower().startswith("correct")), None)

        # Ja AI nedarbojas, tomēr parādās kļūda, bet viss turpinās
        if q_line and len(opts) == 4 and correct in ("A","B","C","D"):
            quiz.append({"q": q_line[2:].strip(), "opts": opts, "correct": correct})
        else:
            quiz.append({"q": "(AI kļūda)", "opts": [], "correct": ""})
    return quiz

def main():
    clear()
    print("TEKSTA APSTRĀDES PROGRAMMA")

    # Automātiski lasa summary.txt
    text = read_file("summary.txt")

    print("\nVeidoju kopsavilkumu...")
    summary = summarize(text)

    clear()
    print("--- KOPSAVILKUMS ---")
    print(summary)

    print("\nCik atslēgvārdus? (1-10)")
    n = ask_int("> ", 1, 10)
    keywords = extract_keywords(text, n)

    clear()
    print("--- KOPSAVILKUMS ---")
    print(summary)
    print("\n--- ATSLĒGVĀRDI ---")
    for k in keywords: print("-", k)

    print("\nCik viktorīnas jautājumus? (1-10)")
    qn = ask_int("> ", 1, 10)
    quiz = generate_quiz(text, qn)

    clear()
    print("--- KOPSAVILKUMS ---")
    print(summary)
    print("\n--- ATSLĒGVĀRDI ---")
    for k in keywords: print("-", k)
    print("\n--- VIKTORĪNA ---")
    for i, q in enumerate(quiz, 1):
        print(f"\n{i}. {q['q']}")
        for idx, opt in enumerate(q['opts']):
            letter = "ABCD"[idx]
            tag = " <- pareizā" if letter == q["correct"] else ""
            print(f"   {letter}) {opt}{tag}")

    print("\nGATAVS.\n")

if __name__ == "__main__":
    main()
