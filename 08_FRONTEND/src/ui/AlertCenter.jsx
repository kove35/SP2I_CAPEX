import React from "react";
import { Bell } from "lucide-react";

export default function AlertCenter() {
  return (
    <button className="alert-center" type="button" title="Alertes">
      <Bell size={16} />
      <span>3</span>
    </button>
  );
}
