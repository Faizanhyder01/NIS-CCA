"""
Blue Team challenge generator for the Cascade-Lattice Cipher (CT-486 CCA - Classical Cipher Challenge).

    python blue_team_challenge.py           builds the 10 pairs, writes the answer key and the Red Team sheet,
                                            then runs a Red-Team style attack that uses ONLY the public pairs.

Faults used for the three intentionally incorrect pairs (all keep the correct length and valid letters):
    pair 3  Type C  one ciphertext letter altered
    pair 6  Type B  the Mirror-5 step skipped
    pair 8  Type A  near-miss Vigenere keyword (CASCODE instead of CASCADE)
"""
import json
import os

from cipher import (PLAYFAIR_KEY, VIGENERE_KEY, encrypt, decrypt, normalise, pf_prepare, group5)

HERE = os.path.dirname(os.path.abspath(__file__))
WRONG_VIG_KEY = "CASCODE"
FLIP = {"index": 7, "shift": 6}          # 0-based ciphertext index, +6 on the 25-letter alphabet
ALPHA25 = "ABCDEFGHIKLMNOPQRSTUVWXYZ"

MESSAGES = [
    "Attack at dawn from the north gate",
    "Never trust unverified network traffic",
    "The firewall blocks every unknown port",          # 3 incorrect
    "Strong keys protect weak messages",
    "Karachi hosts a secure operations center",
    "Encryption turns plain words into noise",         # 6 incorrect
    "A packet travels through many routers",
    "Cryptanalysis rewards patient analysts",          # 8 incorrect
    "The red team will find every pattern",
    "Security is a process not a product",
]
FAULTS = {3: "flip", 6: "nomirror", 8: "nearkey"}
FAULT_TEXT = {
    "flip": ("Corrupted letter", "Type C - letter 8 of the correct ciphertext was shifted six places along the alphabet."),
    "nomirror": ("Wrong sequence", "Type B - Playfair and Cascade done correctly but Mirror-5 skipped."),
    "nearkey": ("Near-miss key", "Type A - encrypted with CASCODE instead of CASCADE (fifth key letter differs)."),
}


def build():
    pairs = []
    for n, msg in enumerate(MESSAGES, start=1):
        true_ct = encrypt(msg)
        kind = FAULTS.get(n, "correct")
        if kind == "flip":
            raw = normalise(true_ct)
            j = FLIP["index"]
            raw = raw[:j] + ALPHA25[(ALPHA25.index(raw[j]) + FLIP["shift"]) % 25] + raw[j + 1:]
            ct = group5(raw)
        elif kind == "nomirror":
            ct = encrypt(msg, do_mirror=False)
        elif kind == "nearkey":
            ct = encrypt(msg, vg_key=WRONG_VIG_KEY)
        else:
            ct = true_ct
        pairs.append(dict(n=n, plaintext=msg, ciphertext=ct, valid=kind == "correct", fault=kind,
                          true_ciphertext=true_ct, how=FAULT_TEXT.get(kind, ("", "Encrypted with the real key."))[1]))
    return pairs


def full_check(pairs):
    rows = []
    for p in pairs:
        ok = decrypt(p["ciphertext"]) == pf_prepare(p["plaintext"])
        rows.append((p["n"], p["valid"], ok))
    assert all(v == ok for _, v, ok in rows), "a correct pair failed or an incorrect pair decrypted"
    assert sum(v for _, v, _ in rows) == 7
    return rows


def write_outputs(pairs):
    os.makedirs(os.path.join(HERE, "answer_key"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "challenge"), exist_ok=True)
    with open(os.path.join(HERE, "answer_key", "challenge_pairs.json"), "w") as f:
        json.dump(pairs, f, indent=1)
    sheet = [{"n": p["n"], "plaintext": p["plaintext"], "ciphertext": p["ciphertext"]} for p in pairs]
    with open(os.path.join(HERE, "challenge", "challenge_sheet.json"), "w") as f:
        json.dump(sheet, f, indent=1)
    with open(os.path.join(HERE, "challenge", "challenge_sheet.txt"), "w") as f:
        f.write("Cascade-Lattice Cipher - Challenge Sheet (7 correct pairs, 3 incorrect)\n\n")
        for p in sheet:
            f.write(f"{p['n']}. PT: {p['plaintext']}\n   CT: {p['ciphertext']}\n")


def load_words():
    try:
        from english_words import get_english_words_set
        return sorted(get_english_words_set(["web2"], lower=True, alpha=True))
    except Exception:
        print("english-words not installed: falling back to a tiny demo list (pip install english-words).")
        return ["meridian", "lattice", "cascade", "network", "security", "cipher", "monarchy", "playfair"]


if __name__ == "__main__":
    pairs = build()
    print("Keys (SECRET):", PLAYFAIR_KEY, VIGENERE_KEY)
    for n, v, ok in full_check(pairs):
        print(f"pair {n:2d}  intended {'correct  ' if v else 'incorrect'}  decrypts back to plaintext: {ok}")
    write_outputs(pairs)
    print("\nRed-Team attack on the public sheet only:")
    from attacks import red_team_attack
    public = [{"plaintext": p["plaintext"], "ciphertext": p["ciphertext"]} for p in pairs]
    res = red_team_attack(public, load_words())
    assert res["playfair_keyword"] == PLAYFAIR_KEY.upper() and res["vigenere_key"] == VIGENERE_KEY.upper()
    assert res["flagged_pairs"] == [p["n"] for p in pairs if not p["valid"]]
    print("\nAttack result matches the answer key.")
