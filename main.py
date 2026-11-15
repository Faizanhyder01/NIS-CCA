"""Demo: encrypt, decrypt, show every layer, then break the cipher from the public pairs.   python main.py"""
from cipher import encrypt, decrypt, encrypt_trace
from attacks import red_team_attack
from blue_team_challenge import build, load_words

msg = "Attack at dawn from the north gate"
t = encrypt_trace(msg)
print("Keyed square :", t["square"])
print("Plaintext    :", msg)
print("Prepared     :", t["prepared"], "  (filler letters added)")
print("Playfair     :", t["after_playfair"])
print("Cascade      :", t["after_cascade"])
print("Mirror-5     :", t["after_mirror"])
print("Ciphertext   :", t["ciphertext"])
print("Decrypted    :", decrypt(t["ciphertext"]))
print("\nNow the Red Team attack on the 10 public challenge pairs:")
pairs = [{"plaintext": p["plaintext"], "ciphertext": p["ciphertext"]} for p in build()]
red_team_attack(pairs, load_words())
