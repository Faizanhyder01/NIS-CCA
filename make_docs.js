// Builds docs/Cascade-Lattice_Blue_Team_Report.docx and challenge/Cascade-Lattice_Challenge_Sheet.docx
const fs = require("fs");
const path = require("path");
const D = require("docx");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, Header, Footer, AlignmentType,
  LevelFormat, HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, PageBreak } = D;

const R = JSON.parse(fs.readFileSync("results/results.json"));
const PAIRS = JSON.parse(fs.readFileSync("answer_key/challenge_pairs.json"));
const FONT = "Arial", ACCENT = "0071E3", GREY = "F5F5F7", LINE = "D2D2D7";
const W = 9638; // content width, A4 with 2 cm margins

const t = (text, o = {}) => new TextRun({ text, font: FONT, size: 21, ...o });
const mono = (text, o = {}) => new TextRun({ text, font: "Courier New", size: 19, ...o });
const P = (runs, o = {}) => new Paragraph({ spacing: { after: 120, line: 300 }, ...o, children: Array.isArray(runs) ? runs : [t(runs)] });
const H1 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: s, font: FONT })] });
const H2 = (s) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: s, font: FONT })] });
const bullet = (runs) => new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 80, line: 290 }, children: Array.isArray(runs) ? runs : [t(runs)] });
const num = (runs, ref = "n1") => new Paragraph({ numbering: { reference: ref, level: 0 }, spacing: { after: 80, line: 290 }, children: Array.isArray(runs) ? runs : [t(runs)] });
const caption = (s) => new Paragraph({ spacing: { before: 60, after: 200 }, alignment: AlignmentType.CENTER, children: [t(s, { italics: true, size: 18, color: "6E6E73" })] });
const note = (runs) => new Paragraph({ spacing: { before: 120, after: 200, line: 290 }, shading: { type: ShadingType.CLEAR, fill: "EAF3FD" }, border: { left: { style: BorderStyle.SINGLE, size: 24, color: ACCENT, space: 8 } }, indent: { left: 200 }, children: Array.isArray(runs) ? runs : [t(runs)] });

function pngSize(file) { const b = fs.readFileSync(file); return [b.readUInt32BE(16), b.readUInt32BE(20)]; }
function img(file, widthPx = 560) {
  const [w, h] = pngSize(file);
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120 }, children: [new ImageRun({ type: "png", data: fs.readFileSync(file), transformation: { width: widthPx, height: Math.round(widthPx * h / w) }, altText: { title: path.basename(file), description: path.basename(file), name: path.basename(file) } })] });
}

const border = { style: BorderStyle.SINGLE, size: 4, color: LINE };
const borders = { top: border, bottom: border, left: border, right: border };
function table(widths, header, rows, o = {}) {
  const mk = (cells, head) => new TableRow({ tableHeader: head, cantSplit: true, children: cells.map((c, i) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA }, borders, margins: { top: 70, bottom: 70, left: 110, right: 110 },
    shading: head ? { type: ShadingType.CLEAR, fill: ACCENT } : (o.zebra && rows.indexOf(cells) % 2 ? { type: ShadingType.CLEAR, fill: "FAFAFC" } : undefined),
    children: [new Paragraph({ alignment: o.center && o.center.includes(i) ? AlignmentType.CENTER : AlignmentType.LEFT, children: [
      (o.mono && o.mono.includes(i) && !head) ? mono(String(c)) : t(String(c), head ? { bold: true, color: "FFFFFF", size: 19 } : { size: 19 })] })] })) });
  return new Table({ width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
    rows: [mk(header, true), ...rows.map((r) => mk(r, false))] });
}
const gap = () => new Paragraph({ spacing: { after: 160 }, children: [] });

const styles = {
  default: { document: { run: { font: FONT, size: 21 } } },
  paragraphStyles: [
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 32, bold: true, font: FONT, color: "1D1D1F" }, paragraph: { spacing: { before: 360, after: 160 }, keepNext: true, outlineLevel: 0 } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 25, bold: true, font: FONT, color: ACCENT }, paragraph: { spacing: { before: 240, after: 100 }, keepNext: true, outlineLevel: 1 } },
  ],
};
const numbering = { config: [
  { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] },
  ...["n1", "n2", "n3", "n4"].map((r) => ({ reference: r, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 340 } } } }] })),
] };
const page = { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } };
const footer = (label) => new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [t(label + "  ·  Page ", { size: 16, color: "86868B" }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: "86868B" })] })] });

const members = [["Syed Muneeb Ali Shah", "CR-23012"], ["Muneeb Ahmed", "CR-23021"], ["S.M. Faizan Hyder", "CR-23026"], ["Kabeer Ahmed", "CR-23034"]];
const fig = (n) => path.join("results", n);
const CA = R.challenge_attack;

/* ======================== BLUE TEAM REPORT ======================== */
const body = [];
const add = (...x) => body.push(...x);

add(new Paragraph({ spacing: { before: 600, after: 80 }, children: [t("NED University of Engineering & Technology", { size: 22, color: "6E6E73" })] }),
  new Paragraph({ spacing: { after: 600 }, children: [t("Department of Cyber Security · Final Year · Batch 2023", { size: 22, color: "6E6E73" })] }),
  new Paragraph({ spacing: { after: 60 }, children: [t("CT-486 Network and Information Security", { size: 24, bold: true })] }),
  new Paragraph({ spacing: { after: 400 }, children: [t("Complex Computing Activity (CCA) · Classical Cipher Challenge", { size: 22 })] }),
  new Paragraph({ spacing: { after: 80 }, children: [t("BLUE TEAM REPORT", { size: 24, bold: true, color: ACCENT })] }),
  new Paragraph({ spacing: { after: 100 }, children: [t("Cascade-Lattice Cipher", { size: 64, bold: true })] }),
  new Paragraph({ spacing: { after: 500 }, children: [t("A three-layer classical cipher (Playfair → Cascade Vigenère → Mirror-5) with team-defined rules", { size: 26, color: "6E6E73" })] }),
  table([6200, 3438], ["Group member", "Roll No."], members), gap(),
  note([t("Handling note. ", { bold: true }), t("This report contains the secret keys, the full algorithm and the identity of the incorrect pairs. It is the Blue Team’s submission to the course teacher. Do not give it to the Red Team until the challenge is finished. The Red Team receives only the separate Challenge Sheet.")]),
  new Paragraph({ children: [new PageBreak()] }));

// 1
add(H1("1. Overview and Deliverables Checklist"),
  P("This report is the Blue Team submission of our group for the Classical Cipher Challenge (CT-486, Complex Computing Activity). As the Blue Team we designed a new cipher, fixed its keys and rules, prepared ten plaintext–ciphertext pairs (seven correct and three intentionally incorrect) and wrote the final explanation of the cipher. We also wrote the attack we expect from a Red Team and ran it on our own dataset, so that every claim about difficulty in this report is backed by a measurement."),
  P("Table 1 maps every Blue Team deliverable in the brief to the section that satisfies it."),
  table([700, 4000, 4938], ["No.", "Deliverable required by the brief", "Where it is met"], [
    ["1", "Unique cipher name and description", "Section 2: name, techniques, plain-language description, design rationale"],
    ["2", "Complete encryption technique and sequence", "Section 3: encryption and decryption sequence, formulas, worked example"],
    ["3", "Key, alphabet mapping and special rules", "Section 4: keyed square, secret keys, rules R1–R8, key space"],
    ["4", "Ten pairs: 7 correct, 3 intentionally incorrect", "Section 5: the ten pairs exactly as issued (unmarked); Red Team copy in the Challenge Sheet"],
    ["5", "Final explanation after the challenge", "Section 7: reveal of keys, algorithm and the three incorrect pairs"],
    ["–", "Evidence for the rubric (CCA-1, CCA-3, CCA-5)", "Section 6 (analysis and solvability) and Section 8 (rubric mapping)"],
  ], { center: [0] }), gap(),
  H2("Rules of the challenge that we followed"),
  bullet("The cipher was fixed before the dataset was issued and is not modified afterwards. All pairs come from one deterministic script (blue_team_challenge.py)."),
  bullet("The keys, the complete algorithm and the identity of the incorrect pairs are not revealed to the Red Team during the challenge."),
  bullet("The cipher combines three classical or classical-style techniques (Playfair, Vigenère, block transposition), more than the two the brief requires, and adds our own rules."));

// 2
add(H1("2. Deliverable 1 – Cipher Name and Description"),
  H2("2.1 Name"),
  P([t("Cascade-Lattice Cipher", { bold: true }), t(" (short name CLC-25). “Lattice” refers to the 5×5 keyed square that is shared by two layers. “Cascade” refers to the shift that grows after every pass of the keyword. “25” is the alphabet size, because J is merged into I.")]),
  H2("2.2 Techniques combined"),
  table([950, 2400, 6288], ["Layer", "Technique", "What it contributes"], [
    ["1", "Playfair cipher (digraph substitution)", "Works on letter pairs, so single-letter frequencies are flattened. Gives the filler-letter rule."],
    ["2", "Vigenère on the keyed alphabet, with a growing (cascade) shift", "Position-dependent substitution. The growing shift removes the repeating key period that Kasiski and period-IoC attacks need."],
    ["3", "Mirror-5 (team-designed block transposition)", "Moves letters by up to four places inside blocks of five, so position-by-position comparisons across messages no longer line up."],
  ], { center: [0] }), gap(),
  H2("2.3 Description"),
  P("The Cascade-Lattice Cipher is a three-layer product cipher over a 25-letter alphabet. First the message is cleaned and encrypted with Playfair on a square built from a secret keyword. Then every letter is shifted along the same keyed alphabet by an amount taken from a second secret keyword. The shift grows by one after every full pass of that keyword, so it never repeats. Finally the text is cut into blocks of five letters and every odd-numbered block is reversed. The result is printed in groups of five. Decryption applies the three layers in reverse order."),
  P("The design follows Shannon’s idea of combining confusion and diffusion (Shannon, 1949). The Vigenère layer supplies confusion that depends on position. The Playfair layer supplies diffusion across letter pairs. The transposition layer breaks the alignment between messages. Figure 1 shows the data flow."),
  img(fig("fig0_dataflow.png"), 600), caption("Figure 1. Data flow of the Cascade-Lattice Cipher (encryption left to right)."),
  H2("2.4 Why this design is challenging for the Red Team"),
  bullet([t("Flat letter statistics. ", { bold: true }), t(`The index of coincidence of the ciphertext is ${R.challenge_ioc.toFixed(4)}, close to the random value 0.040 (Section 6.1).`)]),
  bullet([t("No single-technique shortcut. ", { bold: true }), t("A Red Team that assumes only Caesar, only Vigenère or only Playfair gets no consistent result. All three layers must be found and separated.")]),
  bullet([t("No visible key period. ", { bold: true }), t("A plain 7-letter Vigenère shows peaks at periods 7, 14 and 21 in a periodic IoC test. Ours shows none (Figure 4).")]),
  bullet([t("Order matters. ", { bold: true }), t("Playfair, then Vigenère, then Mirror-5. Any other order gives a different cipher.")]),
  bullet([t("Trap pairs. ", { bold: true }), t("Three of the ten pairs are wrong in three different ways, and all three still have the right length and valid letters.")]));

// 3
const tr = (() => { const { execSync } = require("child_process"); return JSON.parse(execSync(`python3 -c "import json;from cipher import encrypt_trace;print(json.dumps(encrypt_trace('Attack at dawn from the north gate')))"`).toString()); })();
const g5 = (s) => s.replace(/(.{5})(?=.)/g, "$1 ");
add(H1("3. Deliverable 2 – Complete Encryption Technique and Sequence"),
  H2("3.1 Encryption sequence"),
  P("The order of operations is fixed."),
  num([t("Normalise (R1). ", { bold: true }), t("Convert to upper case, delete everything that is not A–Z, merge J into I.")]),
  num([t("Playfair (R3). ", { bold: true }), t("Split into digraphs, inserting the filler X between a double letter (Q if the letter is X) and padding an odd tail. Encrypt each digraph on the keyed 5×5 square: same row, take the letter to the right; same column, take the letter below; otherwise swap the columns.")]),
  num([t("Cascade Vigenère (R4). ", { bold: true }), t("Number the letters by their position 0–24 in the keyed square. Add the shift s")]),
  );
// fix item 3 text fully (replace last pushed numbered paragraph)
body.pop();
add(num([t("Cascade Vigenère (R4). ", { bold: true }), t("Number the letters by their position 0–24 in the keyed square. For position i add the shift "), mono("s_i = (k[i mod m] + floor(i / m)) mod 25"), t(", where k is the keyword written as square positions and m = 7. Then convert back to letters.")]),
  num([t("Mirror-5 (R5). ", { bold: true }), t("Cut into blocks of five letters. Reverse blocks 1, 3, 5, and so on. A short last block is reversed too if it is odd-numbered.")]),
  num([t("Output (R7). ", { bold: true }), t("Write the ciphertext in groups of five letters.")]),
  H2("3.2 Decryption sequence"),
  num("Remove spaces. Undo Mirror-5 by applying it again, because reversing a block twice restores it.", "n2"),
  num("Undo the cascade: subtract the same shifts s_i along the keyed alphabet.", "n2"),
  num("Undo Playfair: same row, take the letter to the left; same column, take the letter above; otherwise swap the columns.", "n2"),
  num("The result still contains the filler letters X (or Q). The receiver removes them by eye (rule R8).", "n2"),
  H2("3.3 Worked example"),
  P([t("Message: "), t("“Attack at dawn from the north gate”", { italics: true }), t(". Square: "), mono(tr.square), t(".")]),
  table([2400, 7238], ["Step", "Result"], [
    ["Prepared (R1, R3)", g5(tr.prepared)], ["After Playfair", g5(tr.after_playfair)],
    ["Shifts s_i (first 14)", tr.shifts.slice(0, 14).join(" ")], ["After Cascade Vigenère", g5(tr.after_cascade)],
    ["After Mirror-5", g5(tr.after_mirror)], ["Ciphertext", tr.ciphertext]], { mono: [1] }), gap(),
  P([t("Check of the first digraph: "), mono("AT"), t(" is in different rows and columns of the square, so it becomes the letters at the swapped corners, "), mono("CP"), t(". The first shift is the square position of the keyword letter C, then the cascade shift grows by one after letter 7. The first block of five is then reversed by Mirror-5, which is why the ciphertext starts "), mono(tr.ciphertext.slice(0, 5)), t(" while the Cascade output starts "), mono(tr.after_cascade.slice(0, 5)), t(".")]));

// 4
const sq = tr.square; const sqRows = [0, 1, 2, 3, 4].map((r) => [...sq.slice(r * 5, r * 5 + 5)].map((c, i) => `${c} (${r * 5 + i})`));
add(H1("4. Deliverable 3 – Key, Alphabet Mapping and Special Rules"),
  H2("4.1 Alphabet mapping"),
  P("The cipher works on 25 letters. J is merged into I. The alphabet is not A–Z in order: it is the keyed square read row by row. The number in brackets is the position used by the Vigenère layer."),
  table([1927, 1927, 1928, 1928, 1928], ["Col 1", "Col 2", "Col 3", "Col 4", "Col 5"], sqRows, { mono: [0, 1, 2, 3, 4], center: [0, 1, 2, 3, 4] }), gap(),
  H2("4.2 Secret keys of the challenge"),
  table([3200, 2400, 4038], ["Key", "Value", "Notes"], [
    ["Playfair keyword", "MERIDIAN", "Builds the square above; also defines the alphabet mapping"],
    ["Vigenère keyword", "CASCADE", "Written as square positions: C=8, A=5, S=17, C=8, A=5, D=4, E=1"],
    ["Mirror block size", "5", "Blocks 1, 3, 5, … are reversed"],
  ]), gap(),
  P("The Vigenère keyword length 7 and the block size 5 share no common factor, so the key repeat and the block pattern coincide only every 35 letters."),
  H2("4.3 Special rules"),
  table([700, 2600, 6338], ["Rule", "Name", "Definition"], [
    ["R1", "Normalise", "Upper case, A–Z only, J becomes I. Spaces, digits and punctuation are dropped."],
    ["R2", "Keyed alphabet", "The keyword (without repeats) followed by the unused letters in order. Used by Playfair and by the Vigenère layer."],
    ["R3", "Filler letters", "A double letter gets an X between its two copies. If the double letter is X, the filler is Q. An odd last letter is padded in the same way."],
    ["R4", "Cascade shift", "After every full pass of the Vigenère keyword, every shift increases by one."],
    ["R5", "Mirror-5", "Reverse every odd-numbered block of five letters, including a short last block."],
    ["R6", "Restart", "Every message is encrypted on its own. The key position and the shift counter restart at 0."],
    ["R7", "Output format", "Groups of five letters. The length equals the Playfair-prepared length, so it is always even."],
    ["R8", "Filler stays", "Decryption returns the filler letters. They are not removed automatically."],
  ], { center: [0] }), gap(),
  H2("4.4 Key space"),
  P(`Taking every 25-letter square as possible, Playfair alone has 25! squares, about 2^83.7. A 7-letter Vigenère keyword on the square adds 25^7, about 2^32.5. Together the upper bound is about 2^${R.keyspace_bits["Cascade-Lattice (upper bound)"].toFixed(1)} (Figure 5). Section 6 explains why the effective strength is lower when the keywords are dictionary words.`));

// 5
add(H1("5. Deliverable 4 – The Ten Plaintext–Ciphertext Pairs"),
  P("The ten pairs below are exactly as issued to the Red Team in the Challenge Sheet. Nothing marks the incorrect ones."),
  table([600, 3500, 5538], ["No.", "Plaintext", "Ciphertext"], PAIRS.map((p) => [p.n, p.plaintext, p.ciphertext]), { mono: [2], center: [0] }), gap(),
  P("The plaintexts are 28 to 35 letters of ordinary English about networking and security. Several contain doubled letters (firewall, messages, process, will), so the filler rule appears in the data and the Red Team must discover it."));

// 6
const A = R.ioc_stages, pn = R.pairs_needed, nd = R.non_dictionary_keys;
add(H1("6. Challenge Design and Solvability Analysis"),
  P("We attacked our own cipher the way a Red Team would. All numbers come from experiments.py and can be reproduced."),
  H2("6.1 Letter statistics"),
  P(`The index of coincidence (IoC) of English is ${A.plaintext.toFixed(3)} in our corpus. After Playfair it is ${A.after_playfair.toFixed(3)}. After the cascade layer it is ${A.after_cascade.toFixed(3)}, equal to random text. Mirror-5 only moves letters, so it does not change the IoC. The seven correct challenge ciphertexts together give ${R.challenge_ioc.toFixed(4)}. Frequency analysis therefore gives the Red Team no foothold.`),
  img(fig("fig1_ioc_stages.png"), 470), caption("Figure 2. Index of coincidence after each layer."),
  img(fig("fig6_letter_freq.png"), 520), caption("Figure 3. Letter frequencies: English against the challenge ciphertext."),
  H2("6.2 Key period"),
  P("Figure 4 repeats the standard periodic IoC test on a 20,000-letter message. A plain Vigenère with a 7-letter key peaks at 7, 14 and 21. With Playfair in front and a fixed shift the peak is weaker but still visible. With the cascade shift and Mirror-5 the curve is flat at the random level. This is the reason for rule R4."),
  img(fig("fig2_periodic_ioc.png"), 480), caption("Figure 4. Periodic IoC for three variants."),
  H2("6.3 Key space"),
  img(fig("fig3_keyspace.png"), 480), caption("Figure 5. Key space of classical ciphers and of the Cascade-Lattice Cipher (upper bounds)."),
  H2("6.4 Solvability: the Red Team attack"),
  P("A challenge should be hard but fair. To show that ours is solvable we wrote a Red Team attack (attacks.py) that uses only the ten public pairs and a word list of 234,261 English words. It never reads the secret keys. It works in five steps."),
  num("Check that every ciphertext has the length of the Playfair-prepared plaintext. It does, which reveals that filler letters were inserted.", "n3"),
  num("Try 19 hypotheses for the transposition layer (block sizes 3 to 8, reverse odd, even or all blocks, or none) and undo each one.", "n3"),
  num("For every candidate Playfair keyword, build its square and compute, at each position, the value pos(S2) − pos(L1) mod 25. For the right keyword this value is the same in every correct pair, because the shift depends only on the position. Count how many pairs agree.", "n3"),
  num("The keyword with the highest agreement is the Playfair keyword. The agreed values are the cascade shifts. The period m is the smallest value with s[i+m] = s[i] + 1, and the key letters follow.", "n3"),
  num("Pairs that disagree with the agreed values are the incorrect pairs.", "n3"),
  img(fig("fig4_mirror_scan.png"), 470), caption("Figure 6. Step 2: the right transposition hypothesis has the highest score."),
  table([3200, 6438], ["Result of the attack", "Value"], [
    ["Transposition found", `block size ${CA.mirror_block}, pattern “${CA.mirror_pattern}” (reverse odd blocks)`],
    ["Playfair keyword found", CA.playfair_keyword], ["Vigenère key found", `${CA.vigenere_key} (period ${CA.period})`],
    ["Best three keywords (score)", CA.scores.map((s) => `${s[0]} ${s[1]}`).join(", ")],
    ["Mismatches per pair", CA.mismatches.join(", ")], ["Incorrect pairs flagged", CA.flagged_pairs.join(", ")],
    ["Run time", `${CA.seconds} seconds on one CPU core`]]), gap(),
  P("The attack recovers both keys and the three incorrect pairs. The mismatch counts also show the type of fault: one mismatch for the single altered letter (pair 3), many for the skipped transposition step (pair 6), and exactly the positions that use the fifth key letter for the near-miss key (pair 8)."),
  H2("6.5 How many correct pairs does the Red Team need?"),
  img(fig("fig5_pairs_needed.png"), 440), caption("Figure 7. Success of the attack for different numbers of correct pairs."),
  P(`With two correct pairs the attack fails, because it needs at least three pairs to agree before it trusts a position. With three to seven pairs it succeeded in every one of our ${pn["3"].trials} trials per setting. The challenge gives seven correct pairs, so a Red Team has a comfortable margin even after it removes the three wrong ones.`),
  H2("6.6 Limitations and honest weak points"),
  bullet([t("Dictionary keywords. ", { bold: true }), t("The Playfair keyword MERIDIAN is an English word, and that is what the attack exploits. We chose a dictionary word on purpose so that the challenge is solvable and the Red Team can justify its answer with evidence.")]),
  bullet([t("The fix is easy. ", { bold: true }), t(`When we replaced the keyword with letter strings that are not words (${Object.keys(nd).join(" and ")}), the same attack no longer recovered the keyword (it returned ${Object.values(nd).map((v) => v.found).join(" and ")}). A Red Team would then need a much larger search, for example hill climbing on the square.`)]),
  bullet([t("The attack assumes the structure. ", { bold: true }), t("It assumes the layer order Playfair, Vigenère, transposition. A real Red Team has to infer this, using the clues in Section 6.7.")]),
  bullet([t("Educational only. ", { bold: true }), t("Classical ciphers are not secure against modern cryptanalysis.")]),
  H2("6.7 Clues a Red Team can use"),
  bullet("The ciphertext length is always even and is longer than the plaintext letter count when the plaintext has a doubled letter. This points to Playfair-style filler."),
  bullet("The IoC is about 0.040, so the cipher is not a plain substitution or a plain Vigenère."),
  bullet("The periodic IoC test shows no key period, so a simple Vigenère is ruled out."),
  bullet("The three incorrect pairs disagree with the other seven under the right hypothesis, which is how they are identified."));

// 7
const wr = PAIRS.filter((p) => !p.valid);
add(H1("7. Deliverable 5 – Final Explanation of the Actual Cipher (Post-Challenge Reveal)"),
  P("This section is for the course teacher and for the debrief after the challenge."),
  H2("7.1 The actual cipher"),
  bullet("Layer 1: Playfair with the keyword MERIDIAN, filler X (Q for XX), J merged into I."),
  bullet("Layer 2: Vigenère on the keyed alphabet with keyword CASCADE, shift s_i = (k[i mod 7] + floor(i/7)) mod 25."),
  bullet("Layer 3: Mirror-5, reversing every odd-numbered block of five letters."),
  bullet("Output in groups of five letters."),
  H2("7.2 The three incorrect pairs"),
  table([600, 1900, 3800, 3338], ["No.", "Fault", "How it was made", "How it can be detected"], [
    [wr[0].n, "Corrupted letter", "The correct ciphertext with letter 8 shifted six places along the alphabet.", `Disagrees with the agreed shifts at exactly one position (${CA.mismatches[wr[0].n - 1]} mismatch).`],
    [wr[1].n, "Wrong sequence", "Playfair and cascade done correctly, Mirror-5 skipped.", `Disagrees at many positions (${CA.mismatches[wr[1].n - 1]} mismatches) because blocks 1, 3 and 5 are not reversed.`],
    [wr[2].n, "Near-miss key", "Encrypted with CASCODE instead of CASCADE.", `Disagrees only at positions 5, 12, 19, 26, 33, where the fifth key letter is used (${CA.mismatches[wr[2].n - 1]} mismatches).`],
  ], { center: [0] }), gap(),
  P("All three have the correct length and valid letters, so a simple length or alphabet check cannot expose them. The positions 3, 6 and 8 are irregular on purpose."),
  H2("7.3 All ten pairs with the correct ciphertext"),
  table([600, 1700, 7338], ["No.", "Verdict", "Correct ciphertext"], PAIRS.map((p) => [p.n, p.valid ? "Correct" : "Incorrect", p.true_ciphertext]), { mono: [2], center: [0] }), gap());

// 8
add(H1("8. Mapping to the Assessment Rubric"),
  table([2800, 3100, 3738], ["Criterion", "How we address it", "Where"], [
    ["Use of resources (CCA-1)", "Team of four, Python implementation, unit tests, NumPy vectorised attack, public-domain English corpus, a 234,261-word list, classical cryptanalysis literature.", "Sections 6, 9; repository"],
    ["Innovation and creativity (CCA-3)", "Cascade shift, one keyed alphabet shared by two layers, Mirror-5 transposition, XX→Q rule, wrong pairs with three distinct faults, a Red Team attack built by the Blue Team.", "Sections 2, 4, 6.4"],
    ["Application to an unfamiliar task (CCA-5)", "A new three-layer design with no textbook solution, chosen by what each layer defeats and checked by experiment.", "Sections 2, 6"],
    ["Cipher design and cryptanalysis (CCA-3, CCA-5)", "Fully specified algorithm, 15 unit tests, solver that recovers the keys and the three wrong pairs from public data only.", "Sections 3, 4, 6.4, 7"],
    ["Evidence and documentation (CCA-1, CCA-5)", "Deliverables checklist, figures from reproducible experiments, stated limitations, separate Challenge Sheet and answer key.", "Sections 1, 6, 7"],
  ]), gap());

// 9
add(H1("9. Conclusion"),
  P("The Cascade-Lattice Cipher combines Playfair, a growing-shift Vigenère on a shared keyed alphabet, and a block transposition. It removes letter-frequency and key-period evidence (IoC about 0.040, flat periodic IoC), and it ships with ten pairs, three of which are wrong in three different ways. We showed that the challenge is fair: a Red Team that finds the structure can recover both keys and the incorrect pairs in about thirteen seconds with a word list. We also showed the limit of the design: the keywords are dictionary words, and replacing them removes that shortcut."),
  P("Everything in this report can be reproduced with the repository: python blue_team_challenge.py rebuilds the dataset and the attack, python experiments.py and python make_charts.py rebuild the results and figures, and python -m unittest discover tests runs the tests."),
  H2("References"),
  bullet("Shannon, C. E. (1949). Communication Theory of Secrecy Systems. Bell System Technical Journal, 28(4), 656–715."),
  bullet("Friedman, W. F. (1922). The Index of Coincidence and Its Applications in Cryptography. Riverbank Laboratories."),
  bullet("Kasiski, F. W. (1863). Die Geheimschriften und die Dechiffrir-Kunst. Berlin: E. S. Mittler und Sohn."),
  bullet("Stallings, W. Cryptography and Network Security: Principles and Practice. Pearson."),
  bullet("Course material, CT-486 Network and Information Security, NED University of Engineering & Technology."));

const report = new Document({ styles, numbering, creator: "Blue Team", title: "Cascade-Lattice Cipher - Blue Team Report",
  sections: [{ properties: { page }, footers: { default: footer("Cascade-Lattice Cipher · Blue Team Report") }, children: body }] });

/* ======================== CHALLENGE SHEET ======================== */
const cs = [];
cs.push(new Paragraph({ spacing: { after: 60 }, children: [t("CT-486 Network and Information Security · Classical Cipher Challenge", { color: "6E6E73", size: 20 })] }),
  new Paragraph({ spacing: { after: 160 }, children: [t("Challenge Sheet", { size: 52, bold: true })] }),
  P([t("Issued by the Blue Team: ", { bold: true }), t(members.map((m) => `${m[0]} (${m[1]})`).join(", "))]),
  H2("What this is"),
  P("Below are ten plaintext–ciphertext pairs made with a new cipher. Seven pairs are correct. Three are intentionally incorrect. The key, the algorithm and the identity of the incorrect pairs are not revealed."),
  table([600, 3500, 5538], ["No.", "Plaintext", "Ciphertext"], PAIRS.map((p) => [p.n, p.plaintext, p.ciphertext]), { mono: [2], center: [0] }), gap(),
  H2("Your task as the Red Team"),
  num("Identify the classical cipher techniques used.", "n4"),
  num("Identify the three incorrect plaintext–ciphertext pairs.", "n4"),
  num("Determine or recover the key.", "n4"),
  num("Determine the encryption sequence.", "n4"),
  num("Explain the discovered encryption algorithm.", "n4"),
  num("Provide evidence supporting your solution.", "n4"),
  H2("Rules"),
  bullet("The Blue Team cannot change the cipher after issuing this sheet."),
  bullet("The Blue Team will not reveal the key, the algorithm or the incorrect pairs during the challenge."),
  bullet("The Red Team cannot ask for the key or the incorrect pairs."),
  bullet("Ciphertext is shown in groups of five letters. Spaces carry no meaning."));
const sheet = new Document({ styles, numbering, creator: "Blue Team", title: "Cascade-Lattice Cipher - Challenge Sheet",
  sections: [{ properties: { page }, footers: { default: footer("Challenge Sheet") }, children: cs }] });

(async () => {
  fs.writeFileSync("docs/Cascade-Lattice_Blue_Team_Report.docx", await Packer.toBuffer(report));
  fs.writeFileSync("challenge/Cascade-Lattice_Challenge_Sheet.docx", await Packer.toBuffer(sheet));
  console.log("docs written");
})();
