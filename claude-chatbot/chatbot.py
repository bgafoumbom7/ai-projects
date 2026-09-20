"""
A terminal chatbot powered by the Claude API.

Features:
  - Streams responses token-by-token
  - Remembers the whole conversation
  - /reset clears memory, /quit exits

Usage:
  export ANTHROPIC_API_KEY=sk-ant-...
  python chatbot.py
"""

import os
import sys

import anthropic

MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
SYSTEM_PROMPT = "You are a concise, friendly assistant. Keep answers short unless asked for detail."


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first (https://console.anthropic.com).")

    client = anthropic.Anthropic()
    history: list[dict] = []

    print(f"Chatting with {MODEL}. Type /reset to clear memory, /quit to exit.\n")

    while True:
        try:
            user_input = input("you > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye!")
            break

        if not user_input:
            continue
        if user_input == "/quit":
            print("bye!")
            break
        if user_input == "/reset":
            history.clear()
            print("(memory cleared)\n")
            continue

        history.append({"role": "user", "content": user_input})

        print("claude > ", end="", flush=True)
        reply_parts: list[str] = []
        try:
            with client.messages.stream(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=history,
            ) as stream:
                for text in stream.text_stream:
                    print(text, end="", flush=True)
                    reply_parts.append(text)
        except anthropic.APIError as e:
            print(f"\n[API error: {e}]")
            history.pop()  # drop the failed user turn
            continue

        print("\n")
        history.append({"role": "assistant", "content": "".join(reply_parts)})


if __name__ == "__main__":
    main()
