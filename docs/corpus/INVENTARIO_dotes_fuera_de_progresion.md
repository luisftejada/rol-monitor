# Inventario previo — dotes concedidas fuera de `clases.<slug>.progresion`

Barrido completo del manual básico (577 pp.), no solo del capítulo 3. **No se ha tocado
el YAML.** Este documento sirve para dimensionar el esquema antes de escribirlo.

Páginas = paginación impresa (PDF físico = impresa + 1).

## Método

1. `pdftotext -layout` sobre las 577 páginas → 35 páginas con alguna coincidencia de
   `dote adicional` / `como dote` / `dote extra`.
2. Reextracción **por columnas** (`-x 0 -W 305` y `-x 300 -W 310`) de esas 35, con
   reunificación de las palabras partidas por guión de maquetación.
3. 48 párrafos candidatos, revisados uno a uno y clasificados por origen.
4. Barrido dirigido adicional sobre dominios (41–48), escuelas arcanas (70–73), talentos
   de pícaro (80–83) y clases de prestigio (373–405), para no depender de que la frase
   cayera en una página ya marcada.
5. Cada nombre de dote contrastado contra `dotes.lista[].nombre`.

---

## ⚠ Dos correcciones al informe anterior

**1. Me equivoqué de origen en dos dotes.** Dije que Liderazgo y Lucha a ciegas venían de
aptitudes del druida. **No: son dominios de clérigo.** Lo deduje de la proximidad en el
texto extraído sin recortar columnas, y la columna contigua era del druida. Corregido
abajo.

**2. Dije que ninguna clase de prestigio concede dotes. Es falso.** Lo verifiqué contra
`clases_de_prestigio.<slug>.progresion[].especial`, y resulta que **ese campo está vacío
en las diez clases** — no es que no haya dotes, es que no hay datos:

| Clase de prestigio | Niveles con `especial` | Filas en `progresion` |
|---|---|---|
| arquero_arcano, asesino, bribon_arcano, caballero_arcano, discipulo_del_dragon, maestro_del_saber, teurgo_mistico | 0 | 10 |
| duelista | 0 | **1** |
| cronista_pathfinder, danzarin_sombrio | 0 | **0** |

Tres de esas clases sí conceden dotes (§5). Y `duelista`, `cronista_pathfinder` y
`danzarin_sombrio` tienen la tabla de progresión **truncada o ausente**, lo cual es un
agujero del corpus anterior a este encargo y probablemente merezca su propia tarea.

---

## 1. Dominios de clérigo — 3 dotes

`clases.clerigo` no tiene clave `dominios`. Son ~20 dominios; solo tres conceden dote.

| Dominio | Dote | Nivel | pág. | Nota |
|---|---|---|---|---|
| Nobleza | Liderazgo | 8 | 46 | además **+2 a la puntuación de Liderazgo**, y es **condicional**: se mantiene «mientras sigas los mandatos de tu dios» |
| Oscuridad | Lucha a ciegas | 1 | 46 | dentro de «Poderes concedidos» |
| Runas | Inscribir pergamino | 1 | 47 | dentro de «Poderes concedidos» |

El de Nobleza es el único caso de todo el manual de una dote adicional **revocable**. Si
el motor la trata como concesión permanente, se equivocará en mesa cuando el DJ aplique
la condición.

## 2. Escuelas arcanas de mago — 1 dote

`clases.mago` no tiene clave `escuelas_arcanas` (existe `magia.escuelas`, pero es la
taxonomía de conjuros, no la aptitud de clase).

| Escuela | Dote | Nivel | pág. |
|---|---|---|---|
| Nigromancia | **Comandar muertos vivientes** *o* **Expulsar muertos vivientes** | 1 | 71 |

Es una elección entre dos, así que en el esquema actual sería `eleccion: lista` con una
lista restringida de dos opciones — no `fija`.

## 3. Talentos de pícaro — 2 dotes

`clases.picaro` no tiene clave `talentos`. Son ~20 talentos; dos conceden dote. Se
escogen a 2º nivel y cada 2 niveles.

| Talento | Dote | pág. |
|---|---|---|
| Entrenamiento en armas | Soltura con un arma | 82 |
| Pícaro sutil | Sutileza con las armas | 82 |

No van atados a un nivel fijo: dependen de cuándo el jugador gaste un hueco de talento.

## 4. Competencias automáticas (capítulo 5) — 5 dotes

Este eje **no lo había detectado antes** y es el más transversal: cinco dotes que las
clases otorgan automáticamente, descritas en el apartado «Especial» de la propia dote,
no en el capítulo de clases.

| Dote | Clases que la obtienen automáticamente | pág. |
|---|---|---|
| Competencia con armadura ligera | todas **excepto** monje, hechicero y mago | 121 |
| Competencia con armadura intermedia | bárbaro, clérigo, druida, guerrero, paladín, explorador | 121 |
| Competencia con armadura pesada | guerrero, paladín | 121 |
| Competencia con escudo | bárbaro, bardo, clérigo, druida, guerrero, paladín, explorador | 122 |
| Competencia con escudo pavés | guerrero | 122 |

Hoy esto vive en `clases.<slug>.competencias` como **prosa libre**. Importa que sean
dotes de verdad y no solo prosa porque **son prerrequisitos de otras dotes**: Competencia
con escudo lo es de Golpear con el escudo mejorado, que a su vez está en la lista de
estilo de dos armas del explorador. Sin modelarlas, la validación de prerrequisitos
fallará en cadena.

### Error de datos encontrado de paso

`clases.explorador.competencias` dice **«armaduras ligeras y escudos (no pavés)»**. El
manual (pág. 55) dice: *competente con todas las armas sencillas y marciales, con las
armaduras ligeras **e intermedias**, y con los escudos (excepto los escudos paveses)*.
**Falta «intermedias»**, y coincide con que la pág. 121 sí lista al explorador entre
quienes obtienen Competencia con armadura intermedia. Dos fuentes independientes contra
el corpus. No lo he corregido porque queda fuera del encargo, pero conviene arreglarlo.

## 5. Clases de prestigio — 3 clases

| Clase | Qué concede | Niveles | pág. |
|---|---|---|---|
| Caballero arcano | dote **de combate** | 1, 5, 9 | 380 |
| Discípulo del dragón | dote de linaje dracónico | 2, 5, 8 | 387 |
| Maestro del saber | vía «secretos»: *Salud secreta* → **Dureza**; *Conocimientos aplicables* → **1 dote libre** | según secreto | 391 |

El caballero arcano **sí debe cumplir prerrequisitos** (a diferencia del explorador y el
monje).

El discípulo del dragón remite explícitamente a la pág. 64: reutiliza la lista del linaje
dracónico. En el YAML ya existe como
`dotes.listas_restringidas.dotes_de_linaje_hechicero.opciones.draconico` — se apunta ahí,
no hay que duplicar nada.

### Caso que parece dote y no lo es

El **duelista** obtiene *el beneficio de* Reflejos de combate (4º, pág. 389) y *el
beneficio de* Desviar flechas (9º, pág. 390) al usar un arma perforante ligera o a una
mano. El manual dice «el beneficio de la dote», no «la dote». **No cuenta como
prerrequisito** y es **condicional al arma empuñada**. Si se modela como dote adicional,
se abre la puerta a construcciones ilegales.

## 6. Compañero animal — 1 dote

Pág. 52: obtiene **Ataque múltiple** si tiene 3 o más ataques naturales y aún no la
tiene; si no llega a los tres ataques, obtiene en su lugar un segundo ataque natural
con penalizador −5.

## 7. Fuera de alcance

- **Pág. 452** — creación de PNJ («Empieza asignando todas las dotes concedidas por las
  aptitudes de clase»). Módulo NPC, diferido por decisión de proyecto.
- **Pág. 407** — avance más allá de nivel 20; menciona las dotes del guerrero solo para
  decir que siguen progresando.
- **Pág. 112** — regla general: cualquier dote marcada como de Combate puede ser dote
  adicional de guerrero. Ya recogido implícitamente en `guerrero.dotes_adicionales`.

---

## Nombres que **no** existen en el corpus

Uno solo, de las 15 dotes del inventario:

**`Ataque múltiple`** (compañero animal, pág. 52). No está en `dotes.lista` y **no es un
fallo de extracción**: no aparece en la Tabla 5-1 del manual básico. Es una dote de
monstruo del Bestiario, citada de pasada. Si se modelan compañeros animales habrá que
decidir si entra en el catálogo o se marca como externa.

Las otras 14 existen con nombre exacto: Liderazgo, Lucha a ciegas, Inscribir pergamino,
Comandar muertos vivientes, Expulsar muertos vivientes, Soltura con un arma, Sutileza con
las armas, Dureza, Competencia con armadura ligera / intermedia / pesada, Competencia con
escudo, Competencia con escudo pavés, y (como beneficio, no dote) Reflejos de combate y
Desviar flechas.

---

## Recuento

| Eje | Dotes | ¿Existe el contenedor en el corpus? |
|---|---|---|
| Dominios de clérigo | 3 | ❌ no hay `dominios` |
| Escuelas arcanas de mago | 1 (elección entre 2) | ❌ no hay `escuelas_arcanas` |
| Talentos de pícaro | 2 | ❌ no hay `talentos` |
| Competencias automáticas | 5 | ⚠ existe como prosa en `competencias` |
| Clases de prestigio | 3 clases | ⚠ existe `progresion`, pero **vacía** |
| Compañero animal | 1 | ❌ no hay `companeros` |

## Lo que esto implica para el esquema

Tres observaciones, sin proponer estructura todavía:

1. **Cuatro de los seis ejes no cuelgan de un nivel de clase**, sino de una *elección*
   (dominio, escuela, talento). El `dotes_adicionales[].nivel` actual no los expresa:
   harían falta claves distintas, colgando del subsistema, no de `clases`.
2. **Las competencias automáticas sí encajan** en la forma actual — son
   `nivel: 1, eleccion: fija` — pero duplicarían información que ya está en
   `competencias`. Hay que decidir cuál es la fuente de verdad antes de escribir.
3. **Hay dos condicionalidades** que la forma actual no sabe expresar: la revocabilidad
   del Liderazgo del dominio de la nobleza y la dependencia del arma del duelista. Ambas
   afectan al motor de apilamiento, que es el núcleo del proyecto.

Mi recomendación de orden, si sigues: **primero las clases de prestigio** (el contenedor
ya existe, solo está vacío, y tres de ellas conceden dotes), **después las competencias
automáticas** (cinco dotes, y desbloquean la validación de prerrequisitos), y **dejar
dominios / escuelas / talentos** para cuando esos subsistemas se modelen por sí mismos,
que es un encargo mucho mayor que las dotes.
