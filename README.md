# Cascade-Lattice Cipher (CLC-25)

**A three-layer classical cipher (Playfair → Cascade Vigenère → Mirror-5) with a Red Team toolkit and a Blue Team challenge dataset.**

CT-486 Network and Information Security · Complex Computing Activity (Classical Cipher Challenge)
NED University of Engineering & Technology · Cyber Security · Batch 2023

| Member | Roll No. |
|---|---|
| Syed Muneeb Ali Shah | CR-23012 |
| Muneeb Ahmed | CR-23021 |
| S.M. Faizan Hyder | CR-23026 |
| Kabeer Ahmed | CR-23034 |
| Muhammad Waleed Kashif | CR-23040 |


## How it works

1. **Playfair** on a 5×5 square built from a secret keyword (J merged into I). A double letter gets a filler `X` (a `Q` when the double is `XX`); an odd tail is padded the same way.
2. **Cascade Vigenère** over the *keyed* alphabet (the square order). `shift_i = (k[i mod m] + ⌊i / m⌋) mod 25`, so every full pass of the key adds one and the key never repeats.
3. **Mirror-5**: cut into blocks of five and reverse blocks 1, 3, 5, … . Output in groups of five.

Decryption runs the layers in reverse. The decrypted text still contains the Playfair filler letters.

## Repository structure

```
├── cipher.py                 Encryption, decryption, step-by-step trace
├── attacks.py                Red Team toolkit: IoC, periodic IoC, Mirror hypotheses, dictionary known-plaintext attack
├── main.py                   Demo: encrypt, decrypt, then break the cipher from the public pairs
├── blue_team_challenge.py    Builds the 10 pairs (7 correct, 3 wrong), answer key, Red Team sheet, self-attack
├── experiments.py            Experiments for the report (writes results/results.json, ~2 min)
├── make_charts.py            Report figures from results.json
├── tests/test_cipher.py      Unit tests (15)
├── data/                     Public-domain English corpus (Project Gutenberg)
├── results/                  Experiment output and figures
├── challenge/                Challenge Sheet for the Red Team (pairs only)
├── docs/                     Blue Team report (Word)
└── answer_key/               Answer key - publish only after the challenge has ended
```

## Quick start

```bash
pip install -r requirements.txt

python main.py                                  # demo + attack
python cipher.py enc "attack at dawn"           # uses the demo keys MERIDIAN / CASCADE
python cipher.py dec "<ciphertext>"

python -m unittest discover tests               # run the tests
python blue_team_challenge.py                   # rebuild the challenge and attack it
python experiments.py && python make_charts.py  # reproduce the results
```

## Attacks implemented

| Attack | Needs | Idea |
|---|---|---|
| Index of coincidence | ciphertext | Shows the ciphertext is flat (≈0.040) so frequency analysis fails |
| Periodic IoC | long ciphertext | A plain key period shows as peaks; the cascade removes them |
| Mirror-5 hypothesis scan | public pairs + word list | Tries 19 block-reversal hypotheses; the right one gives the highest agreement |
| Dictionary known-plaintext | ≥ 3 correct pairs + word list | For the right Playfair keyword the shift `pos(S2) − pos(L1)` is the same in every correct pair; this recovers the keyword, the key and flags the wrong pairs |

On the challenge pairs the attack recovers `MERIDIAN` and `CASCADE` and flags pairs 3, 6 and 8 in about 13 seconds. It fails when the Playfair keyword is not a dictionary word (see the report, Section 6), which is the recommended hardening.

## License

MIT, see [LICENSE](LICENSE).
