section Section1;

FactMetre =
    let
        Source = PostgreSQL.Database(
            "ep-snowy-flower-al6kbdya.c-3.eu-central-1.aws.neon.tech",
            "neondb",
            [CreateNavigationProperties = false]
        ),
        Table = Source{[Schema = "public", Item = "fact_metre"]}[Data]
    in
        Table;

DimProjet =
    let
        Source = PostgreSQL.Database(
            "ep-snowy-flower-al6kbdya.c-3.eu-central-1.aws.neon.tech",
            "neondb",
            [CreateNavigationProperties = false]
        ),
        Table = Source{[Schema = "public", Item = "dim_projet"]}[Data]
    in
        Table;

DimBatiment =
    let
        Source = PostgreSQL.Database(
            "ep-snowy-flower-al6kbdya.c-3.eu-central-1.aws.neon.tech",
            "neondb",
            [CreateNavigationProperties = false]
        ),
        Table = Source{[Schema = "public", Item = "dim_batiment"]}[Data]
    in
        Table;

DimNiveau =
    let
        Source = PostgreSQL.Database(
            "ep-snowy-flower-al6kbdya.c-3.eu-central-1.aws.neon.tech",
            "neondb",
            [CreateNavigationProperties = false]
        ),
        Table = Source{[Schema = "public", Item = "dim_niveau"]}[Data]
    in
        Table;

DimAppartement =
    let
        Source = PostgreSQL.Database(
            "ep-snowy-flower-al6kbdya.c-3.eu-central-1.aws.neon.tech",
            "neondb",
            [CreateNavigationProperties = false]
        ),
        Table = Source{[Schema = "public", Item = "dim_appartement"]}[Data]
    in
        Table;

DimZone =
    let
        Source = PostgreSQL.Database(
            "ep-snowy-flower-al6kbdya.c-3.eu-central-1.aws.neon.tech",
            "neondb",
            [CreateNavigationProperties = false]
        ),
        Table = Source{[Schema = "public", Item = "dim_zone"]}[Data]
    in
        Table;

DimPiece =
    let
        Source = PostgreSQL.Database(
            "ep-snowy-flower-al6kbdya.c-3.eu-central-1.aws.neon.tech",
            "neondb",
            [CreateNavigationProperties = false]
        ),
        Table = Source{[Schema = "public", Item = "dim_piece"]}[Data]
    in
        Table;

DimLot =
    let
        Source = PostgreSQL.Database(
            "ep-snowy-flower-al6kbdya.c-3.eu-central-1.aws.neon.tech",
            "neondb",
            [CreateNavigationProperties = false]
        ),
        Table = Source{[Schema = "public", Item = "dim_lot"]}[Data]
    in
        Table;

DimSousLotComplet =
    let
        Source = PostgreSQL.Database(
            "ep-snowy-flower-al6kbdya.c-3.eu-central-1.aws.neon.tech",
            "neondb",
            [CreateNavigationProperties = false]
        ),
        Table = Source{[Schema = "public", Item = "dim_sous_lot_complet"]}[Data]
    in
        Table;

DimArticleBpu =
    let
        Source = PostgreSQL.Database(
            "ep-snowy-flower-al6kbdya.c-3.eu-central-1.aws.neon.tech",
            "neondb",
            [CreateNavigationProperties = false]
        ),
        Table = Source{[Schema = "public", Item = "dim_article_bpu"]}[Data]
    in
        Table;

