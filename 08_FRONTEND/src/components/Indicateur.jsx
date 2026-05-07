export default function Indicateur({ libelle, valeur, tonalite = "neutre" }) {
  return (
    <article className={`indicateur indicateur-${tonalite}`}>
      <span>{libelle}</span>
      <strong>{valeur}</strong>
    </article>
  );
}
