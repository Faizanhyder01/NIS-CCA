"""
Cascade-Lattice Cipher (CLC-25)  -  CT-486 Network and Information Security, Classical Cipher Challenge
=====================================================================================================

Three layers over a 25-letter alphabet (A-Z with J merged into I):

    1. Playfair            digraph substitution on a 5x5 square built from PLAYFAIR_KEY
    2. Cascade Vigenere    Vigenere over the KEYED alphabet (the Playfair square order);
                           shift_i = (k[i mod m] + floor(i / m)) mod 25   (the shift grows each pass)
    3. Mirror-5            cut into blocks of 5, reverse blocks 1, 3, 5, ... ; print in groups of 5

Decryption runs the layers in reverse. Educational project: classical ciphers are NOT secure.
"""
import re

PLAYFAIR_KEY = "MERIDIAN"
VIGENERE_KEY = "CASCADE"
BLOCK = 5
ALPHA25 = "ABCDEFGHIKLMNOPQRSTUVWXYZ"


# ---------------------------------------------------------------- helpers
def normalise(text: str) -> str:
    """Rule R1: upper-case, keep A-Z only, merge J into I."""
    return re.sub(r"[^A-Z]", "", text.upper()).replace("J", "I")


def keyed_alphabet(keyword: str) -> str:
    """Rule R2: keyword letters first (no repeats), then the rest of the 25-letter alphabet."""
    seen, out = set(), []
    for ch in normalise(keyword) + ALPHA25:
        if ch not in seen:
            seen.add(ch)
            out.append(ch)
    return "".join(out)


def group5(text: str) -> str:
    return " ".join(text[i:i + 5] for i in range(0, len(text), 5))


# ---------------------------------------------------------------- layer 1: Playfair
def pf_prepare(text: str) -> str:
    """Rule R3: split into digraphs; a double letter gets a filler X (a Q when the letter is X);
    an odd last letter is padded the same way."""
    t, out, i = normalise(text), [], 0
    while i < len(t):
        a = t[i]
        b = t[i + 1] if i + 1 < len(t) else None
        if b is None or a == b:
            out.append(a + ("Q" if a == "X" else "X"))
            i += 1
        else:
            out.append(a + b)
            i += 2
    return "".join(out)


def _pf_pair(sq: str, a: str, b: str, d: int) -> str:
    ra, ca = divmod(sq.index(a), 5)
    rb, cb = divmod(sq.index(b), 5)
    if ra == rb:
        return sq[ra * 5 + (ca + d) % 5] + sq[rb * 5 + (cb + d) % 5]
    if ca == cb:
        return sq[((ra + d) % 5) * 5 + ca] + sq[((rb + d) % 5) * 5 + cb]
    return sq[ra * 5 + cb] + sq[rb * 5 + ca]


def playfair(text: str, sq: str, d: int) -> str:
    """d = +1 encrypts, d = -1 decrypts. `text` must already be prepared (even length, no doubles)."""
    return "".join(_pf_pair(sq, text[i], text[i + 1], d) for i in range(0, len(text), 2))


# ---------------------------------------------------------------- layer 2: Cascade Vigenere
def cascade(text: str, sq: str, key: str, d: int) -> str:
    """Rule R4: Vigenere on the keyed alphabet; every full pass of the key adds one to all shifts."""
    k = [sq.index(c) for c in normalise(key)]
    m = len(k)
    return "".join(sq[(sq.index(ch) + d * ((k[i % m] + i // m) % 25)) % 25] for i, ch in enumerate(text))


# ---------------------------------------------------------------- layer 3: Mirror-5
def mirror(text: str) -> str:
    """Rule R5: reverse blocks 1, 3, 5, ... of five letters (a short last block is reversed too).
    Reversing is its own inverse, so the same function encrypts and decrypts."""
    blocks = [text[i:i + BLOCK] for i in range(0, len(text), BLOCK)]
    return "".join(b[::-1] if n % 2 == 0 else b for n, b in enumerate(blocks))


# ---------------------------------------------------------------- public API
def encrypt(plaintext, pf_key=PLAYFAIR_KEY, vg_key=VIGENERE_KEY, do_mirror=True, progressive=True) -> str:
    """Returns the ciphertext in groups of five. `do_mirror` / `progressive` exist only so the
    challenge generator can forge the intentionally wrong pairs and so experiments can compare variants."""
    sq = keyed_alphabet(pf_key)
    s1 = playfair(pf_prepare(plaintext), sq, +1)
    if progressive:
        s2 = cascade(s1, sq, vg_key, +1)
    else:
        k = [sq.index(c) for c in normalise(vg_key)]
        s2 = "".join(sq[(sq.index(c) + k[i % len(k)]) % 25] for i, c in enumerate(s1))
    return group5(mirror(s2) if do_mirror else s2)


def decrypt(ciphertext, pf_key=PLAYFAIR_KEY, vg_key=VIGENERE_KEY) -> str:
    """Returns the Playfair-prepared plaintext (filler X / Q letters are still inside)."""
    sq = keyed_alphabet(pf_key)
    s2 = mirror(normalise(ciphertext))
    s1 = cascade(s2, sq, vg_key, -1)
    return playfair(s1, sq, -1)


def encrypt_trace(plaintext, pf_key=PLAYFAIR_KEY, vg_key=VIGENERE_KEY) -> dict:
    """Every intermediate value (used for the worked example in the report)."""
    sq = keyed_alphabet(pf_key)
    p0, p1 = normalise(plaintext), pf_prepare(plaintext)
    s1 = playfair(p1, sq, +1)
    s2 = cascade(s1, sq, vg_key, +1)
    s3 = mirror(s2)
    k = [sq.index(c) for c in normalise(vg_key)]
    shifts = [(k[i % len(k)] + i // len(k)) % 25 for i in range(len(p1))]
    return dict(square=sq, normalised=p0, prepared=p1, after_playfair=s1, shifts=shifts,
                after_cascade=s2, after_mirror=s3, ciphertext=group5(s3))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Cascade-Lattice Cipher (Playfair -> Cascade Vigenere -> Mirror-5)")
    ap.add_argument("mode", choices=["enc", "dec"])
    ap.add_argument("text")
    ap.add_argument("--pkey", default=PLAYFAIR_KEY, help="Playfair keyword")
    ap.add_argument("--vkey", default=VIGENERE_KEY, help="Vigenere keyword")
    a = ap.parse_args()
    print(encrypt(a.text, a.pkey, a.vkey) if a.mode == "enc" else decrypt(a.text, a.pkey, a.vkey))
