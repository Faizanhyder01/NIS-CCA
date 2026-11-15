"""
Experiments for the report. Writes results/results.json.   python experiments.py   (about 2-3 minutes)
Corpus: data/sample_plaintext.txt (public domain text, Project Gutenberg).
"""
import json
import math
import os
import random
import re
import time

from cipher import (normalise, keyed_alphabet, pf_prepare, playfair, cascade, mirror, encrypt,
                    PLAYFAIR_KEY, VIGENERE_KEY)
from attacks import ioc, periodic_ioc, letter_freq, red_team_attack
from blue_team_challenge import build, load_words

HERE = os.path.dirname(os.path.abspath(__file__))
random.seed(486)

corpus_raw = open(os.path.join(HERE, "data", "sample_plaintext.txt"), encoding="utf-8", errors="ignore").read()
corpus = normalise(corpus_raw)
LONG = corpus[:20000]
res = {"corpus_letters": len(corpus), "sample_letters": len(LONG)}

# ---- E1: IoC after each layer -------------------------------------------------------------
sq = keyed_alphabet(PLAYFAIR_KEY)
p1 = pf_prepare(LONG)
s1 = playfair(p1, sq, +1)
s2 = cascade(s1, sq, VIGENERE_KEY, +1)
s3 = mirror(s2)
res["ioc_stages"] = {"plaintext": ioc(LONG), "after_playfair": ioc(s1), "after_cascade": ioc(s2), "after_mirror": ioc(s3),
                     "random_25": 1 / 25}
res["english_freq"] = letter_freq(LONG)

# ---- E2: periodic IoC (does the key period show?) -----------------------------------------
def plain_vigenere(text, key):
    k = [ord(ch) - 65 for ch in key]
    return "".join(chr((ord(ch) - 65 + k[i % len(k)]) % 26 + 65) for i, ch in enumerate(text))

static = normalise(encrypt(LONG, do_mirror=False, progressive=False))
full = normalise(encrypt(LONG))
res["periodic_ioc"] = {"plain_vigenere": periodic_ioc(plain_vigenere(corpus[:20000].replace("J", "I"), VIGENERE_KEY), 21),
                       "playfair_static_vigenere": periodic_ioc(static, 21),
                       "cascade_lattice": periodic_ioc(full, 21)}

# ---- E3: key space (bits) ------------------------------------------------------------------
res["keyspace_bits"] = {"Caesar": math.log2(26), "Vigenere (7 letters)": 7 * math.log2(26),
                        "Hill 2x2": math.log2(157248), "Playfair (all 25! squares)": math.log2(math.factorial(25)),
                        "Cascade-Lattice (upper bound)": math.log2(math.factorial(25)) + 7 * math.log2(25)}

# ---- E4: attack on the real challenge ---------------------------------------------------------
words = load_words()
pairs = [{"plaintext": p["plaintext"], "ciphertext": p["ciphertext"]} for p in build()]
r = red_team_attack(pairs, words, verbose=False)
res["challenge_attack"] = {k: r[k] for k in ("mirror_block", "mirror_pattern", "playfair_keyword", "vigenere_key", "period",
                                             "mismatches", "flagged_pairs", "scores", "hypothesis_scores", "n_words", "seconds")}
res["challenge_ct_freq"] = letter_freq("".join(normalise(p["ciphertext"]) for p in build() if p["valid"]))
res["challenge_ioc"] = ioc("".join(normalise(p["ciphertext"]) for p in build() if p["valid"]))

# ---- E5: how many correct pairs does the Red Team need? -----------------------------------------
def random_sentence():
    words_ = re.findall(r"[A-Za-z]+", corpus_raw)
    while True:
        i = random.randrange(0, len(words_) - 12)
        s, n = [], 0
        for w in words_[i:i + 12]:
            s.append(w); n += len(w)
            if 28 <= n <= 36:
                return " ".join(s)
            if n > 36:
                break

succ = {}
for k in (2, 3, 4, 5, 7):
    ok, trials = 0, 6
    for _ in range(trials):
        msgs = [random_sentence() for _ in range(k)]
        pr = [{"plaintext": m, "ciphertext": encrypt(m)} for m in msgs]
        out = red_team_attack(pr, words, verbose=False, hypotheses=[(5, "odd")])
        ok += out["playfair_keyword"] == "MERIDIAN" and out["vigenere_key"] == "CASCADE"
    succ[k] = {"success": ok, "trials": trials}
    print("pairs", k, succ[k], flush=True)
res["pairs_needed"] = succ

# ---- E6: effect of a non-dictionary keyword (the fix) -----------------------------------------------
hard = {}
for kw in ("QXZVWKT", "ZZQXJKV"):
    pr = [{"plaintext": p["plaintext"], "ciphertext": encrypt(p["plaintext"], pf_key=kw)} for p in pairs]
    out = red_team_attack(pr, words, verbose=False, hypotheses=[(5, "odd")])
    hard[kw] = {"found": out["playfair_keyword"], "recovered": out["playfair_keyword"] == normalise(kw)}
res["non_dictionary_keys"] = hard

json.dump(res, open(os.path.join(HERE, "results", "results.json"), "w"), indent=1)
print(json.dumps({k: res[k] for k in ("ioc_stages", "challenge_ioc", "pairs_needed", "non_dictionary_keys")}, indent=1))
print("challenge attack seconds:", res["challenge_attack"]["seconds"])
