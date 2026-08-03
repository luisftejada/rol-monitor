/**
 * Spanish message catalog. `es` is the only locale for now, but every
 * user-facing string is routed through this layer so a second locale would be a
 * data change, not a code change. Game data (ability names, bonus sources) arrives
 * from the API already in Spanish and is rendered verbatim.
 */
export const es = {
  "app.title": "pf-tracker",
  "app.tagline": "Asistente de combate para Pathfinder 1.ª edición",
  "nav.characters": "Personajes",

  "health.checking": "Comprobando el servicio…",
  "health.ok": "Servicio operativo",
  "health.error": "No se puede contactar con el servicio",

  "common.loading": "Cargando…",
  "common.error": "Se ha producido un error",
  "common.retry": "Reintentar",
  "common.back": "Volver",

  "list.title": "Personajes",
  "list.empty": "Aún no hay personajes.",
  "list.search": "Buscar por nombre",
  "list.col.name": "Nombre",
  "list.col.class": "Clase y nivel",
  "list.col.hp": "PG",
  "list.col.ac": "CA",
  "list.col.touch": "Tacto",
  "list.col.flat": "Desprevenido",
  "list.col.init": "Iniciativa",
  "list.col.saves": "Salvaciones",
  "list.col.actions": "Acciones",
  "list.action.open": "Abrir",
  "list.action.duplicate": "Duplicar",
  "list.action.delete": "Eliminar",
  "list.confirmDelete": "¿Eliminar «{name}»?",

  "sheet.abilities": "Características",
  "sheet.ac": "Clase de armadura",
  "sheet.ac.touch": "CA de tacto",
  "sheet.ac.flat": "CA desprevenido",
  "sheet.saves": "Salvaciones",
  "sheet.save.Fortaleza": "Fortaleza",
  "sheet.save.Reflejos": "Reflejos",
  "sheet.save.Voluntad": "Voluntad",
  "sheet.initiative": "Iniciativa",
  "sheet.cmb": "BMC",
  "sheet.cmd": "DMC",
  "sheet.bab": "Ataque base",
  "sheet.attacks": "Ataques",
  "sheet.attack.damage": "Daño",
  "sheet.attack.crit": "Crítico",
  "sheet.attack.notProficient": "No competente",
  "sheet.skills": "Habilidades",
  "sheet.speed": "Velocidad",
  "sheet.speed.feet": "{value} pies",
  "sheet.hp": "Puntos de golpe",
  "sheet.hp.current": "Actuales",
  "sheet.hp.max": "Máx.",
  "sheet.hp.temp": "Temporales",
  "sheet.hp.nonlethal": "No letal",
  "sheet.acp": "Penalizador de armadura",
  "sheet.asf": "Fallo de conjuros arcanos",
  "sheet.warnings": "Avisos",
  "sheet.classSkill": "Habilidad de clase",

  "breakdown.why": "¿Por qué?",
  "breakdown.hide": "Ocultar desglose",
  "breakdown.show": "Ver desglose de {label}",
  "breakdown.suppressed": "Anulados por apilamiento",
  "breakdown.untyped": "sin tipo",
  "breakdown.empty": "Sin bonificadores.",
} as const;

export type MessageKey = keyof typeof es;
