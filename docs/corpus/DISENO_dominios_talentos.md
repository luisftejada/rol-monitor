# Diseño — `dominios`, `escuelas_arcanas` y `talentos`

Propuesta de esquema. **No hay parche**: esto es para decidir la forma antes de escribir
datos. El fragmento de referencia (`propuesta_esquema.yaml`) carga y sus referencias
cruzadas validan contra el corpus real.

Páginas = paginación impresa.

---

## El hecho que decide el diseño

**Los dominios no son del clérigo.** El druida, a 1er nivel, elige entre compañero animal
y *«uno de los siguientes dominios de clérigo: agua, aire, animal, clima, fuego, plantas,
o tierra»* (pág. 49).

Eso descarta colgarlos de `clases.clerigo.dominios`: habría que duplicar siete entradas o
inventar una referencia entre clases. Y el mismo patrón se repite en todo el manual —
«escoge N de este catálogo, a tal nivel, cada tantos niveles» — con al menos cinco
instancias:

| Subsistema | Pool | Quién elige | Cuándo | Cuántas |
|---|---|---|---|---|
| Dominios | 33 entradas, págs. 41–48 | clérigo | 1 | 2 (limitadas a su dios) |
| Dominios | *el mismo pool* | druida | 1 | 1 de 7, excluyente con compañero animal |
| Escuelas arcanas | 8 + universalista, págs. 70–73 | mago | 1 | 1 escuela + 2 opuestas |
| Talentos de pícaro | ~20, págs. 81–83 | pícaro | 2 | 1 cada 2 niveles |
| Talentos avanzados | ~8, pág. 82 | pícaro | 10 | sustituyen a un talento normal |
| *(Poderes de ira)* | ~20, págs. 32–33 | bárbaro | 2 | 1 cada 2 niveles |

De ahí la propuesta central:

> **Separar el catálogo (*pool*) de la ranura (*slot*).** El pool es un catálogo
> compartido de primer nivel. El slot vive en la clase y solo dice *cuándo, cuántas y con
> qué restricción* se escoge de ese pool.

Sin esa separación, el druida obliga a duplicar datos y los talentos avanzados no tienen
dónde declarar que *sustituyen* a un talento normal.

Incluyo los poderes de ira del bárbaro en la tabla porque tienen exactamente la misma
forma. No los diseño aquí (no los pediste), pero si el esquema no los admite sin cambios,
está mal planteado.

---

## Estructura propuesta

### Pools — tres claves nuevas de primer nivel

```
dominios:            # slug -> dominio        (compartido clérigo/druida)
escuelas_arcanas:    # slug -> escuela        (mago)
talentos:            # pool  -> {metadatos, opciones: slug -> talento}
```

`talentos` lleva un nivel más de anidamiento porque agrupa varios pools (`picaro`,
`picaro_avanzados`, y mañana `barbaro`) y cada uno tiene sus propios metadatos de ranura.

### Slots — clave `elecciones` dentro de cada clase

```yaml
clases:
  druida:
    elecciones:
    - clave: vinculo_con_la_naturaleza
      pool: dominios
      nivel: 1
      cantidad: 1
      subconjunto: [agua, aire, animal, clima, fuego, plantas, tierra]
      excluyente_con: companero_animal
      fuente: pág. 49
```

`pool` admite ruta con punto (`talentos.picaro`) para alcanzar los pools anidados.

### La pieza clave: `dotes_adicionales` se reutiliza tal cual

Cada entrada de pool que conceda una dote lleva **el mismo bloque `dotes_adicionales`**
que ya escribimos para clases y razas, con las mismas claves `eleccion` / `tipos` /
`lista` / `dote` / `fuente`:

```yaml
dominios:
  oscuridad:
    nombre: Oscuridad
    dioses: [Zon-Kuthon]
    pagina: 46
    dotes_adicionales:
    - nivel_de_clase: 1
      eleccion: fija
      dote: Lucha a ciegas
      fuente: pág. 46
```

Beneficio concreto: **un solo camino de código**. El resolutor que ya recorre
`clases.<slug>.dotes_adicionales` recorre esto sin ramas nuevas, y las cinco reglas de
validación que ya escribimos siguen aplicando sin tocarlas.

---

## Tres cambios que el esquema actual necesita

### 1. `nivel` → `nivel_de_clase`, y admitir `null`

En un pool, `nivel: 8` no puede significar «nivel de personaje»: significa **nivel de la
clase que concede la opción**. Un clérigo 8 / guerrero 4 tiene Liderazgo; un clérigo 4 /
guerrero 8, no. Confundirlos es un bug silencioso en multiclase, y el corpus ya tiene
`avance.multiclase`, así que el caso es real.

Y los talentos de pícaro **no tienen nivel**: la dote llega cuando el jugador gasta el
hueco. De ahí `nivel_de_clase: null`, que es información — «esta concesión no está atada a
un nivel» — y no un hueco.

Renombrar dentro de los pools y dejar `nivel` como está en `clases` y `razas` sería
incoherente. Propongo **`nivel_de_clase` en los pools** y mantener `nivel` en clases y
razas, donde sí coinciden. La alternativa —un único nombre en todas partes— obliga a
migrar lo ya entregado. Es la decisión que menos me convence de todo el diseño y la
dejo abierta.

### 2. `condicion` y `revocable`

El Liderazgo del dominio de la nobleza es el único caso del manual de dote adicional que
**se puede perder**: se mantiene *«mientras sigas los mandatos de tu dios»* (pág. 46).

```yaml
    - nivel_de_clase: 8
      eleccion: fija
      dote: Liderazgo
      condicion: mientras el personaje siga los mandatos de su dios o concepto divino
      revocable: true
      fuente: pág. 46
```

Para un rastreador de combate con traza de auditoría esto importa: si el DJ retira la
concesión, la traza tiene que poder decir *por qué* desapareció el bonificador, no
limitarse a que no está. `revocable: true` es lo que permite renderizar «suprimida por
condición de dominio» en vez de que el modificador se evapore.

También cubre al duelista (§5 del inventario), que obtiene *el beneficio* de dos dotes
solo mientras empuñe un arma perforante ligera o a una mano.

### 3. `origen` implícito por la ruta

No propongo clave nueva: la ruta del pool **ya es** la procedencia
(`dominios.oscuridad` → «Dominio de la oscuridad»). Basta con que el resolutor la
arrastre al construir el modificador para que la traza diga de dónde sale cada bonificador
sin duplicar el dato en el YAML.

---

## Detalles que el fragmento resuelve

- **Enlace con `magia.escuelas`.** `escuelas_arcanas.<slug>.escuela_de_magia` apunta a la
  taxonomía de conjuros que ya existe. Ojo: `magia.escuelas` está **en minúscula**
  (`nigromancia`, no `Nigromancia`). Lo detecté al validar el fragmento; sin esa
  comprobación se colaba.
- **Elección entre dotes.** La nigromancia da Comandar muertos vivientes *o* Expulsar
  muertos vivientes: es `eleccion: lista`, no `fija`, apuntando a una lista restringida
  de dos.
- **Escuelas opuestas.** No conceden nada, encarecen conjuros. Van como slot con
  `tipo: penalizacion` para que no se confundan con una concesión.
- **Talentos avanzados.** `sustituye_a: picaro` declara que consumen un hueco del otro
  pool en vez de añadir uno.
- **Contenedores vacíos.** `poderes: []` y `conjuros: []` quedan declarados desde el
  primer día aunque solo se rellenen las dotes. Añadir los 9 conjuros de cada dominio
  después no toca el esquema, solo añade datos.

---

## Validación a añadir

Sobre las cinco reglas actuales, seis más, todas comprobables sin ejecutar el motor:

1. Todo `pool` de un slot resuelve a una clave existente (con ruta con punto).
2. Todo `subconjunto` referencia slugs que existen en ese pool.
3. Todo `excluyente_con` referencia una aptitud declarada de esa clase.
4. Todo `escuela_de_magia` existe en `magia.escuelas`, respetando mayúsculas.
5. Toda entrada con `revocable: true` tiene `condicion` no vacía, y viceversa.
6. Todo `sustituye_a` referencia otro pool de `talentos`.

Las tres primeras y la cuarta ya están implementadas en el script con el que validé el
fragmento.

---

## Volumen y fases

| Fase | Contenido | Entradas | Riesgo |
|---|---|---|---|
| A | Esqueleto: los tres pools con `nombre`, `pagina` y contenedores vacíos, más `elecciones` en las 4 clases | 33 + 9 + 28 | bajo, mecánico |
| B | Las 6 `dotes_adicionales` del inventario | 6 | bajo, ya verificadas |
| C | `poderes` de dominios y escuelas | ~80 | **alto**: prosa densa, cada poder tiene su propia mecánica |
| D | `conjuros` de dominio | 33 × 9 = 297 referencias | medio: hay que casar contra `pathfinder_conjuros.yaml` |

**A y B cierran lo que el rastreador de combate necesita hoy.** C y D son la mitad de un
capítulo del manual y no aportan nada al apilamiento de bonificadores de combate; los
dejaría fuera hasta que haya una razón concreta.

---

## Lo que no me convence, dicho claro

1. **`nivel` vs `nivel_de_clase`** es un compromiso feo. Un solo nombre sería más limpio,
   pero obliga a migrar lo ya entregado y validado. Tú decides si prefieres la coherencia
   o el diff pequeño.
2. **`talentos` con doble anidamiento** rompe la simetría con `dominios` y
   `escuelas_arcanas`. La alternativa —tres pools hermanos `talentos_picaro`,
   `talentos_picaro_avanzados`, `poderes_de_ira`— es más plana pero pierde el sitio
   natural para `nivel_minimo` y `cada_n_niveles`.
3. **Sigo pensando que este no es el orden óptimo.** Las clases de prestigio son 3 dotes
   con el contenedor ya existente y vacío; las competencias automáticas son 5 dotes que
   desbloquean la validación de prerrequisitos en cadena. Ambas cosas son más baratas y
   más útiles para el motor que los 70 registros de esqueleto de la fase A. Dicho esto,
   el diseño de aquí arriba se sostiene por sí solo y no depende de en qué orden lo hagas.
