from core.config_loader import load_config
from core.ai_brain import AIBrain

CONFIG = load_config("config/config.yaml")

brain = AIBrain(CONFIG)

print("=" * 60)
print("🤖 Nova Developer Chat")
print("Type 'exit' to quit.")
print("=" * 60)

while True:

    user = input("\nYou > ")

    if user.lower() in ["exit", "quit"]:
        print("\nNova > Goodbye Yash 👋")
        break

    reply = brain.think(user)

    print("\nNova >", reply)