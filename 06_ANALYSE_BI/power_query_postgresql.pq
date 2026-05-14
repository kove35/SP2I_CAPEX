section Section1;

FactMetre =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "fact_metre"]}[Data]
    in
        Table;

DimFamille =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "dim_famille"]}[Data]
    in
        Table;
