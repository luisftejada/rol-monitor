/**
 * Spanish message catalog. `es` is the only locale for now, but every
 * user-facing string is routed through this layer so a second locale would be a
 * data change, not a code change.
 */
export const es = {
  "app.title": "pf-tracker",
  "app.tagline": "Asistente de combate para Pathfinder 1.ª edición",
  "health.checking": "Comprobando el servicio…",
  "health.ok": "Servicio operativo",
  "health.error": "No se puede contactar con el servicio",
} as const;

export type MessageKey = keyof typeof es;
