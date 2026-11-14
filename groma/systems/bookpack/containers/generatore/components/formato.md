---
type: C4 Component
title: Formato del pack
status: stable
groma:
  id: formato
  parent: generatore
  code:
    - scanner: python
      file: generator/src/bookpack/models.py
    - scanner: python
      file: generator/src/bookpack/validate.py
  technology: Pydantic
description: Modelli del pack, export dello schema JSON e controlli dei vincoli.
---

Definisce `*.bookpack.json` con Pydantic. `bookpack schema` ne ricava `schema/bookpack.schema.json`, da cui il lettore genera i suoi tipi TypeScript. I controlli verificano anche ciò che lo schema non esprime, come lunghezze e pagine delle card.
