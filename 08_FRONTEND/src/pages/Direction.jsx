import React from "react";
import Indicateur from "../components/Indicateur";

export default function Direction() {
  return (
    <main className="page direction">
      <header className="entete-page">
        <p>Vue Direction</p>
        <h1>Pilotage CAPEX SP2I</h1>
      </header>

      <section className="grille-indicateurs">
        <Indicateur libelle="CAPEX local" valeur="A consolider" />
        <Indicateur libelle="CAPEX optimise" valeur="Pipeline BI" tonalite="succes" />
        <Indicateur libelle="Economies nettes" valeur="Calcul import" tonalite="alerte" />
      </section>

      <section className="bandeau-metier">
        <h2>Arbitrage achats et construction</h2>
        <p>
          La direction suit les postes importables, les economies nettes et les
          familles qui portent le plus fort impact CAPEX.
        </p>
      </section>
    </main>
  );
}
