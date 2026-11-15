"""
Red-Team toolkit for the Cascade-Lattice Cipher.

Everything here uses ONLY what a Red Team receives: the public plaintext/ciphertext pairs, plus a
word list. It never reads the secret keys. Main entry point: red_team_attack(pairs, words).

Idea (known-plaintext, dictionary attack on the Playfair keyword)
-----------------------------------------------------------------
After the Mirror-5 layer is undone, position i of the text equals
        S2[i] = SQ[ (pos(L1[i]) + shift_i) mod 25 ]
where L1 is the Playfair output and pos() is the index of a letter in the keyed square SQ.
shift_i depends only on i (not on the message), so for the RIGHT square the value
        d[j][i] = pos(S2_j[i]) - pos(L1_j[i])  (mod 25)
is identical for every correct pair j.  A wrong square gives unrelated numbers.  So:
  1. guess the Mirror layer (block size and pattern) and undo it,
  2. for every candidate keyword build its square and count how many pairs agree on d at each position,
  3. the keyword with a near-perfect agreement score is the Playfair keyword,
  4. the shifts d[.][i] are the cascade shifts; the period m satisfies shift[i+m] = shift[i] + 1,
  5. pairs that disagree with the consensus are the incorrect ones.
"""
from collections import Counter
import time
import numpy as np

from cipher import normalise, keyed_alphabet, pf_prepare, playfair, ALPHA25, BLOCK

L2I = {c: i for i, c in enumerate(ALPHA25)}


# ------------------------------------------------------------------ statistics
def ioc(text: str) -> float:
    """Index of coincidence. English ~0.067, random 26 letters ~0.038, random 25 letters 0.040."""
    c, n = Counter(text), len(text)
    return sum(v * (v - 1) for v in c.values()) / (n * (n - 1)) if n > 1 else 0.0


def periodic_ioc(text: str, max_period: int = 20) -> list:
    """Mean IoC of the columns for every period 1..max_period (the Friedman/Kasiski-style test).
    A plain Vigenere with key length m shows a clear peak at m and its multiples."""
    out = []
    for p in range(1, max_period + 1):
        cols = [text[i::p] for i in range(p)]
        out.append(float(np.mean([ioc(c) for c in cols])))
    return out


def letter_freq(text: str) -> dict:
    c, n = Counter(text), len(text)
    return {ch: c.get(ch, 0) / n for ch in ALPHA25}


# ------------------------------------------------------------------ Mirror hypotheses
def unmirror(text: str, size: int, pattern: str) -> str:
    """Undo a block-reversal hypothesis. pattern: none | odd | even | all (reversal is an involution)."""
    blocks = [text[i:i + size] for i in range(0, len(text), size)]
    out = []
    for n, b in enumerate(blocks):
        rev = (pattern == "all") or (pattern == "odd" and n % 2 == 0) or (pattern == "even" and n % 2 == 1)
        out.append(b[::-1] if rev else b)
    return "".join(out)


def mirror_hypotheses():
    hyps = [(1, "none")]
    for size in range(3, 9):
        for pattern in ("odd", "even", "all"):
            hyps.append((size, pattern))
    return hyps


# ------------------------------------------------------------------ vectorised dictionary scoring
def build_square_table(words):
    """Return (kept_words, pos) where pos[w, L2I[ch]] = index of ch in the keyed square of word w."""
    seen, kept, rows = set(), [], []
    for w in words:
        w = normalise(w)
        if not (3 <= len(w) <= 25) or w in seen:
            continue
        seen.add(w)
        sq = keyed_alphabet(w)
        row = [0] * 25
        for idx, ch in enumerate(sq):
            row[L2I[ch]] = idx
        kept.append(w)
        rows.append(row)
    return kept, np.array(rows, dtype=np.int16)


def _shift_table(pos, unmirrored, prepared, npos):
    """d[j, i, w] = pos(S2_j[i]) - pos(L1_j[i]) mod 25 for every candidate square w."""
    J, W = len(prepared), pos.shape[0]
    D = np.empty((J, npos, W), dtype=np.int8)
    for j in range(J):
        for t in range(0, npos, 2):
            a, b = L2I[prepared[j][t]], L2I[prepared[j][t + 1]]
            pa, pb = pos[:, a], pos[:, b]
            ra, ca, rb, cb = pa // 5, pa % 5, pb // 5, pb % 5
            same_r, same_c = ra == rb, ca == cb
            oa = np.where(same_r, ra * 5 + (ca + 1) % 5, np.where(same_c, ((ra + 1) % 5) * 5 + ca, ra * 5 + cb))
            ob = np.where(same_r, rb * 5 + (cb + 1) % 5, np.where(same_c, ((rb + 1) % 5) * 5 + cb, rb * 5 + ca))
            sa, sb = pos[:, L2I[unmirrored[j][t]]], pos[:, L2I[unmirrored[j][t + 1]]]
            D[j, t] = (sa - oa) % 25
            D[j, t + 1] = (sb - ob) % 25
    return D


def agreement_scores(pos, unmirrored, prepared, npos):
    """Number of agreeing pair-couples summed over positions (higher = more consistent)."""
    D = _shift_table(pos, unmirrored, prepared, npos)
    J = D.shape[0]
    score = np.zeros(pos.shape[0], dtype=np.int32)
    for i in range(npos):
        for a in range(J):
            for b in range(a + 1, J):
                score += (D[a, i] == D[b, i])
    return score


# ------------------------------------------------------------------ the attack
def prepare_public(pairs):
    """Red-Team assumption from the data itself: ciphertext length is even and longer than the number of
    plaintext letters when a filler was inserted, so the Playfair filler rule is used on the plaintext."""
    prepared = [pf_prepare(p["plaintext"]) for p in pairs]
    cts = [normalise(p["ciphertext"]) for p in pairs]
    length_ok = [len(a) == len(b) for a, b in zip(prepared, cts)]
    return prepared, cts, length_ok


def recover_stream(sq, prepared, unmirrored, min_support=3):
    """Majority shift per position, the pairs' mismatches, the key period and the key letters."""
    J = len(prepared)
    L = max(len(x) for x in prepared)
    pos = {c: i for i, c in enumerate(sq)}
    d = [[None] * L for _ in range(J)]
    for j in range(J):
        l1 = playfair(prepared[j], sq, +1)
        for i in range(len(l1)):
            d[j][i] = (pos[unmirrored[j][i]] - pos[l1[i]]) % 25
    shifts, bad = [], [0] * J
    for i in range(L):
        vals = [d[j][i] for j in range(J) if d[j][i] is not None]
        if len(vals) < min_support:
            break
        mode, cnt = Counter(vals).most_common(1)[0]
        shifts.append(mode)
        for j in range(J):
            if d[j][i] is not None and d[j][i] != mode:
                bad[j] += 1
    n = len(shifts)
    period = next((m for m in range(2, n // 2 + 1)
                   if all((shifts[i + m] - shifts[i]) % 25 == 1 for i in range(n - m))), None)
    key = "".join(sq[shifts[i]] for i in range(period)) if period else None
    return dict(shifts=shifts, mismatches=bad, period=period, vig_key=key)


def red_team_attack(pairs, words, verbose=True, hypotheses=None, scan_positions=10):
    t0 = time.time()
    prepared, cts, length_ok = prepare_public(pairs)
    kept, pos = build_square_table(words)
    if verbose:
        print(f"[1] {len(kept):,} candidate keywords, ciphertext lengths match Playfair-prepared lengths: {all(length_ok)}")
    npos = min(len(p) for p in prepared)
    npos -= npos % 2
    # --- step 1: find the Mirror layer ---------------------------------------------------------
    results = []
    for size, pattern in (hypotheses or mirror_hypotheses()):
        unm = [unmirror(c, size, pattern) for c in cts]
        sc = agreement_scores(pos, unm, prepared, scan_positions)
        results.append((int(sc.max()), size, pattern, int(sc.argmax())))
    results.sort(reverse=True)
    best_score, size, pattern, widx = results[0]
    if verbose:
        print("[2] Mirror hypotheses (best agreement score each, top 4):")
        for s, sz, pt, _ in results[:4]:
            print(f"      block={sz} pattern={pt:<5} score={s}")
    # --- step 2: full-length score with the winning hypothesis ----------------------------------
    unm = [unmirror(c, size, pattern) for c in cts]
    sc = agreement_scores(pos, unm, prepared, npos)
    order = np.argsort(sc)[::-1][:3]
    word = kept[int(order[0])]
    if verbose:
        print("[3] Top keywords:", [(kept[int(i)], int(sc[i])) for i in order],
              f"(max possible if all {len(pairs)} pairs agreed: {npos * len(pairs) * (len(pairs) - 1) // 2})")
    # --- step 3: stream, period, key, wrong pairs -----------------------------------------------
    sq = keyed_alphabet(word)
    rec = recover_stream(sq, prepared, unm)
    flagged = [j + 1 for j, b in enumerate(rec["mismatches"]) if b > 0]
    out = dict(mirror_block=size, mirror_pattern=pattern, playfair_keyword=word, square=sq,
               vigenere_key=rec["vig_key"], period=rec["period"], shifts=rec["shifts"],
               mismatches=rec["mismatches"], flagged_pairs=flagged, scores=[(kept[int(i)], int(sc[i])) for i in order],
               hypothesis_scores=[(s, sz, pt) for s, sz, pt, _ in results], n_words=len(kept),
               seconds=round(time.time() - t0, 1))
    if verbose:
        print(f"[4] Playfair keyword: {word}   Vigenere key: {rec['vig_key']} (period {rec['period']})")
        print(f"[5] Mismatches per pair: {rec['mismatches']}  ->  incorrect pairs: {flagged}   ({out['seconds']} s)")
    return out
