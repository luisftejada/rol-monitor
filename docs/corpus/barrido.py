#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Barrido: toda mencion a una dote concedida, en cualquier capitulo del manual.

PROVENANCE ONLY. This is the throwaway extraction script behind
INVENTARIO_dotes_fuera_de_progresion.md, kept so the inventory can be audited or
redone. It is not part of the build and does not run from this repo: it needs the
per-column text of the PDF under sweep/, which is not vendored.

Trabaja sobre las columnas ya extraidas en sweep/. Reune las lineas partidas por
guion de la maquetacion para que las frases sean legibles.
"""
import glob
import io
import re

PAT = re.compile(r"dote[s]? adicional(?:es)?|como dote|dote extra|obtienes? .{0,40} como dote",
                 re.I)


def reunir(texto):
    """Deshace el corte de palabra a final de linea y junta el parrafo."""
    t = texto.replace("f l", "fl").replace("f i", "fi")
    t = re.sub(r"-\n\s*", "", t)
    t = re.sub(r"\n\s*", " ", t)
    return re.sub(r"\s{2,}", " ", t).strip()


def bloques(lineas):
    """Trocea la columna en parrafos (un parrafo empieza con sangria o tras vacio)."""
    out, actual = [], []
    for ln in lineas:
        if not ln.strip():
            if actual:
                out.append(actual)
                actual = []
            continue
        actual.append(ln)
    if actual:
        out.append(actual)
    return out


filas = []
for path in sorted(glob.glob("sweep/p*_?.txt"),
                   key=lambda p: (int(re.search(r"p(\d+)_", p).group(1)), p)):
    pdf_pg = int(re.search(r"p(\d+)_", path).group(1))
    col = "izq" if path.endswith("_L.txt") else "der"
    lineas = io.open(path, encoding="utf-8").read().split("\n")
    for blq in bloques(lineas):
        texto = reunir("\n".join(blq))
        if PAT.search(texto):
            filas.append((pdf_pg - 1, col, texto))

print("menciones encontradas: %d\n" % len(filas))
for impresa, col, texto in filas:
    print("--- pag. %d (%s) ---" % (impresa, col))
    print(texto[:520])
    print()
