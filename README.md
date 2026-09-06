# asystent-cli

Konsolowy asystent AI z narzędziami, napisany od zera na gołym SDK (bez frameworków agentowych
typu LangChain czy PydanticAI) — żeby zrozumieć, jak faktycznie działa pętla tool use pod maską.

## Co potrafi

- Rozmowa w terminalu z pamięcią kontekstu (historia wysyłana przy każdym wywołaniu — API modeli
  LLM jest bezstanowe).
- Trzy narzędzia, z których model korzysta samodzielnie w zależności od pytania:
  - **pogoda** — `get_weather(city)`
  - **kalkulator** — `calculate(expression)`, liczący wyrażenia bezpiecznie przez `ast`
    (bez `eval()` — model nigdy nie wykonuje dowolnego kodu Pythona)
  - **notatki** — `save_note(note)`, dopisuje notatkę do `Notes.txt` na pulpicie
- Licznik kosztów sesji (`/cost`) — realne zużycie tokenów i przeliczenie na dolary wg cennika
  modelu.
- Zabezpieczenie przed zapętleniem (limit iteracji w pętli tool use).

## Architektura

```
src/asystent_cli/
├── config.py     — konfiguracja (klucz API, model) przez pydantic-settings + .env
├── tools.py      — definicje narzędzi (schematy JSON) i ich implementacje
├── assistant.py  — system prompt, licznik kosztów, pętla tool use
└── main.py       — punkt wejścia: pętla CLI (input, komendy /cost i /exit)
```

Model komunikacyjny: **OpenRouter** (endpoint kompatybilny z OpenAI Chat Completions), model
domyślny to Claude Haiku 4.5 — tani i wystarczający do zadań w tym projekcie.

## Uruchomienie

Wymagany [uv](https://docs.astral.sh/uv/).

1. Sklonuj repozytorium i zainstaluj zależności:
   ```bash
   uv sync
   ```
2. Utwórz plik `.env` w katalogu głównym z kluczem API OpenRouter:
   ```
   OPENROUTER_API_KEY=twój-klucz-tutaj
   ```
   Klucz zdobędziesz na [openrouter.ai](https://openrouter.ai/keys). `.env` jest w `.gitignore`
   — nigdy nie trafi do repozytorium.
3. Uruchom asystenta:
   ```bash
   uv run asystent-cli
   ```

## Komendy w czacie

| Komenda | Działanie |
|---|---|
| `/cost` | Pokazuje sumaryczne zużycie tokenów i koszt bieżącej sesji |
| `/exit` | Kończy program |

## Testy

```bash
uv run pytest -v
```

Testy pokrywają logikę narzędzi (`tools.py`): poprawne działanie, przypadki brzegowe (dzielenie
przez zero, priorytet operatorów), oraz bezpieczeństwo `calculate` — odrzucanie prób wykonania
dowolnego kodu (np. `__import__(...)`, dostęp do atrybutów, odwołania do zmiennych) zamiast
liczenia wyrażenia.

## Dlaczego bez frameworka

Ten projekt celowo nie używa żadnego frameworka agentowego — pętla `wyślij → sprawdź czy model
prosi o narzędzie → wykonaj → odeślij wynik → powtórz` jest napisana ręcznie w `assistant.py`.
To był świadomy wybór edukacyjny: zrozumienie tego mechanizmu bez abstrakcji ułatwia późniejszą
pracę z frameworkami (które robią dokładnie to samo, tylko schowane za wygodniejszym API).
