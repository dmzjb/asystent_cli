"""Punkt wejścia CLI: pętla input/output, komendy /cost i /exit."""

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from asystent_cli.assistant import SYSTEM_PROMPT, get_response, print_cost
from asystent_cli.config import Settings


def main() -> None:
    settings = Settings() #type: ignore
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=settings.openrouter_api_key)

    history: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    total_input_tokens = 0
    total_output_tokens = 0

    print("Witaj w Asystencie CLI z narzędziami! (Wpisz '/exit' aby zakończyć)")
    print(f"Model: {settings.model}. Komendy: /cost, /exit")

    while True:
        user_input = input("\nTy: ").strip()
        if not user_input:
            continue
        if user_input == "/exit":
            break
        if user_input == "/cost":
            print_cost(settings.model, total_input_tokens, total_output_tokens)
            continue

        history.append({"role": "user", "content": user_input})

        total_input_tokens, total_output_tokens = get_response(
            client,
            settings,
            history,
            total_input_tokens,
            total_output_tokens
        )


if __name__ == "__main__":
    main()
