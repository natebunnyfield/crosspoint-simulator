# Albo's capitals against three width systems

**Owner ask, 2026-09-15:** *"make a version of capitals that matches 'trajan',
'humanist' and 'helvetica' widths (needs research in md files)."* This is that
research. Nothing is drawn yet; this doc is the measurement the drawing has to
hit, and `tools/wedge_serif/cmp_capwidths.py` re-runs it in one command.

```
python3 cmp_capwidths.py <albo-regular.ttf>
```

## The unit, and why it is not the em

Every width here is the **advance over that face's own H-ink cap height**. It
cannot be the em: the cap-to-em ratio runs 0.596 (Dante) to 0.753 (Trajan)
across these faces, so an em-relative width would mostly measure how big each
designer drew their capitals, not how wide. Albo's is 0.676.

The **humanist** column is the MEDIAN of five faces -- Coelacanth, Libris ADF,
Dante MT, Van den Keere, Doves Type -- so that no single cut's quirk becomes
the model. Trajan and Helvetica are each a single face because each one IS its
own system. Trajan Pro is Adobe-licensed and sits in the firmware repo's
gitignored `lib/EpdFont/local_fonts/`.

## What actually separates the three, measured

It is not overall width. It is **the ratio of the round letters to the square
ones** -- median of C D G O Q over median of B E F L P S:

| system | median cap | round | square | **round / square** | spread (no I J) |
|---|---|---|---|---|---|
| Trajan | 0.958 | 1.215 | 0.798 | **1.522** | 1.93x |
| humanist | 1.047 | 1.128 | 0.864 | **1.306** | 2.07x |
| **Albo today** | **1.111** | **1.146** | **0.907** | **1.264** | **2.30x** |
| Helvetica | 0.930 | 1.084 | 0.930 | **1.166** | 1.70x |

Trajan is the Roman inscriptional system: the round letters are half again as
wide as the square ones, because they were laid out on a circle and a half-
square. Helvetica is modular -- B C D E H N O all land within 0.93..1.08, which
is what makes it look engineered. Humanist sits between, and **Albo already
sits with the humanist group and slightly flatter than it**.

So the three variants are not three widths, they are three JOBS:

- **Trajan-width**: narrow the set ~14% AND open round/square from 1.264 to
  1.522 -- the round letters barely move, the square ones lose a lot. Chiefly
  E F L S B P narrower and D O Q C held.
- **Humanist-width**: narrow ~6%, raise round/square 1.264 -> 1.306. The small
  one; Albo is nearly there already.
- **Helvetica-width**: narrow ~16% and FLATTEN round/square to 1.166, which
  means widening the square letters relative to the rounds. The opposite move
  from Trajan, and the one that fights the pen hardest.

## Per letter, advance over cap height

| | Trajan | humanist | Helvetica | Albo | Albo/Trajan | Albo/hum | Albo/Helv |
|---|---|---|---|---|---|---|---|
| A | 0.930 | 1.012 | 0.930 | 1.118 | 1.203 | 1.105 | 1.203 |
| B | 0.912 | 0.875 | 0.930 | 0.914 | 1.002 | 1.045 | 0.983 |
| C | 1.069 | 1.064 | 1.007 | 1.034 | 0.967 | 0.971 | 1.027 |
| D | 1.218 | 1.135 | 1.007 | 1.104 | 0.906 | 0.973 | 1.096 |
| E | 0.810 | 0.887 | 0.930 | 0.963 | 1.189 | 1.086 | 1.036 |
| F | 0.786 | 0.811 | 0.852 | 0.862 | 1.097 | 1.064 | 1.013 |
| G | 1.145 | 1.118 | 1.084 | 1.146 | 1.001 | 1.026 | 1.057 |
| H | 1.275 | 1.215 | 1.007 | 1.291 | 1.013 | 1.063 | 1.283 |
| I | 0.584 | 0.490 | 0.387 | 0.407 | 0.696 | 0.831 | 1.050 |
| J | 0.550 | 0.483 | 0.697 | 0.607 | 1.103 | 1.256 | 0.870 |
| K | 0.999 | 1.031 | 0.930 | 1.152 | 1.154 | 1.118 | 1.239 |
| L | 0.786 | 0.880 | 0.775 | 0.956 | 1.216 | 1.086 | 1.232 |
| M | 1.394 | 1.372 | 1.161 | 1.447 | 1.038 | 1.054 | 1.246 |
| N | 1.258 | 1.206 | 1.007 | 1.312 | 1.043 | 1.088 | 1.303 |
| O | 1.215 | 1.152 | 1.084 | 1.149 | 0.946 | 0.998 | 1.060 |
| P | 0.853 | 0.854 | 0.930 | 0.899 | 1.055 | 1.053 | 0.967 |
| Q | 1.222 | 1.128 | 1.084 | 1.149 | 0.941 | 1.019 | 1.060 |
| R | 1.001 | 1.039 | 1.007 | 1.061 | 1.059 | 1.021 | 1.053 |
| S | 0.757 | 0.778 | 0.930 | 0.734 | 0.969 | 0.943 | 0.789 |
| T | 0.918 | 1.007 | 0.852 | 1.099 | 1.198 | 1.092 | 1.291 |
| U | 1.102 | 1.156 | 1.007 | 1.206 | 1.094 | 1.042 | 1.197 |
| V | 0.985 | 1.054 | 0.930 | 1.151 | 1.168 | 1.092 | 1.238 |
| W | 1.461 | 1.610 | 1.316 | 1.686 | 1.154 | 1.048 | 1.282 |
| X | 0.922 | 1.090 | 0.930 | 1.163 | 1.262 | 1.066 | 1.250 |
| Y | 0.869 | 0.988 | 0.930 | 1.093 | 1.259 | 1.106 | 1.176 |
| Z | 0.919 | 1.065 | 0.852 | 1.132 | 1.231 | 1.063 | 1.329 |

Two things to read off it before drawing anything. **Albo is wider than all
three at almost every letter** (median 116% of Trajan, 106% of humanist, 119.5%
of Helvetica) -- the exceptions are S, C, O, Q, D, B, P, where it is at or
under. And **Albo's I is the narrowest of the four** at 0.407 against Trajan's
0.584, so the one letter a Trajan variant must make WIDER is the I.

## Not settled here

- Which of the three the owner actually wants shipped, or whether all three.
- Whether a variant is a separate cut, a `wdth`-style parameter on the caps
  only, or a stylistic set. `garalde_caps.json` already holds per-glyph solved
  widths from four garalde faces and is how the capitals are currently sized,
  so it is the natural place for a second and third column.
- Lowercase is untouched by any of this. Trajan has no true lowercase.
