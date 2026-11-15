"""Builds the report figures from results/results.json.   python make_charts.py"""
import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "results", "results.json")))
OUT = os.path.join(HERE, "results")
BLUE, GREY, INK, RED, GREEN, ORANGE = "#0071e3", "#d2d2d7", "#1d1d1f", "#d70015", "#248a3d", "#b25000"
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#86868b", "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
                     "figure.dpi": 150, "savefig.bbox": "tight", "savefig.facecolor": "white"})


def save(name):
    plt.savefig(os.path.join(OUT, name)); plt.close()


# fig0: data flow
fig, ax = plt.subplots(figsize=(9, 2.3)); ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(0, 24)
boxes = [("Plaintext", "letters only, J to I"), ("1  Playfair", "keyword MERIDIAN\nfiller X / Q"),
         ("2  Cascade", "keyword CASCADE\nshift grows each pass"), ("3  Mirror-5", "reverse odd blocks\nof five letters"),
         ("Ciphertext", "groups of five")]
for i, (t, s) in enumerate(boxes):
    x = 1 + i * 20
    ax.add_patch(FancyBboxPatch((x, 4), 16, 16, boxstyle="round,pad=0.4,rounding_size=2",
                                fc=BLUE if i in (1, 2, 3) else "#f5f5f7", ec="none"))
    col = "white" if i in (1, 2, 3) else INK
    ax.text(x + 8, 14.5, t, ha="center", va="center", fontsize=9, fontweight="bold", color=col)
    ax.text(x + 8, 8.5, s, ha="center", va="center", fontsize=7, color=col)
    if i < 4:
        ax.add_patch(FancyArrowPatch((x + 16.6, 12), (x + 20.4, 12), arrowstyle="-|>", mutation_scale=10, color="#86868b"))
save("fig0_dataflow.png")

# fig1: IoC after each layer
s = R["ioc_stages"]
labels = ["English\nplaintext", "After\nPlayfair", "After\nCascade", "After\nMirror-5", "Random\n25 letters"]
vals = [s["plaintext"], s["after_playfair"], s["after_cascade"], s["after_mirror"], s["random_25"]]
plt.figure(figsize=(7, 3.6)); b = plt.bar(labels, vals, color=[GREY, BLUE, BLUE, BLUE, "#86868b"], width=0.6)
for r, v in zip(b, vals): plt.text(r.get_x() + r.get_width() / 2, v + 0.001, f"{v:.3f}", ha="center", fontsize=9)
plt.ylabel("Index of coincidence"); plt.title("Each layer flattens the letter statistics", loc="left", fontsize=11, fontweight="bold")
save("fig1_ioc_stages.png")

# fig2: periodic IoC
p = R["periodic_ioc"]; xs = list(range(1, 22))
plt.figure(figsize=(7.5, 3.8))
plt.plot(xs, p["plain_vigenere"], color=RED, marker="o", ms=4, label="Plain Vigenere (key length 7)")
plt.plot(xs, p["playfair_static_vigenere"], color=ORANGE, marker="o", ms=4, label="Playfair + fixed-shift Vigenere")
plt.plot(xs, p["cascade_lattice"], color=BLUE, marker="o", ms=4, lw=2.4, label="Cascade-Lattice (full)")
plt.axhline(0.04, color="#86868b", ls="--", lw=1, label="Random 25 letters (0.040)")
plt.xticks(xs[::2]); plt.xlabel("Assumed key period"); plt.ylabel("Mean column IoC")
plt.title("A plain key period shows as peaks; the cascade hides it", loc="left", fontsize=11, fontweight="bold")
plt.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=1); save("fig2_periodic_ioc.png")

# fig3: key space
k = R["keyspace_bits"]; names = list(k); vals = list(k.values())
plt.figure(figsize=(7.5, 3.6)); b = plt.barh(names[::-1], vals[::-1], color=[BLUE] + [GREY] * 4, height=0.6)
for r, v in zip(b, vals[::-1]): plt.text(v + 1, r.get_y() + r.get_height() / 2, f"{v:.1f} bits", va="center", fontsize=9)
plt.xlim(0, 135); plt.xlabel("Key space (bits, upper bound)")
plt.title("Raw key space is large, but dictionary keys shrink it", loc="left", fontsize=11, fontweight="bold")
save("fig3_keyspace.png")

# fig4: Mirror hypotheses scan
h = R["challenge_attack"]["hypothesis_scores"][:8]
lab = [f"block {sz}, {pt}" for _, sz, pt in h]; sc = [x[0] for x in h]
plt.figure(figsize=(7.5, 3.6)); b = plt.barh(lab[::-1], sc[::-1], color=[GREY] * (len(h) - 1) + [BLUE], height=0.6)
for r, v in zip(b, sc[::-1]): plt.text(v + 4, r.get_y() + r.get_height() / 2, str(v), va="center", fontsize=9)
plt.xlabel("Best agreement score over 234,261 keywords")
plt.title("Red Team step 1: the Mirror-5 layer stands out", loc="left", fontsize=11, fontweight="bold")
save("fig4_mirror_scan.png")

# fig5: pairs needed
pn = R["pairs_needed"]; ks = list(pn); rate = [100 * pn[x]["success"] / pn[x]["trials"] for x in ks]
plt.figure(figsize=(7, 3.5)); b = plt.bar([f"{x} pairs" for x in ks], rate, color=[RED if r == 0 else BLUE for r in rate], width=0.55)
for r, v in zip(b, rate): plt.text(r.get_x() + r.get_width() / 2, v + 2, f"{v:.0f}%", ha="center", fontsize=9)
plt.ylim(0, 115); plt.ylabel("Attack success (6 trials each)")
plt.title("The dictionary attack needs at least three correct pairs", loc="left", fontsize=11, fontweight="bold")
save("fig5_pairs_needed.png")

# fig6: letter frequency
alpha = "ABCDEFGHIKLMNOPQRSTUVWXYZ"; e = R["english_freq"]; c = R["challenge_ct_freq"]
plt.figure(figsize=(8, 3.5)); xs = range(25)
plt.bar([x - 0.2 for x in xs], [100 * e[a] for a in alpha], width=0.4, color=GREY, label="English")
plt.bar([x + 0.2 for x in xs], [100 * c[a] for a in alpha], width=0.4, color=BLUE, label="Challenge ciphertext (7 correct pairs)")
plt.xticks(xs, list(alpha)); plt.ylabel("Frequency (%)"); plt.legend(frameon=False, fontsize=8)
plt.title("No English letter peaks survive", loc="left", fontsize=11, fontweight="bold")
save("fig6_letter_freq.png")
print("figures written to results/")
