"""
Carga y consulta del resumen de reglas de Pathfinder (Reglas básicas).

Uso rápido:
    from pathfinder_reglas import Reglas

    r = Reglas.cargar()                         # busca los YAML en el directorio actual
    r.clase("mago").progresion[19]["conjuros"]  # espacios de conjuro a nivel 20
    r.conjuros_de("clérigo", 3)                 # conjuros de clérigo de nivel 3
    r.dotes_disponibles(bab=6, caracteristicas={"Fue": 15})
    r.bab("picaro", 12)                         # +9/+4
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any, Iterable

import yaml

NUCLEO_POR_DEFECTO = "pathfinder_nucleo.yaml"
CONJUROS_POR_DEFECTO = "pathfinder_conjuros.yaml"


def _norm(s: str) -> str:
    """Minúsculas sin acentos, para comparar nombres de forma tolerante."""
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower().strip()


# --------------------------------------------------------------------------- #
#  Modelos ligeros
# --------------------------------------------------------------------------- #

@dataclass
class Clase:
    clave: str
    datos: dict[str, Any]

    def __getattr__(self, nombre: str) -> Any:
        try:
            return self.datos[nombre]
        except KeyError as exc:
            raise AttributeError(nombre) from exc

    def nivel(self, n: int) -> dict[str, Any]:
        """Fila de progresión del nivel n (1-20, o 1-10 en clases de prestigio)."""
        for fila in self.datos["progresion"]:
            if fila["nivel"] == n:
                return fila
        raise ValueError(f"{self.clave}: nivel {n} fuera de rango")

    def salvaciones(self, n: int) -> dict[str, int]:
        f = self.nivel(n)
        return {"fortaleza": f["fort"], "reflejos": f["ref"], "voluntad": f["vol"]}

    def rasgos_hasta(self, n: int) -> list[str]:
        """Rasgos especiales acumulados hasta el nivel n."""
        out = []
        for fila in self.datos["progresion"]:
            if fila["nivel"] > n:
                break
            if fila.get("especial"):
                out.extend(x.strip() for x in fila["especial"].split(",") if x.strip())
        return out

    def es_lanzador(self) -> bool:
        return bool(self.datos.get("lanzador"))

    def __repr__(self) -> str:
        return f"<Clase {self.datos.get('nombre', self.clave)}>"


@dataclass
class Conjuro:
    datos: dict[str, Any]

    def __getattr__(self, nombre: str) -> Any:
        try:
            return self.datos[nombre]
        except KeyError as exc:
            raise AttributeError(nombre) from exc

    @property
    def nombre(self) -> str:
        return self.datos["nombre"]

    def nivel_para(self, clase: str) -> int | None:
        niveles = self.datos.get("niveles") or {}
        objetivo = _norm(clase)
        for k, v in niveles.items():
            if objetivo in _norm(k).split("/"):
                return v
        return None

    def cd_salvacion(self, mod_caracteristica: int, clase: str) -> int | None:
        """CD = 10 + nivel del conjuro + modificador de la característica."""
        n = self.nivel_para(clase)
        return None if n is None else 10 + n + mod_caracteristica

    def __repr__(self) -> str:
        return f"<Conjuro {self.nombre}>"


# --------------------------------------------------------------------------- #
#  Contenedor principal
# --------------------------------------------------------------------------- #

@dataclass
class Reglas:
    nucleo: dict[str, Any]
    conjuros_doc: dict[str, Any] = field(default_factory=dict)

    # ---------------------------------------------------------------- carga
    @classmethod
    def cargar(cls, directorio: str | Path = ".", *, con_conjuros: bool = True) -> "Reglas":
        d = Path(directorio)
        nucleo = yaml.safe_load((d / NUCLEO_POR_DEFECTO).read_text(encoding="utf-8"))
        conj = {}
        if con_conjuros:
            ruta = d / CONJUROS_POR_DEFECTO
            if ruta.exists():
                conj = yaml.safe_load(ruta.read_text(encoding="utf-8"))
        return cls(nucleo=nucleo, conjuros_doc=conj)

    # ------------------------------------------------------------- clases
    def clase(self, nombre: str) -> Clase:
        clave = _norm(nombre)
        for grupo in ("clases", "clases_de_prestigio"):
            for k, v in self.nucleo[grupo].items():
                if clave in (_norm(k), _norm(v.get("nombre", ""))):
                    return Clase(clave=k, datos=v)
        raise KeyError(f"clase desconocida: {nombre}")

    @property
    def clases(self) -> list[str]:
        return list(self.nucleo["clases"])

    @property
    def clases_de_prestigio(self) -> list[str]:
        return list(self.nucleo["clases_de_prestigio"])

    def bab(self, clase: str, nivel: int) -> str:
        return self.clase(clase).nivel(nivel)["bab"]

    def pg_medios(self, clase: str, nivel: int, mod_con: int = 0) -> int:
        """PG con dado máximo a nivel 1 y media redondeada hacia arriba después."""
        dado = int(self.clase(clase).datos["dado_golpe"].lstrip("d"))
        total = dado + mod_con
        media = dado // 2 + 1
        total += (nivel - 1) * (media + mod_con)
        return total

    # --------------------------------------------------------- habilidades
    @property
    def habilidades(self) -> list[dict[str, Any]]:
        return self.nucleo["habilidades"]["lista"]

    def habilidad(self, nombre: str) -> dict[str, Any]:
        objetivo = _norm(nombre)
        for h in self.habilidades:
            if _norm(h["nombre"]) == objetivo:
                return h
        raise KeyError(f"habilidad desconocida: {nombre}")

    def habilidades_de_clase(self, clase: str) -> list[str]:
        clave = self.clase(clase).clave
        return [h["nombre"] for h in self.habilidades if clave in h["clases"]]

    def bonif_habilidad(self, nombre: str, *, rangos: int, mod_caracteristica: int,
                        clase: str | None = None, mod_racial: int = 0,
                        penalizador_armadura: int = 0) -> int:
        h = self.habilidad(nombre)
        total = rangos + mod_caracteristica + mod_racial
        if rangos > 0 and clase and self.clase(clase).clave in h["clases"]:
            total += 3
        if h["penalizador_armadura"]:
            total += penalizador_armadura      # el penalizador ya viene negativo
        return total

    # --------------------------------------------------------------- dotes
    @property
    def dotes(self) -> list[dict[str, Any]]:
        return self.nucleo["dotes"]["lista"]

    def dote(self, nombre: str) -> dict[str, Any]:
        objetivo = _norm(nombre)
        for d in self.dotes:
            if _norm(d["nombre"]) == objetivo:
                return d
        raise KeyError(f"dote desconocida: {nombre}")

    def dotes_por_tipo(self, tipo: str) -> list[dict[str, Any]]:
        objetivo = _norm(tipo)
        return [d for d in self.dotes if any(_norm(t) == objetivo for t in d["tipos"])]

    def dotes_disponibles(self, *, bab: int = 0,
                          caracteristicas: dict[str, int] | None = None,
                          dotes_poseidas: Iterable[str] = ()) -> list[dict[str, Any]]:
        """Filtro aproximado por prerrequisitos numéricos y de dote.

        Interpreta 'ataque base +N' y 'Fue 13'; el resto de prerrequisitos
        (rasgos de clase, rangos de habilidad, texto libre) se ignoran, así que
        el resultado es un superconjunto que conviene revisar.
        """
        caracteristicas = {k.capitalize()[:3]: v for k, v in (caracteristicas or {}).items()}
        poseidas = {_norm(d) for d in dotes_poseidas}
        nombres = {_norm(d["nombre"]) for d in self.dotes}
        out = []
        for d in self.dotes:
            pre = d.get("prerrequisitos")
            if not pre:
                out.append(d)
                continue
            ok = True
            m = re.search(r"ataque base \+(\d+)", pre, re.I)
            if m and bab < int(m.group(1)):
                ok = False
            for car, val in re.findall(r"\b(Fue|Des|Con|Int|Sab|Car)\s*(\d+)", pre):
                if caracteristicas.get(car, 0) < int(val):
                    ok = False
            for trozo in pre.split(","):
                t = _norm(trozo).strip()
                if t in nombres and t not in poseidas and t != _norm(d["nombre"]):
                    ok = False
            if ok:
                out.append(d)
        return out

    # -------------------------------------------------------------- equipo
    @property
    def armas(self) -> list[dict[str, Any]]:
        return self.nucleo["equipo"]["armas"]

    @property
    def armaduras(self) -> list[dict[str, Any]]:
        return self.nucleo["equipo"]["armaduras_y_escudos"]

    def arma(self, nombre: str) -> dict[str, Any]:
        objetivo = _norm(nombre)
        for a in self.armas:
            if _norm(a["nombre"]) == objetivo:
                return a
        raise KeyError(f"arma desconocida: {nombre}")

    def carga(self, fuerza: int) -> dict[str, Any]:
        tabla = self.nucleo["equipo"]["capacidad_de_carga"]["tabla"]
        if fuerza in tabla:
            return tabla[fuerza]
        if fuerza < 1:
            raise ValueError("Fuerza fuera de rango")
        base = self.carga(fuerza - 10)   # por cada +10 de Fuerza, x4 la capacidad
        return {"ligera_max": base["ligera_max"] * 4,
                "media": [x * 4 for x in base["media"]],
                "pesada": [x * 4 for x in base["pesada"]]}

    # -------------------------------------------------------------- varios
    def estado(self, nombre: str) -> dict[str, Any]:
        objetivo = _norm(nombre)
        for e in self.nucleo["estados"]:
            if _norm(e["nombre"]) == objetivo:
                return e
        raise KeyError(f"estado desconocido: {nombre}")

    def raza(self, nombre: str) -> dict[str, Any]:
        objetivo = _norm(nombre)
        for r in self.nucleo["razas"]:
            if objetivo in (_norm(r["clave"]), _norm(r["nombre"])):
                return r
        raise KeyError(f"raza desconocida: {nombre}")

    def px_necesarios(self, nivel: int, ritmo: str = "medio") -> int:
        return self.nucleo["avance"]["px_por_nivel"][nivel][ritmo]

    def nivel_por_px(self, px: int, ritmo: str = "medio") -> int:
        tabla = self.nucleo["avance"]["px_por_nivel"]
        return max(n for n, v in tabla.items() if v[ritmo] <= px)

    # ------------------------------------------------------------ conjuros
    @cached_property
    def _conjuros(self) -> list[Conjuro]:
        return [Conjuro(d) for d in self.conjuros_doc.get("conjuros", [])]

    @property
    def conjuros(self) -> list[Conjuro]:
        return self._conjuros

    def conjuro(self, nombre: str) -> Conjuro:
        objetivo = _norm(nombre)
        for c in self._conjuros:
            if _norm(c.nombre) == objetivo:
                return c
        raise KeyError(f"conjuro desconocido: {nombre}")

    def conjuros_de(self, clase: str, nivel: int | None = None) -> list[Conjuro]:
        objetivo = _norm(clase)
        out = []
        for c in self._conjuros:
            for k, v in (c.datos.get("niveles") or {}).items():
                if objetivo in _norm(k).split("/") and (nivel is None or v == nivel):
                    out.append(c)
                    break
        return sorted(out, key=lambda c: c.nombre)

    def conjuros_por_escuela(self, escuela: str) -> list[Conjuro]:
        objetivo = _norm(escuela)
        return [c for c in self._conjuros if _norm(c.datos.get("escuela") or "") == objetivo]

    def buscar_conjuros(self, texto: str) -> list[Conjuro]:
        objetivo = _norm(texto)
        return [c for c in self._conjuros if objetivo in _norm(c.nombre)]


if __name__ == "__main__":
    r = Reglas.cargar()
    print("clases:", ", ".join(r.clases))
    mago = r.clase("mago")
    print("mago nivel 20 ->", mago.nivel(20))
    print("BAB pícaro 12:", r.bab("picaro", 12))
    print("PG medios guerrero 5 (Con +2):", r.pg_medios("guerrero", 5, 2))
    print("conjuros de clérigo nivel 3:", len(r.conjuros_de("clérigo", 3)))
    bf = r.conjuro("Bola de fuego")
    print("bola de fuego:", bf.escuela, bf.niveles, "CD con Int +5:", bf.cd_salvacion(5, "mago"))
    print("dotes de crítico:", [d["nombre"] for d in r.dotes_por_tipo("Crítico")][:5])
    print("carga con Fue 18:", r.carga(18))
    print("nivel con 40.000 px (medio):", r.nivel_por_px(40000))
