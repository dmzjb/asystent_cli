import ast
import pytest
from asystent_cli.assistant import safe_exec, execute_tool

# ==========================================
# 1. PODSTAWOWE DZIAŁANIA I MATEMATYKA
# ==========================================

def test_dodawanie():
    wynik = safe_exec(ast.parse("2 + 2", mode="eval").body)
    assert wynik == 4

def test_priorytet_operatorow():
    wynik = safe_exec(ast.parse("2 + 3 * 4", mode="eval").body)
    assert wynik == 14

def test_nawiasy():
    wynik = safe_exec(ast.parse("(2 + 3) * 4", mode="eval").body)
    assert wynik == 20

def test_liczby_ujemne():
    wynik = safe_exec(ast.parse("-5 + 3", mode="eval").body)
    assert wynik == -2

def test_mnozenie_przez_ujemna():
    wynik = safe_exec(ast.parse("5 * -2", mode="eval").body)
    assert wynik == -10

def test_zmiennoprzecinkowe():
    wynik = safe_exec(ast.parse("7 / 2", mode="eval").body)
    assert wynik == 3.5


# ==========================================
# 2. SKRAJNE PRZYPADKI (EDGE CASES)
# ==========================================

def test_dzielenie_przez_zero():
    # Moduł operator po prostu dzieli liczby, więc w Pythonie rzuci to ZeroDivisionError.
    # Musimy to złapać w testach modułu inner (safe_exec)
    with pytest.raises(ZeroDivisionError):
        safe_exec(ast.parse("5 / 0", mode="eval").body)

def test_bardzo_duze_liczby_potegowanie():
    # Sprawdzamy, czy potęgowanie działa poprawnie (jeśli dopuściłeś ast.Pow)
    wynik = safe_exec(ast.parse("2 ** 10", mode="eval").body)
    assert wynik == 1024


# ==========================================
# 3. BEZPIECZEŃSTWO (PROMPT INJECTION / RCE)
# ==========================================

def test_odrzuca_niebezpieczny_kod_import():
    # Model próbuje zaimportować i wykonać moduł systemowy
    with pytest.raises(ValueError):
        safe_exec(ast.parse("__import__('os')", mode="eval").body)

def test_odrzuca_zmienne():
    # Model próbuje odwołać się do niezdefiniowanej zmiennej np. "x + 1"
    # AST zinterpretuje "x" jako ast.Name, a nasz kod akceptuje tylko ast.Constant, BinOp itp.
    with pytest.raises(ValueError):
        safe_exec(ast.parse("x + 1", mode="eval").body)

def test_odrzuca_dostep_do_atrybutu():
    # Próba "ucieczki" z piaskownicy przez wewnętrzne dundery Pythona
    with pytest.raises(ValueError):
        safe_exec(ast.parse("().__class__", mode="eval").body)

def test_bledna_skladnia():
    # Sprawdzamy czy samo wbudowane ast.parse rzuca błędem przed dojściem do safe_exec
    with pytest.raises(SyntaxError):
        ast.parse("2 + ", mode="eval")


# ==========================================
# 4. WARSTWA ZEWNĘTRZNA (execute_tool)
# ==========================================
# Te testy sprawdzają samą funkcję nadrzędną, która powinna mieć try...except
# i zwracać błędy jako czysty tekst (string), a nie pozwalać aplikacji "wybuchnąć" (crash).

def test_execute_tool_poprawne_dzialanie():
    wynik = execute_tool("calculate", {"expression": "10 / 2"})
    # Zakładając że execute_tool formatuje float 5.0 do "5" lub chociaż "5.0"
    assert wynik in ("5", "5.0")

def test_execute_tool_brak_klucza_expression():
    # Złe działanie LLMa: wywołuje narzędzie, ale daje pusty słownik
    wynik = execute_tool("calculate", {})
    assert "Błąd" in wynik

def test_execute_tool_zly_typ_expression():
    # Złe działanie LLMa: zwraca int zamiast string w JSON-ie (np. expression: 123)
    wynik = execute_tool("calculate", {"expression": 123})
    assert "Błąd" in wynik

def test_execute_tool_dzielenie_przez_zero():
    # Sprawdzamy, czy funkcja wrapper ładnie wyłapuje ZeroDivisionError z safe_exec
    wynik = execute_tool("calculate", {"expression": "10 / 0"})
    assert "Błąd" in wynik or "ZeroDivisionError" in wynik or "dzielenie przez zero" in wynik.lower()
