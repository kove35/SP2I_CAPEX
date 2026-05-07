import Indicateur from "../components/Indicateur";

export default function Import() {
  return (
    <main className="page import">
      <header className="entete-page">
        <p>Vue Import</p>
        <h1>Optimisation Pointe-Noire</h1>
      </header>

      <section className="grille-indicateurs">
        <Indicateur libelle="Incoterm" valeur="FOB" />
        <Indicateur libelle="Port" valeur="Pointe-Noire" />
        <Indicateur libelle="Decision" valeur="Import / Local" tonalite="succes" />
      </section>

      <section className="bandeau-metier">
        <h2>Landed cost complet</h2>
        <p>
          Le moteur applique transport, assurance, douane, frais portuaires et
          logistique locale avant arbitrage CAPEX.
        </p>
      </section>
    </main>
  );
}
