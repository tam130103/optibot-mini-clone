"""Interactive RAG chat demo — use this for screenshots."""

import logging

from src.chat import ask

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)


def main():
    print("=" * 60)
    print("  OptiBot Mini-Clone (DeepSeek + ChromaDB)")
    print("  Type 'quit' to exit")
    print("=" * 60)

    history = []

    while True:
        try:
            question = input("\n🧑 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        if not question:
            continue

        print("\n🤖 OptiBot:")
        try:
            answer = ask(question, history)
            print(answer)

            # Maintain conversation history (last 10 messages)
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": answer})
            if len(history) > 10:
                history = history[-10:]
        except Exception as e:
            print(f"Error: {e}")
            logging.exception("Chat error")


if __name__ == "__main__":
    main()
