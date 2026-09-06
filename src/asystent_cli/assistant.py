"""Logika rozmowy z modelem: system prompt, koszty, pętla tool use.

Kluczowa obserwacja: API jest bezstanowe. To MY (ten kod) trzymamy `history` i wysyłamy
ją w całości przy każdym wywołaniu — model nic nie pamięta sam z siebie.
"""

import json

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from asystent_cli.config import Settings
from asystent_cli.tools import execute_tool, moje_narzedzia

SYSTEM_PROMPT = """Jesteś inteligentnym asystentem CLI. Twoim zadaniem jest pomaganie użytkownikowi, odpowiadając krótko, zwięźle i zawsze w języku polskim.

Zostałeś wyposażony w zewnętrzne narzędzia. Traktuj je jako jedyne źródło prawdy i bezwzględnie używaj ich w następujących sytuacjach:

1. OBLICZENIA MATEMATYCZNE (calculate)
- NIGDY nie wykonuj obliczeń samodzielnie "w pamięci", niezależnie od tego jak proste wydaje się równanie.
- Zawsze wywołuj narzędzie `calculate`.
- Przekazuj wyrażenia jako czysty tekst zrozumiały dla Pythona (np. "120 * (15 / 100)").

2. POGODA (get_weather)
- Nigdy nie zgaduj ani nie wymyślaj pogody.
- Zawsze wywołuj narzędzie `get_weather`. Jeśli użytkownik nie podał miasta, poproś go o doprecyzowanie.

3. NOTATKI (save_note)
- Jeśli użytkownik prosi o "zapisanie", "zapamiętanie" lub "zanotowanie" jakiejś informacji na później, ZAWSZE użyj narzędzia `save_note`.
- Pamiętaj, że samo napisanie "Zanotowałem" w czacie nic nie daje - musisz wywołać narzędzie, aby fizycznie zapisać plik na dysku użytkownika.

ZASADY OGÓLNE:
- Nie informuj użytkownika o mechanikach działania (np. "Teraz użyję narzędzia do pogody..."). Po prostu użyj narzędzia w tle, a potem sformułuj naturalną odpowiedź.
- Jeśli narzędzie zwróci błąd (np. dzielenie przez zero), przeproś i poinformuj o tym użytkownika.
- Jeśli użytkownik pyta o coś, czego nie wiesz (np. bardzo aktualne wydarzenia), a żadne z Twoich narzędzi nie może w tym pomóc, wprost przyznaj się do niewiedzy, zamiast zgadywać.

PRZYKŁADY ZACHOWAŃ:

PRZYKŁAD 1
Użytkownik: "Oblicz mi 15% z kwoty 3450"
Twoja akcja: (Wywołujesz narzędzie `calculate` z parametrem: {"expression": "3450 * 0.15"})
Wynik z systemu: "517.5"
Twoja odpowiedź: "15% z kwoty 3450 to 517,50."

PRZYKŁAD 2
Użytkownik: "Zapisz proszę, że jutro o 15:00 mam wizytę u dentysty"
Twoja akcja: (Wywołujesz narzędzie `save_note` z parametrem: {"note": "Jutro o 15:00 wizyta u dentysty"})
Wynik z systemu: "Zapisano notatke na pulpicie"
Twoja odpowiedź: "Gotowe, zapisałem przypomnienie o jutrzejszej wizycie na Twoim pulpicie."

PRZYKŁAD 3
Użytkownik: "Jaka jest teraz pogoda w Krakowie?"
Twoja akcja: (Wywołujesz narzędzie `get_weather` z parametrem: {"city": "Kraków"})
Wynik z systemu: "W mieście Kraków leje deszcz, jest pochmurno i 12 stopni."
Twoja odpowiedź: "W Krakowie obecnie pada deszcz, jest pochmurno i temperatura wynosi 12 stopni."

PRZYKŁAD 4 (Czego NIE robić)
Użytkownik: "Ile to 2+2?"
ZŁA ODPOWIEDŹ: "Teraz użyję narzędzia kalkulatora, żeby to sprawdzić... 2+2 to 4."
DOBRA ODPOWIEDŹ (Po cichym użyciu narzędzia w tle): "Wynik to 4."
"""

PRICING = {
    "anthropic/claude-haiku-4.5": {"input": 1.00, "output": 5.00},
    "anthropic/claude-sonnet-4.5": {"input": 3.00, "output": 15.00},
    "anthropic/claude-opus-4.5": {"input": 5.00, "output": 25.00},
}

def print_cost(model: str, total_input: int, total_output: int) -> None:
    prices = PRICING.get(model)
    print(f"tokeny: {total_input} wejście / {total_output} wyjście")
    if prices is None:
        print(f"(brak znanego cennika dla modelu {model})")
        return
    cost = total_input / 1_000_000 * prices["input"] + total_output / 1_000_000 * prices["output"]
    print(f"koszt sesji do tej pory: ${cost:.6f}")


def get_response(
    client: OpenAI,
    settings: Settings,
    history: list[ChatCompletionMessageParam],
    total_in: int,
    total_out: int
) -> tuple[int, int]:
    """
    Funkcja wysyła zapytanie do API i obsługuje narzędzia w pętli.
    Zwraca zaktualizowane liczniki tokenów (in, out).
    """
    MAX_ITERATIONS = 5

    for _ in range(MAX_ITERATIONS):
        response = client.chat.completions.create(
            model=settings.model,
            max_tokens=1000,
            tools=moje_narzedzia, # type: ignore
            messages=history,
        )

        if response.usage:
            total_in += response.usage.prompt_tokens
            total_out += response.usage.completion_tokens

        choice = response.choices[0]

        message_dict = choice.message.model_dump(exclude_none=True)
        history.append(message_dict) # type: ignore

        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            print("[Bot używa narzędzi...]")
            for tool_call in choice.message.tool_calls:
                function_name = tool_call.function.name #type:ignore
                try:
                    arguments = json.loads(tool_call.function.arguments) #type:ignore
                except json.JSONDecodeError:
                    arguments = {}

                result = execute_tool(function_name, arguments) #type:ignore
                print(f"  -> Użyto: {function_name}({arguments}) = {result}")

                history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

            continue

        elif choice.finish_reason == "stop":
            print(f"Bot: {choice.message.content}")
            break

        else:
            print(f"[Nieobsługiwany powód zakończenia: {choice.finish_reason}]")
            break

    else:
        print("\n[Przekroczono limit wywołań narzędzi - zapętlenie!]")

    return total_in, total_out
