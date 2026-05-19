import React from "react";
import { ChevronDown, Loader2, Search, X } from "lucide-react";

export default function AnalyticsSelect({
  label,
  value,
  options = [],
  placeholder = "Tous",
  loading = false,
  onChange,
}) {
  const [open, setOpen] = React.useState(false);
  const [search, setSearch] = React.useState("");
  const ref = React.useRef(null);
  const selected = options.find((option) => option.value === value);
  const placeholderByLabel = {
    batiment: "Choisir un batiment...",
    niveau: "Choisir un niveau...",
    lot: "Rechercher un lot...",
    famille: "Choisir une famille metier...",
    "import/local": "Choisir local ou import...",
  };
  const searchPlaceholder = placeholderByLabel[label.toLowerCase()] || `Rechercher ${label.toLowerCase()}...`;
  const filteredOptions = React.useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return options;
    return options.filter((option) => option.label.toLowerCase().includes(query));
  }, [options, search]);

  React.useEffect(() => {
    const close = (event) => {
      if (ref.current && !ref.current.contains(event.target)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const selectOption = (option) => {
    onChange(option?.value || "");
    setSearch("");
    setOpen(false);
  };

  return (
    <div className="analytics-select-field" ref={ref}>
      <span>{label}</span>
      <button type="button" className={open ? "analytics-select-control open" : "analytics-select-control"} onClick={() => setOpen((state) => !state)}>
        <strong>{selected?.label || placeholder}</strong>
        {loading ? <Loader2 className="spin" size={14} /> : value ? <X size={14} onClick={(event) => { event.stopPropagation(); selectOption(null); }} /> : <ChevronDown size={15} />}
      </button>
      {open ? (
        <div className="analytics-select-menu">
          <label className="analytics-select-search">
            <Search size={14} />
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={searchPlaceholder} autoFocus />
          </label>
          <button type="button" className="analytics-select-option muted" onClick={() => selectOption(null)}>
            {placeholder}
          </button>
          <div className="analytics-select-options">
            {filteredOptions.length ? (
              filteredOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={option.value === value ? "analytics-select-option selected" : "analytics-select-option"}
                  onClick={() => selectOption(option)}
                >
                  {option.label}
                </button>
              ))
            ) : (
              <p className="analytics-select-empty">Aucun resultat</p>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
