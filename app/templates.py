# app/templates.py
# Einheitliche Templates-Datei, kompatibel mit einfacher UND erweiterter Nutzung.
# Regeln:
# - Umlaute ä/ö/ü Pflicht
# - kein ß (immer ss)  -> z. B. grösste
# - keine Bindestriche/Gedankenstriche in Ausgaben
# - DU-Form
# - kein Treffen, keine Kontakte in den Texten

from __future__ import annotations
import random

# -----------------------------
# 1) Einfache, generische Liste
#    -> dein bot_with_history.py kann sofort random.choice(TEMPLATES) nutzen
# -----------------------------
TEMPLATES: list[str] = [
    "Hm, das klingt wirklich interessant. Kannst du mir ein bisschen mehr darüber erzählen?",
    "Ach so, jetzt wird mir klarer, was du meinst. Würdest du genauer beschreiben, worauf du anspielst?",
    "Ich höre dir aufmerksam zu. Was bedeutet das für dich im Moment?",
    "Das wirkt aufrichtig. Was bereitet dir dabei die grösste Freude?",
    "Ich merke, dass dir das wichtig ist. An was denkst du gerade?",
    "So etwas habe ich schon lange nicht gehört. Erzähl mir mehr darüber!",
    "Das klingt vertraut. Hast du positive Erfahrungen damit gemacht?",
    "Ich bin neugierig. Was genau möchtest du damit sagen?",
    "Das hat etwas Besonderes. Was kommt dir dabei in den Sinn?",
    "Ich spüre gerade eine Energie. Möchtest du das vertiefen?",
    "Interessant, wie du das formulierst. Was bedeutet es dir im Moment?",
    "Das klingt nahbar. Wie fühlt es sich für dich an?",
    "Mir fällt auf, dass du offen bist. Möchtest du mehr teilen?",
    "Das klingt nach einem besonderen Moment. Was reizt dich daran besonders?",
    "Ich kann mir vorstellen, wie das ist. Was möchtest du dazu noch sagen?",
    "Das wirkt sehr ehrlich. Erzähl mir bitte mehr darüber.",
    "So direkt mag ich es. Was kommt dir noch in den Sinn?",
    "Das klingt nach einem Gefühl, das wichtig ist. Wie fühlt es sich für dich an?",
    "Ich kann mich gut hineinversetzen. Wie erlebst du das im Alltag?",
    "Das wirkt lebendig. Was möchtest du dazu noch sagen?",
    "Spannend, wie du das ausdrückst. Hast du ein Beispiel für mich?",
    "Das klingt nach einer Seite von dir, die ich gerne besser kennenlernen möchte.",
    "Da steckt Tiefe drin. Was meinst du genau?",
    "Ich finde es schön, wie du das formulierst. Was bedeutet es dir jetzt gerade?",
    "Das macht mich neugierig. Was fühlst du im Moment?",
    "Da ist viel zu spüren. Was davon möchtest du teilen?",
    "Das klingt ehrlich. Wie geht es dir, wenn du das aussprichst?",
    "Ich lese da Sehnsucht heraus. Magst du sie näher beschreiben?",
    "Das ist ein spannender Gedanke. Was kommt dir dazu noch in den Sinn?",
    "Das wirkt warmherzig. Was steckt dahinter?",
    "Das ist mutig. Erzähl mir mehr darüber.",
    "Ich fühle, dass dir das wichtig ist. Möchtest du etwas tiefer eintauchen?",
    "Das klingt nach dir. Wie zeigt sich das in deinem Alltag?",
    "Ich mag deine Offenheit. Was beschäftigt dich gerade am meisten?",
    "Es wirkt, als wäre dir das ernst. Was meinst du genau?",
    "Das klingt nah. Wie fühlt es sich an, das zu sagen?",
    "Ich spüre da etwas Tiefes. Kannst du mir darüber mehr erzählen?",
    "Das klingt echt und unverstellt. Was möchtest du mir noch anvertrauen?",
    "Ich fühle mich verbunden mit dem, was du schreibst. Erzähl mir dazu mehr.",
    "Das berührt mich. Möchtest du mir mehr darüber erzählen?",
    "Ich bin ganz bei dir. Womit möchtest du weitermachen?",
    "Klingt gut. Was wäre dir als Nächstes wichtig?",
    "Danke für deine Offenheit. Was möchtest du jetzt als Schwerpunkt setzen?",
    "Ich höre zu. Welche Richtung möchtest du einschlagen?",
    "Alles klar. Was davon möchtest du zuerst angehen?",
    "Ich bin dabei. Womit fangen wir an?",
    "Gut zu wissen. Welche Frage soll ich dir als Erstes stellen?",
    "Verstanden. Was ist dir im Chat gerade am wichtigsten?",
]

# -----------------------------
# 2) Optional: Kategorisierte Nutzung
#    -> falls wir später per Intent auswählen wollen
#    Wir verwenden deine Sätze oben auch als Fallback,
#    so gibt es immer eine gültige, menschliche Antwort.
# -----------------------------
_CATEGORIZED = {
    "compliment": [
        "Das liest sich schön. Was hat dich zuerst an mir angesprochen?",
        "Danke für die netten Worte. Was gefällt dir besonders an mir?",
        "Sehr charmant. Magst du mir noch etwas über dich erzählen?",
    ],
    "question": [
        "Gute Frage. Was ist dir an der Antwort am wichtigsten?",
        "Ich überlege mit. In welche Richtung soll es gehen?",
        "Sag mir kurz, was dahinter steckt, dann gehe ich darauf ein.",
    ],
    "smalltalk": [
        "Klingt sympathisch. Was wünschst du dir hier gerade am meisten Gespräche Humor oder etwas Ablenkung?",
        "Was war dein kleines Highlight in letzter Zeit?",
        "Ich mag ehrlichen Smalltalk. Was macht dich neugierig an mir?",
    ],
    "sexual": [
        "Danke für deine Offenheit. Bleiben wir hier im Chat und schreiben respektvoll. Was reizt dich an Worten am meisten?",
        "Wir tasten uns heran. Welche Stimmung magst du eher verspielt ruhig oder fantasievoll?",
        "Ich bleibe hier. Erzähl mir, was dich anspricht, dann greife ich es behutsam auf.",
    ],
    "boundary": [
        "Ich bleibe hier im Chat. Schreib mir, was dir wichtig ist, dann knüpfe ich daran an.",
        "Hier ist für mich der richtige Ort. Was möchtest du mir über dich erzählen?",
        "Ich wechsle nicht. Erzähl mir lieber, was dich gerade beschäftigt.",
    ],
    "aggressive": [
        "Ich lese dich, bleibe aber respektvoll. Sag mir, worum es dir genau geht.",
        "Ich nehme dich ernst. Was ist dein Kernanliegen?",
        "Ich bleibe ruhig. Wie kann ich dir gerade am besten begegnen?",
    ],
    "repetition": [
        "Ich knüpfe an. Was ist dir jetzt am wichtigsten?",
        "Das Thema hatten wir schon kurz. Was fehlt dir noch?",
        "Alles klar. Sollen wir Schritt für Schritt weitergehen?",
    ],
    "fallback": TEMPLATES,  # <- deine grosse, menschliche Liste oben
}

def pick_template(intent: str | None, hint: str | None = None) -> str:
    """
    Liefert eine menschliche Vorlage:
    - nutzt intent, wenn vorhanden
    - sonst die grosse generische Liste (TEMPLATES)
    - hint bleibt aktuell ungenutzt, ist aber für spätere Feinsteuerung vorgesehen
    """
    pool = _CATEGORIZED.get(intent or "", TEMPLATES)
    return random.choice(pool)
