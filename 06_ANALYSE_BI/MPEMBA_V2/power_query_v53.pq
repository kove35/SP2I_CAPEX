// SP2I CAPEX - Power Query V5.3
// Univers separes: Reel, Generatif, Completude batiment.
// Remplacer Server et Database par les valeurs Neon/Power BI Gateway.

let
    Server = "NEON_HOST",
    Database = "NEON_DATABASE",
    Source = PostgreSQL.Database(Server, Database, [CreateNavigationProperties=false]),

    FACT_METRE = Source{[Schema="public",Item="fact_metre"]}[Data],
    FACT_SIMULATION = Source{[Schema="public",Item="fact_simulation"]}[Data],
    PROCUREMENT_DECISIONS = Source{[Schema="public",Item="procurement_decisions"]}[Data],

    VW_SP2I_GENERATED_CAPEX = Source{[Schema="public",Item="vw_sp2i_generated_capex"]}[Data],
    VW_SP2I_GENERATED_QUANTITIES = Source{[Schema="public",Item="vw_sp2i_generated_quantities"]}[Data],
    VW_ENERGY_RESILIENCE_DASHBOARD = Source{[Schema="public",Item="vw_energy_resilience_dashboard"]}[Data],
    VW_GENERATOR_DASHBOARD = Source{[Schema="public",Item="vw_generator_dashboard"]}[Data],
    VW_ENERGY_SOURCES_DASHBOARD = Source{[Schema="public",Item="vw_energy_sources_dashboard"]}[Data],
    VW_SP2I_GENERATED_BUILDING = Source{[Schema="public",Item="vw_sp2i_generated_building"]}[Data],
    VW_SP2I_GENERATED_ENVELOPE = Source{[Schema="public",Item="vw_sp2i_generated_envelope"]}[Data],
    VW_SP2I_GENERATED_SPECIAL_SYSTEMS = Source{[Schema="public",Item="vw_sp2i_generated_special_systems"]}[Data],

    DIM_BATIMENT = Source{[Schema="public",Item="dim_batiment"]}[Data],
    DIM_NIVEAU = Source{[Schema="public",Item="dim_niveau"]}[Data],
    DIM_APPARTEMENT = Source{[Schema="public",Item="dim_appartement"]}[Data],
    DIM_PIECE = Source{[Schema="public",Item="dim_piece"]}[Data],
    DIM_LOT = Source{[Schema="public",Item="dim_lot"]}[Data]
in
    Source
