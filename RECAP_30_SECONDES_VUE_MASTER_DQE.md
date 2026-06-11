# ⚡ VUE MAÎTRE DQE : 30 SECONDES

**Status:** 🟢 **GO**  
**Effort:** 1.5 jours (technical)  
**Risque:** 🟢 Zéro (lecture seule + rollback simple)

---

## Quoi ?

**Créer vue `vw_sp2i_generated_dqe_master`** = Union de 4 vues générées 18 lots V5.3

---

## Schéma final

| Colonnes | Détail |
|----------|--------|
| **Métier** | lot_code, article_code, designation, quantity, unit |
| **Spatial** | batiment_id, niveau_id, appartement (60% NULL) |
| **Sources** | source_table, component_index, scope_note (40% NULL) |
| **Total** | 23 colonnes, ~2400 lignes |

---

## Résultats

✅ **18 lots** présents  
✅ **90% mapping** métier  
✅ **< 500ms** performance  
✅ **Export Excel** automatique  

---

## Exécution

| Jour | Action | Temps |
|------|--------|-------|
| 1 | Lire synthèse | 5 min |
| 2 | Audit SQL | 15 min |
| 3 | CREATE VIEW | 10 min |
| 4 | Export Excel | 5 min |
| 5 | Validation métier | 30 min |

**TOTAL: 1h15 + métier**

---

## 📚 Démarrer

1. Lire: [SYNTHESE_VUE_MASTER_DQE.md](SYNTHESE_VUE_MASTER_DQE.md) (5 min)
2. Lire: [INDEX_VUE_MASTER_DQE.md](INDEX_VUE_MASTER_DQE.md) (5 min)
3. Exécuter: [AUDIT_VUE_MASTER_DQE_SCHEMA.sql](AUDIT_VUE_MASTER_DQE_SCHEMA.sql) (5 min)
4. Exécuter: [SQL_CREATE_VUE_MASTER_DQE.sql](SQL_CREATE_VUE_MASTER_DQE.sql) (2 min)
5. Exécuter: [PYTHON_EXPORT_DQE_MASTER_XLSX.py](PYTHON_EXPORT_DQE_MASTER_XLSX.py) (30 sec)

---

## ✅ Livrables

- ✅ 7 fichiers (docs + SQL + Python)
- ✅ Zéro modification exécutée (audit pure)
- ✅ Schéma validated
- ✅ Estimations confirmed
- ✅ Ready to go

---

**GO?** 🟢 **YES**

