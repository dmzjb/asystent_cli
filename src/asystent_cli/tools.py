"""Definicje narzędzi (schematy dla API) i ich implementacje."""

import ast
import operator
from pathlib import Path
from typing import Any

moje_narzedzia: list[dict[str, object]] = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Zwraca aktualną pogodę dla podanego miasta. Użyj tego narzędzia do pytań o pogodę.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "Nazwa miasta, np. Kraków, Warszawa"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Oblicza wynik wyrażenia matematycznego. Zawsze używaj tego do obliczeń.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Wyrażenie np. '17 * 3450 / 100'"}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_note",
            "description": "Zapisuje notatkę jako plik .txt na pulpicie. Używaj tego narzędzia do zapisywania notatek.",
            "parameters": {
                "type": "object",
                "properties": {
                    "note": {"type": "string", "description": "Notatka podana przez użytkownika np. 'Jutro lekarz godzina 15'"}
                },
                "required": ["note"]
            }
        }
    }
]

allowed_operators: dict[type[ast.AST], Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv, #type:ignore
    ast.Pow: operator.pow, #type:ignore
    ast.Mod: operator.mod,
    ast.USub: operator.neg
}

def safe_exec(wezel: ast.AST) -> float:
    if isinstance(wezel, ast.Expression):
        return safe_exec(wezel.body)
    if isinstance(wezel, ast.Constant) and isinstance(wezel.value, (int, float)):
        return wezel.value
    if isinstance(wezel, ast.BinOp):
        typ_op = type(wezel.op)
        if typ_op not in allowed_operators:
            raise ValueError(f"niedozwolony operator: {typ_op.__name__}")
        return allowed_operators[typ_op](
            safe_exec(wezel.left),
            safe_exec(wezel.right),
        )
    if isinstance(wezel, ast.UnaryOp):
        typ_op = type(wezel.op)
        if typ_op not in allowed_operators:
            raise ValueError(f"niedozwolony operator: {typ_op.__name__}")
        return allowed_operators[typ_op](safe_exec(wezel.operand))
    raise ValueError(f"niedozwolony element wyrażenia: {type(wezel).__name__}")

def save_note_function(note: str) -> None:
    desktop = Path.home() / "Desktop"
    desktop.mkdir(parents=True, exist_ok=True)
    fd = desktop / "Notes.txt"

    with fd.open("a", encoding="utf-8") as file:
        file.write(note + "\n")

def execute_tool(name: str, arguments: dict[str, Any]) -> str:
    if name == "get_weather":
        city = arguments.get("city", "nieznane miasto")
        return f"W mieście {city} leje deszcz, jest pochmurno i 12 stopni."
    elif name == "calculate":
        try:
            expr = arguments.get("expression")
            if not isinstance(expr, str):
                return "Błąd obliczeń: wyrażenie musi być tekstem."
            wynik = safe_exec(ast.parse(expr, mode="eval"))
            return str(wynik)
        except Exception as e:
            return f"Błąd obliczeń: {e}"
    elif name == "save_note":
        note = arguments.get("note")
        if not isinstance(note, str):
            return "Błąd: Treść notatki musi być tekstem"
        try:
            save_note_function(note)
            return "Zapisano notatke na pulpicie"
        except Exception as e:
            return f"Błąd systemu plików podczas zapisywania notatki: {e}"
    else:
        return f"Błąd: nieznane narzędzie: {name}"
