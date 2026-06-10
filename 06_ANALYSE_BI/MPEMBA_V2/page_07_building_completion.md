# Page 07 - COMPLETUDE_BATIMENT

## Objectif

Afficher les lots V5.3 de completude BAT_01.

## Sources

- `vw_sp2i_generated_building`
- `vw_sp2i_generated_envelope`
- `vw_sp2i_generated_special_systems`

## KPIs

- GO
- Maconnerie
- Toiture
- Facades
- Menuiseries
- VRD
- Securite
- Incendie
- Ascenseur

## Heatmaps

- Par lot: `lot_code`.
- Par niveau: utiliser `scope_note` ou une future dimension niveau si V5.4 detaille les niveaux.
- Par appartement: utiliser les vues generatives V5.2.1 pour les composants rattaches aux pieces.

## Dedoublonnage

Pour un total V5.3:
- compter tout `vw_sp2i_generated_building`;
- ajouter `vw_sp2i_generated_envelope` hors `LOT_TOIT`;
- ajouter `vw_sp2i_generated_special_systems` hors `LOT_VRD`.

Cette logique evite de compter deux fois toiture et VRD.
