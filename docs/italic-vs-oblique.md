# What an italic is, and why Albo's was an oblique — 2026-09-14

Owner, on the round-103 page: *"research what italic is because you're just
doing an oblique."*

Page: https://claude.ai/artifact/ASURG4g4NyfZ82u3PebFHF

He is right, and this document is the proof, the measurement that settles it,
and the list of what an actual italic would require. Written because rounds
100–103 shipped four increasingly elaborate versions of the wrong thing, each
one defended with a measurement that was answering a different question.

---

## 1. The measurement that settles it

An **oblique** is the roman, slanted. A **true italic** is a different set of
skeletons, descended from a cursive hand, that happens also to slope.

So the test is mechanical: **shear a family's roman by its own italic's angle,
and see how much of its italic that accounts for.** Per letter, normalized to
a common height and registered horizontally, intersection over union:

| family | italic slant | overlap of the italic with its OWN roman, sheared |
|---|---|---|
| ITC Berkeley | 7° | **0.306** |
| Coelacanth | 14° | **0.431** |
| **Albo (round 103)** | 13° | **0.852** |

1.00 would mean the italic *is* the sheared roman — a pure oblique. The two
real italics sit at 0.31 and 0.43. Albo sits at **0.85**.

And the per-letter breakdown says exactly what happened:

```
Albo, least like its own sheared roman:
  o 0.35   f 0.46   a 0.61   r 0.84   x 0.86   k 0.87   m 0.88   n 0.89
```

**Those are the only three letters I actually redrew** — the o (narrowed), the
f (made to descend) and the a (single-storey). Everything else — n, m, h, u,
b, d, p, q, l, k, z — is the roman with a shear applied. The whole
apparatus of round 101's "five levers measured off real italics" changed
*proportions*, and proportions are not what makes an italic.

Compare where the real ones differ most:

```
Coelacanth:    l 0.12   k 0.14   m 0.15   z 0.18   n 0.22   h 0.23
ITC Berkeley:  f 0.14   h 0.22   q 0.23   m 0.24   w 0.24   k 0.24   b 0.25
```

The letters a real italic changes hardest are the **arch letters** (n m h),
the **ascenders** (l b h k) and the **diagonals** (k w z) — precisely the ones
Albo left alone.

Instrument: `outlines/cmp/oblique.py`. Run it against any roman/italic pair.

---

## 2. Where my earlier measurement went wrong

Round 102 reported that "neither model branches low — both arches join at
0.96–0.97 of the x-height, the same as their romans", and used that to set
`IT_BRANCH` to a token 0.15.

**That measurement was of the wrong end of the arch.** It found where the arch
*meets the right stem*, which is near the x-height in every face, roman and
italic alike, because that is where an arch lands. The italic question is
where the arch **leaves the left stem** — the branch — and the detector I
wrote could not see it: it looked for the lowest y with two ink runs, which in
any n is the baseline, because the two feet are two runs.

So a real difference was measured, found absent, and reported as a finding
that shut down the very lever that mattered. A wrong measurement is worse than
no measurement, because it carries the authority of a number.

---

## 3. What a true italic actually changes

Read off the rendering of Coelacanth's italic beside its own sheared roman
(`scratchpad/oblique-proof.png`, reproduced on the round-104 page), letter by
letter:

**The construction, not the proportions:**

1. **The arch branches out of the stem, low, and tapers.** In a roman n the
   arch springs off a shoulder near the top of the left stem. In an italic it
   *leaves the stem* around mid-height as a thinning branch and arcs over. The
   n, m, h, u, b, p, r and k all follow from this one change; it is the single
   biggest item on the list.
2. **The lowercase loses its foot serifs.** The stems end in a curved exit,
   not a wedge. Round 103 added an optional exit but kept the wedge beside it
   by default; a written letter has one or the other, never both.
3. **The ascenders take an entry, not a top wedge.** l, b, h, k, d begin with
   an angled or curved entry stroke.
4. **The k's leg curves**, and its arm meets the stem differently — Coelacanth
   and Berkeley both change the k more than almost any other letter.
5. **The z changes form entirely** — a curved, often descending tail.
6. **The bowls join their stems lower and are more pointed** (b d p q), the
   o with them: a written oval has two changes of direction, not four.
7. **The letters narrow and the rhythm tightens**, which is the part round 101
   did get right, and which on its own accomplishes nothing.

**What stays:** the pen, the contrast, the x-height, the serif *family* where
serifs survive. That is what keeps an italic in the same typeface as its
roman rather than being a second face bolted on.

---

## 4. Albo's italic: the standing state

`Albo-Italic.ttf` as shipped in round 103 is **an oblique with three redrawn
letters and an optional flick**. It is honest to call it that and wrong to
call it an italic. Its measured overlap with the sheared roman is 0.852.

What it does have, which a redraw should keep: 13° (his ruling), the o's
width solved to the references' mean, the single-storey a now derived from the
o, the descending f, the entry and exit machinery in `primitives.stem`, and a
weight solved so its ink at 13 pt matches the roman's (61.8% against 61.9%).

What it needs is section 3, items 1–6 — new skeletons, drawn, not dialled.
The levers cannot get there: `IT_BRANCH` moves where an existing roman arch
starts, but a roman arch started low is still a roman arch.

---

## 5. Rule for the next time

**A proportion is not a construction.** Every number in rounds 101 and 102 was
real and correctly measured, and all of them together moved the overlap from
about 0.95 to 0.85 when the target was 0.35. When a thing is defined by its
skeleton, measuring its widths will confirm whatever you already built.

The check that would have caught it on day one is the one in section 1, and it
takes a minute: shear the roman and see what is left to explain.
