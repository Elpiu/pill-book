---
type: C4 Actor
title: Chi genera i pack
status: stable
groma:
  id: chi-genera-i-pack
---

Prepara i libri sul computer: sceglie il PDF, controlla i capitoli, genera il pack e lo passa al telefono. Spesso è la stessa persona che poi legge.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [chi-genera-i-pack](chi-genera-i-pack.md) | [generator/src/bookpack/cli.py](../../generator/src/bookpack/cli.py) | Genera da terminale | comando bookpack |
| [chi-genera-i-pack](chi-genera-i-pack.md) | [generator/src/bookpack/gui.py](../../generator/src/bookpack/gui.py) | Prepara e genera | finestra Tkinter |
