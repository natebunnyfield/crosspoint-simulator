**Kept Legibility Index (v3.1, 9-26 px, 8-bit) and the e hint gate (8-12 ppem)**

| arm | roman grand | roman crowded | roman e>o Vision | roman e>o Tesseract | italic grand | italic e>o | e gate (worst mouth_block) |
|---|---|---|---|---|---|---|---|
| TODAY | 88.0 | 60.4 | 136 | 17 | 86.4 | 6 | FAIL 0.243 |
| TTFA default (qsq) | 88.0 | 54.5 | 130 | 31 | 86.7 | 7 | FAIL 0.255 |
| TTFA natural (nnn) | 88.2 | 51.8 | 3 | 0 | - | - | ok 0.141 |
| TTFA strong (sss) | - | - | - | - | - | - | FAIL 0.263 |
| LIGHT | 88.6 | 57.0 | 6 | 0 | 86.4 | 6 | ok 0.118 |
| NO HINTING | 88.7 | 58.0 | 2 | 0 | 86.7 | 5 | FAIL 0.267 |
| Georgia (ref) | 94.0 | 91.7 | 0 | 0 |  |  |  |

**Apple Vision on the converter's own 2-bit pixels (index corpus, 4 shuffles per size)**

| arm | 9 px | 1x worst | 1x mean | 2x worst | e>o at reader sizes |
|---|---|---|---|---|---|
| TODAY R | 81.1 | 99.66 | 99.93 | 99.80 | 0 |
| TODAY I | 54.7 | 99.49 | 99.89 | 99.80 | 0 |
| TTFA default (qsq) R | 79.1 | 99.73 | 99.90 | 99.93 | 0 |
| TTFA default (qsq) I | 46.4 | 99.32 | 99.85 | 99.80 | 0 |
| LIGHT R | 69.7 | 99.73 | 99.92 | 99.93 | 0 |
| LIGHT I | 54.7 | 99.49 | 99.89 | 99.80 | 0 |
| NO HINTING R | 76.1 | 99.70 | 99.88 | 99.93 | 0 |
| NO HINTING I | 52.7 | 99.80 | 99.93 | 99.86 | 0 |

**Regular, the six reader sizes at 1x (8 10 12 14 16 18 pt = 16.7-37.5 ppem)**

| arm | colour vs outline, per size | per-letter colour sd | stem shapes, per size | stem spread px, per size | flat edge crisp | round edge crisp | flat edge spread px (worst) |
|---|---|---|---|---|---|---|---|
| TODAY | 1.08 1.06 1.07 1.04 1.10 1.10 | 0.072 | 2 2 2 3 3 2 | 0.33 0.67 1.00 1.33 1.00 1.33 | 1.00 | 0.87 | 0.00 |
| TTFA default (qsq) | 1.06 0.98 0.99 1.01 1.00 1.00 | 0.048 | 3 6 6 6 6 7 | 0.33 1.00 1.33 1.33 1.33 1.67 | 1.00 | 0.85 | 0.33 |
| TTFA natural (nnn) | 1.05 0.97 0.99 1.01 1.00 1.00 | 0.046 | 3 6 6 6 6 7 | 0.33 1.00 1.33 1.33 1.33 1.67 | 0.95 | 0.85 | 0.33 |
| TTFA strong (sss) | 1.07 0.98 0.99 1.01 1.00 1.00 | 0.049 | 3 6 6 6 6 7 | 0.33 1.00 1.33 1.33 1.33 1.67 | 1.00 | 0.85 | 0.33 |
| LIGHT | 1.06 0.97 0.99 1.01 1.00 1.01 | 0.043 | 3 6 6 6 6 7 | 0.33 1.00 1.00 1.33 1.67 2.00 | 0.95 | 0.87 | 0.33 |
| NO HINTING | 0.97 0.99 1.00 1.01 0.99 1.00 | 0.037 | 4 6 6 6 6 7 | 2.00 1.00 1.33 1.33 1.33 0.67 | 0.90 | 0.67 | 0.33 |

**Regular, the 2x tier, 10-18 pt drawn at 20-36 pt = 41.7-75 ppem (its 8 pt is 16 pt at 1x, already above)**

| arm | colour vs outline | stem shapes | flat edge crisp |
|---|---|---|---|
| TODAY | 1.09 1.07 1.04 0.99 1.00 | 2 2 4 3 1 | 1.00 |
| TTFA default (qsq) | 1.02 0.99 1.00 1.01 0.99 | 5 7 5 5 5 | 1.00 |
| TTFA natural (nnn) | 1.03 0.99 1.00 1.01 0.99 | 5 7 5 5 5 | 0.84 |
| TTFA strong (sss) | 1.02 0.99 1.00 1.01 0.99 | 5 7 5 5 5 | 1.00 |
| LIGHT | 1.04 0.99 1.01 1.01 0.99 | 5 7 5 5 5 | 0.86 |
| NO HINTING | 1.00 0.99 1.00 1.00 0.99 | 5 7 5 5 5 | 0.90 |

**Italic, the six reader sizes at 1x (8 10 12 14 16 18 pt = 16.7-37.5 ppem)**

| arm | colour vs outline, per size | per-letter colour sd | stem shapes, per size | stem spread px, per size | flat edge crisp | round edge crisp | flat edge spread px (worst) |
|---|---|---|---|---|---|---|---|
| TODAY | 0.94 0.98 1.00 1.02 1.03 0.98 | 0.024 | 8 6 7 9 7 10 | 1.33 1.33 1.33 1.33 2.00 1.67 | 0.90 | 0.86 | 1.00 |
| TTFA default (qsq) | 0.95 0.98 1.00 1.01 1.03 0.98 | 0.026 | 8 6 7 9 8 9 | 1.33 1.33 1.33 1.33 2.00 1.67 | 0.90 | 0.84 | 1.00 |
| TTFA natural (nnn) | 0.95 0.98 1.00 1.01 1.03 0.98 | 0.026 | 8 6 7 9 8 9 | 1.33 1.33 1.33 1.33 2.00 1.67 | 0.90 | 0.84 | 1.00 |
| TTFA strong (sss) | 0.96 0.98 1.00 1.01 1.02 0.98 | 0.028 | 8 6 7 9 9 10 | 1.33 1.33 1.33 1.33 2.00 1.67 | 0.90 | 0.84 | 1.00 |
| LIGHT | 0.94 0.98 1.00 1.02 1.03 0.98 | 0.024 | 8 6 7 9 7 10 | 1.33 1.33 1.33 1.33 2.00 1.67 | 0.90 | 0.86 | 1.00 |
| NO HINTING | 0.97 0.98 0.99 0.99 0.99 1.00 | 0.021 | 7 6 8 9 7 8 | 1.33 1.33 1.33 1.67 1.33 1.67 | 0.90 | 0.77 | 1.00 |

**Italic, the 2x tier, 10-18 pt drawn at 20-36 pt = 41.7-75 ppem (its 8 pt is 16 pt at 1x, already above)**

| arm | colour vs outline | stem shapes | flat edge crisp |
|---|---|---|---|
| TODAY | 0.99 1.01 1.02 1.00 1.01 | 9 8 9 10 9 | 0.84 |
| TTFA default (qsq) | 0.99 1.00 1.01 1.00 1.01 | 10 8 10 10 10 | 0.83 |
| TTFA natural (nnn) | 0.99 1.00 1.01 1.00 1.01 | 10 8 10 10 10 | 0.83 |
| TTFA strong (sss) | 0.99 1.00 1.01 1.00 1.01 | 10 8 10 10 10 | 0.83 |
| LIGHT | 0.99 1.01 1.02 1.00 1.01 | 9 8 9 10 9 | 0.84 |
| NO HINTING | 1.00 1.00 1.00 1.00 1.00 | 10 7 11 10 10 | 0.90 |
