# Worked examples

Each example is a proven instantiation of the skeleton. Start from the nearest
one rather than the blank skeleton when the domain matches.

## Example 1: Chess opening trainer (Alien Gambit vs. Caro-Kann, playing Black)

Why each section is shaped the way it is:

- The **self-test replaying every line** is the load-bearing instruction —
  from/to square coordinates are exactly where a model hallucinates, and a wrong
  board that renders confidently is worse than an error banner.
- **"Verify or omit"** beats "be accurate": it gives the model a legal way out
  of inventing theory.
- **Trap moves for the trainee's side are first-class data** — a trainer that
  only knows the right move can't explain *why* the natural-looking move loses,
  and in a gambit the explanation of the punishment is most of the value.
- **No chess engine** — an opening trainer only needs a move tree; the board is
  derived by replaying tree moves, and input validates against the tree, not
  chess rules.

```
Build me an interactive chess opening trainer as a single self-contained HTML file.

OPENING: [the Alien Gambit against the Caro-Kann]
I PLAY: [Black]
LINE TO REACH IT: [1.e4 c6 2.d4 d5 3.Nd2 dxe4 4.Nxe4 Nf6 5.Ng5 h6 6.Nxf7 Kxf7
7.Nf3 — include the 3.Nc3 move-order transposition]

RESEARCH FIRST (do not skip):
- Before writing any code, research this opening's current theory (web search;
  Lichess opening explorer / chess.com opening pages if reachable). Build a move
  tree covering the top 2–4 opponent tries at every branch point, going 10–12
  plies deep past the defining position. Only include moves you verified against
  sources — if you cannot verify a line, leave it out rather than guess.
- Every one of MY moves gets a 1–2 sentence explanation of why it's right.
  Known mistake moves for my side get entries too, marked as traps, with an
  explanation of how they lose — so the trainer can explain my wrong answer
  when I play one, not just reject it.
- End each line with a short plain-language summary of the resulting plan.

ARCHITECTURE (do not deviate):
- One HTML file, zero external resources (no CDNs, no fonts, no images) so it
  works offline and as an artifact. Inline CSS + vanilla JS.
- DO NOT write a chess move-legality engine. Encode the opening as a move tree
  where every move stores {san, from, to} plus flags for castling / en passant /
  promotion / which piece type moves. The board position is derived only by
  replaying tree moves from the start position. Input is validated against the
  tree, not against chess rules.
- On page load, run a self-test that replays every line in the tree and checks
  each move is consistent (the piece named in the SAN is actually on the from-
  square, captures land on occupied squares, etc.). If any line fails, show a
  red error banner naming the broken line instead of rendering a wrong board.

BOARD & UX:
- Unicode chess pieces, large and readable; board oriented with MY color at the
  bottom; coordinates on the edges; last move highlighted; click a piece then a
  destination to move (show dots on the tree-legal destinations of a selected
  piece). Light and dark friendly colors.
- Opponent moves play automatically after a ~600ms delay.

MODES:
1. LEARN — step through each variation move by move with the explanations
   shown, next/back buttons, and a variation picker listing every line by name.
2. DRILL — the trainer plays the opponent side, choosing randomly among the
   branches (weighted toward the most common). I must find my move. Wrong move:
   shake + show why it's wrong if it's a known trap, generic "not the move"
   otherwise; after 2 misses reveal the answer with its explanation. A hint
   button shows the piece to move. Track per-line pass/fail in localStorage and
   show a coverage panel (which lines I've completed, success rate) with a reset
   button.
- A header line stating the opening, my color, and one sentence of strategic
  context. If reaching this opening requires a specific earlier move choice of
  mine, say so.

Finish by testing: open the file (or trace the self-test logic by hand), confirm
the self-test passes for every line, and tell me how many lines and total moves
the tree contains.
```

To reuse for another opening, change only the three bracketed slots at the top.
