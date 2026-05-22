from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "07_API_BACKEND"
SOURCE = ROOT / "03_DONNEES_REFERENCE" / "DQE_PROJECT_SP2I.xlsx"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.services.service_ai_mapping import ServiceAIMapping  # noqa: E402


def section(title: str) -> None:
    print("\n" + "=" * 88)
    print(title)
    print("=" * 88)


def main() -> int:
    started = time.perf_counter()
    section("DEVTOOLS | Validation DQE governance pipeline")
    print(f"Source: {SOURCE}")

    if not SOURCE.exists():
        print("[FAIL] Fichier DQE introuvable.")
        return 1

    try:
        contenu = SOURCE.read_bytes()
        lignes, audit = ServiceAIMapping().extraire_lignes_normalisees(contenu, SOURCE.name)
        confidence = audit.get("ai_confidence") or {}
        governance = confidence.get("governance_quality") or {}
        analysis = audit.get("analyse") or {}

        print(f"[INFO] Feuille recommandee: {audit.get('feuille_recommandee')}")
        print(f"[INFO] Ligne entete: {analysis.get('ligne_entete')}")
        print("[INFO] Mapping:")
        for item in analysis.get("mapping", []):
            print(f"  - {item.get('champ_standard')} <- col {item.get('colonne_index')} ({item.get('colonne_excel')})")
        print(f"[OK] Lignes normalisees: {len(lignes)}")
        print(f"[OK] Trust score: {confidence.get('trust_score', '-')}")
        print(f"[OK] Pertes strictes: {governance.get('blocking_loss_rows', 0)}")
        print(f"[OK] Revue humaine: {governance.get('review_required_rows', 0)}")
        print(f"[OK] Warnings qualite: {governance.get('warning_rows', 0)}")
        print(f"[OK] Lignes ignorees non critiques: {governance.get('ignored_rows', 0)}")
        print("[INFO] Resume gouvernance:")
        print(json.dumps(governance, ensure_ascii=False, indent=2))

        if int(governance.get("blocking_loss_rows") or 0) > 0:
            print("[FAIL] Des pertes strictes bloquantes restent detectees.")
            return 1

        elapsed = round((time.perf_counter() - started) * 1000, 1)
        print(f"\nResume final: OK ({elapsed} ms)")
        return 0
    except Exception:
        print("[FAIL] Validation DQE governance impossible.")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
