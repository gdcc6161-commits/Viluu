from templates import pick_template

tests = [
    ("smalltalk", None),
    ("smalltalk", "bin müde, heute echt kaputt"),
    ("boundary", "schreib mir auf whatsapp 01234"),
    ("repetition", "hallo nochmal, hi"),
    ("compliment", "du siehst toll aus"),
]

for intent, hint in tests:
    out = pick_template(intent, hint)
    print(f"{intent:10} | hint={hint!r}\n  -> {out}\n")

# harte Regel: keine Striche
probe = pick_template("smalltalk", "nur ein test")
for bad in ("-", "–", "—"):
    assert bad not in probe, f"Strich '{bad}' gefunden: {probe}"

print("✅ Strich-Regel ok. Alles lauffähig.")
