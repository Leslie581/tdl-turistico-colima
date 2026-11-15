"""La configuración de protección de `main` (no activada) es coherente con el CI y con el flujo de captura."""
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
RS = json.loads((RAIZ / ".github" / "rulesets" / "proteger-main.json").read_text(encoding="utf-8"))
CI = (RAIZ / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")


def _regla(tipo):
    return next(r for r in RS["rules"] if r["type"] == tipo)


def test_trabajos_exigidos_existen_en_ci():
    trabajos = set(re.findall(r"^  ([a-z-]+):\s*$", CI, flags=re.M))
    exigidos = {c["context"] for c in _regla("required_status_checks")["parameters"]["required_status_checks"]}
    assert exigidos and exigidos <= trabajos


def test_pide_una_aprobacion_y_bloquea_force_push():
    p = _regla("pull_request")["parameters"]
    assert p["required_approving_review_count"] == 1 and p["require_code_owner_review"]
    assert _regla("non_fast_forward") and _regla("deletion")


def test_se_entrega_desactivada_y_sin_actores_de_excepcion():
    # Importado como "disabled": no bloquea nada hasta que la usuaria lo active tras probar la captura con workflow_dispatch (el modo "evaluate" es solo de planes Enterprise).
    # bypass_actors vacío: GitHub rechazó al importar un actor de tipo Integration (error "invalid actor"); la excepción de la captura se agrega en la interfaz
    # (llave de despliegue) y no por archivo.
    assert RS["enforcement"] == "disabled"
    assert RS["bypass_actors"] == []
    captura = (RAIZ / ".github" / "workflows" / "captura-diaria.yml").read_text(encoding="utf-8")
    assert 'git push origin "HEAD:${GITHUB_REF_NAME}"' in captura   # el empuje que necesita la excepción
