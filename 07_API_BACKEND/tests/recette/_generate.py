"""Assemble recipe_v6_schema.sql (recette isolee, donnees 100% synthetiques).

Les vues V6 projet/dashboard/cost-intelligence sont extraites textuellement de
09_INFRA/sql/033_v6_financial_reconciliation.sql (entre le premier CREATE VIEW
et le bloc DO $$) pour rester conformes a la definition de production sans
rejouer la chaine vw_fact_metre_financial_canonical.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
RACINE = HERE.parents[2]
SQL_033 = RACINE / "09_INFRA" / "sql" / "033_v6_financial_reconciliation.sql"

part1 = (HERE / "_part1.sql").read_text(encoding="utf-8").rstrip() + "\n"
part3 = (HERE / "_part3.sql").read_text(encoding="utf-8").lstrip() + "\n"

src = SQL_033.read_text(encoding="utf-8")
start = src.index("CREATE OR REPLACE VIEW vw_project_cost_summary_v6 AS")
end = src.index("DO $$", start)  # bloc de validation post-vues (apres le CREATE VIEW)
v6_views = src[start:end].rstrip() + "\n"

out = part1 + "\n" + v6_views + "\n" + part3
(HERE / "recipe_v6_schema.sql").write_text(out, encoding="utf-8")
print("RECIPE_SQL_GENERATED", HERE / "recipe_v6_schema.sql")
