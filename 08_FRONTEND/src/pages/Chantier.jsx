import Indicateur from "../components/Indicateur";

export default function Chantier() {
  return (
    <main className="page chantier">
      <header className="entete-page">
        <p>Vue Chantier</p>
        <h1>Controle DQE et metriques terrain</h1>
      </header>

      <section className="grille-indicateurs">
        <Indicateur libelle="Lignes DQE" valeur="JSON normalise" />
        <Indicateur libelle="Anomalies" valeur="Audit qualite" tonalite="alerte" />
        <Indicateur libelle="Zones" valeur="Batiment / niveau" />
      </section>

      <section className="bandeau-metier">
        <h2>Lecture operationnelle</h2>
        <p>
          Les equipes chantier disposent d'une base metree propre par lot,
          batiment, niveau, unite, statut et cle metier BI.
        </p>
      </section>
    </main>
  );
}
