# run.py
from app.bot_with_history import main
import os

def start():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear') 
        
        print("=============================================")
        print("          VILUU BOT - STEUERZENTRALE           ")
        print("=============================================")
        print("\nWelche KI möchtest du für diesen Lauf nutzen?")
        print("\n[1] Google Gemini (Online, schnell und kreativ)")
        print("[2] Lokales Modell / Kobold (Offline, auf deinem PC)")
        print("\n[q] Programm beenden")
        print("\n=============================================")
        
        choice = input("Deine Wahl (tippe 1, 2 oder q) und drücke ENTER: ").strip()
        
        if choice == '1':
            print("\nStarte Bot mit Google Gemini...")
            main(ki_provider="gemini")
            # Das break hier ist Absicht, damit das Menü nach einem Lauf nicht sofort wieder erscheint.
            # Du kannst es entfernen, wenn du das wünschst.
            break 
        elif choice == '2':
            print("\nStarte Bot mit dem lokalen Modell (Kobold)...")
            print("WICHTIG: Stelle sicher, dass dein lokaler Server (z.B. KoboldCpp) läuft!")
            main(ki_provider="kobold")
            break
        elif choice.lower() == 'q':
            print("\nProgramm wird beendet. Bis zum nächsten Mal!")
            break
        else:
            input("\nUngültige Eingabe. Drücke ENTER zum Wiederholen.")

if __name__ == "__main__":
    start()