import os
import random
import string
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import cipher as c
import blue_team_challenge as bt
import attacks as at

SMALL_WORDS = ["meridian", "lattice", "cascade", "network", "monarchy", "playfair", "security", "cipher",
               "firewall", "karachi", "kingdom", "garden", "student", "problem", "justice"]


class CipherTests(unittest.TestCase):
    def test_keyed_alphabet(self):
        self.assertEqual(c.keyed_alphabet("MERIDIAN"), "MERIDANBCFGHKLOPQSTUVWXYZ")
        self.assertEqual(len(c.keyed_alphabet("JAZZ")), 25)       # J merged into I, no repeats

    def test_normalise_merges_j(self):
        self.assertEqual(c.normalise("Jack, 7 jumps!"), "IACKIUMPS")

    def test_filler_rules(self):
        self.assertEqual(c.pf_prepare("BALLOON"), "BALXLOON")      # LL split with X; ON pairs cleanly
        self.assertEqual(c.pf_prepare("XX"), "XQXQ")                # doubled X uses Q
        self.assertEqual(c.pf_prepare("AX"), "AX")

    def test_known_vector(self):
        self.assertEqual(c.encrypt("HELLO WORLD"), "UNDHZ OMVFA AH")
        t = c.encrypt_trace("HELLO WORLD")
        self.assertEqual(t["after_playfair"], "QNKYOGZHIKRZ")
        self.assertEqual(t["after_cascade"], "ZHDNUOMVFAHA")

    def test_mirror_is_involution(self):
        for n in range(0, 40):
            s = "".join(random.choice(string.ascii_uppercase) for _ in range(n))
            self.assertEqual(c.mirror(c.mirror(s)), s)

    def test_cascade_shift_grows(self):
        sq = c.keyed_alphabet("MERIDIAN")
        # a text of all-first-letter 'M' (index 0): output index equals the shift itself
        out = c.cascade("M" * 16, sq, "CASCADE", +1)
        k = [sq.index(x) for x in "CASCADE"]
        self.assertEqual([sq.index(x) for x in out], [(k[i % 7] + i // 7) % 25 for i in range(16)])

    def test_round_trip_random(self):
        random.seed(1)
        for _ in range(500):
            s = "".join(random.choice(string.ascii_letters + " ,.") for _ in range(random.randint(1, 80)))
            if c.normalise(s):
                self.assertEqual(c.decrypt(c.encrypt(s)), c.pf_prepare(s))

    def test_other_keys_round_trip(self):
        for pk, vk in (("LATTICE", "ZEBRA"), ("QUARTZ", "AAAAAAAA"), ("X", "Y")):
            self.assertEqual(c.decrypt(c.encrypt("Meet me at the gate", pk, vk), pk, vk), c.pf_prepare("Meet me at the gate"))

    def test_ciphertext_format(self):
        ct = c.encrypt("Attack at dawn from the north gate")
        self.assertTrue(all(len(g) == 5 for g in ct.split()[:-1]))
        self.assertTrue(ct.isupper() or " " in ct)
        self.assertNotIn("J", ct)
        self.assertEqual(len(c.normalise(ct)) % 2, 0)               # Playfair output is always even


class ChallengeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = bt.build()

    def test_seven_correct_three_wrong(self):
        self.assertEqual(sum(p["valid"] for p in self.pairs), 7)
        self.assertEqual([p["n"] for p in self.pairs if not p["valid"]], [3, 6, 8])
        bt.full_check(self.pairs)

    def test_wrong_pairs_look_valid(self):
        for p in self.pairs:
            raw = c.normalise(p["ciphertext"])
            self.assertEqual(len(raw), len(c.pf_prepare(p["plaintext"])))   # same length as a correct pair
            self.assertNotIn("J", raw)

    def test_distinct_faults(self):
        self.assertEqual(len({p["fault"] for p in self.pairs if not p["valid"]}), 3)


class AttackTests(unittest.TestCase):
    def test_ioc_basics(self):
        self.assertAlmostEqual(at.ioc("AAAA"), 1.0)
        self.assertAlmostEqual(at.ioc("ABCDEFGHIKLMNOPQRSTUVWXYZ" * 3), 150 / (75 * 74))

    def test_attack_recovers_keys(self):
        pairs = [{"plaintext": p["plaintext"], "ciphertext": p["ciphertext"]} for p in bt.build()]
        res = at.red_team_attack(pairs, SMALL_WORDS, verbose=False)
        self.assertEqual(res["playfair_keyword"], "MERIDIAN")
        self.assertEqual(res["vigenere_key"], "CASCADE")
        self.assertEqual((res["mirror_block"], res["mirror_pattern"]), (5, "odd"))
        self.assertEqual(res["flagged_pairs"], [3, 6, 8])

    def test_attack_needs_the_right_word(self):
        pairs = [{"plaintext": p["plaintext"], "ciphertext": p["ciphertext"]} for p in bt.build()]
        res = at.red_team_attack(pairs, [w for w in SMALL_WORDS if w != "meridian"], verbose=False)
        self.assertNotEqual(res["playfair_keyword"], "MERIDIAN")


if __name__ == "__main__":
    unittest.main()
