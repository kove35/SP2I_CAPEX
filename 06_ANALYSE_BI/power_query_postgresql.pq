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

DimProjet =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "dim_projet"]}[Data]
    in
        Table;

DimLot =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "dim_lot"]}[Data]
    in
        Table;

DimNiveau =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "dim_niveau"]}[Data]
    in
        Table;

DimBatiment =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "dim_batiment"]}[Data]
    in
        Table;

KpiCapex =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "v_kpi_capex"]}[Data]
    in
        Table;

DimScenario =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "dim_scenario"]}[Data]
    in
        Table;

SimulationRun =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "simulation_run"]}[Data]
    in
        Table;

FactSimulation =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "fact_simulation"]}[Data]
    in
        Table;

KpiScenario =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "v_kpi_scenario"]}[Data]
    in
        Table;

CompareScenarios =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "v_compare_scenarios"]}[Data]
    in
        Table;

ScenarioEvolution =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "v_scenario_evolution"]}[Data]
    in
        Table;

DimSupplier =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "dim_supplier"]}[Data]
    in
        Table;

DimCountry =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "dim_country"]}[Data]
    in
        Table;

DimRiskLevel =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "dim_risk_level"]}[Data]
    in
        Table;

DecisionSummary =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "v_decision_summary"]}[Data]
    in
        Table;

DecisionRisk =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "v_decision_risk"]}[Data]
    in
        Table;

SupplierPerformance =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "v_supplier_performance"]}[Data]
    in
        Table;

ImportRiskAnalysis =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "v_import_risk_analysis"]}[Data]
    in
        Table;

ProcurementSummary =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "v_procurement_summary"]}[Data]
    in
        Table;

RiskAnalysis =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "v_risk_analysis"]}[Data]
    in
        Table;

SupplierRanking =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "v_supplier_ranking"]}[Data]
    in
        Table;

CountryRisk =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "v_country_risk"]}[Data]
    in
        Table;

ImportComplexity =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "v_import_complexity"]}[Data]
    in
        Table;

DimContainer =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "dim_container"]}[Data]
    in
        Table;

FactShipment =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "fact_shipment"]}[Data]
    in
        Table;

FactLogisticsCost =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "fact_logistics_cost"]}[Data]
    in
        Table;

ContainerUtilization =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "v_container_utilization"]}[Data]
    in
        Table;

ShipmentPerformance =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "v_shipment_performance"]}[Data]
    in
        Table;

LogisticsCosts =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "v_logistics_costs"]}[Data]
    in
        Table;

DeliveryRisk =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "v_delivery_risk"]}[Data]
    in
        Table;

SupplierLogistics =
    let
        Source = PostgreSQL.Database("localhost", "sp2i_capex"),
        Table = Source{[Schema = "public", Item = "v_supplier_logistics"]}[Data]
    in
        Table;
