"""Draws the portable cluster v0 schematic sheets from the numbers below (README.md explains each one).
    python draw.py   ->  block.svg, power.svg, network.svg, layout.svg"""
from pathlib import Path

HERE = Path(__file__).parent
NODES = 4
NODE_W12 = 165          # W per node at 12 V, peak (estimate)
SWITCH_W, FAN_W, CTRL_W = 20, 3, 3
PSU_W = 1000
LANE, BOARD, FRONT, REAR, HEIGHT = 97, 170, 30, 120, 220   # mm
POWER, DATA, CTRL, AIR, INK, MUTE = "#c2410c", "#1d4ed8", "#15803d", "#64748b", "#111111", "#6b7280"
FONT = "font-family='Helvetica Neue, Helvetica, Arial, sans-serif'"


class Sheet:
    def __init__(self, w, h, title, sub):
        self.w, self.h, self.e = w, h, []
        self.text(30, 42, title, 22, INK, weight=600)
        self.text(30, 66, sub, 13, MUTE)

    def rect(self, x, y, w, h, label="", sub="", stroke=INK, fill="#ffffff", dash=None, size=14):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        self.e.append(f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='4' fill='{fill}' stroke='{stroke}' stroke-width='1.5'{d}/>")
        if label:
            self.text(x + w / 2, y + h / 2 - (6 if sub else -5), label, size, INK, anchor="middle", weight=600)
        if sub:
            self.text(x + w / 2, y + h / 2 + 14, sub, 11.5, MUTE, anchor="middle")

    def line(self, pts, color, width=2.5, dash=None, arrow=False):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        m = f" marker-end='url(#a{color[1:]})'" if arrow else ""
        p = " ".join(f"{x},{y}" for x, y in pts)
        self.e.append(f"<polyline points='{p}' fill='none' stroke='{color}' stroke-width='{width}'{d}{m}/>")

    def text(self, x, y, s, size, color, anchor="start", weight=400):
        s = s.replace("&", "&amp;").replace("<", "&lt;")
        self.e.append(f"<text x='{x}' y='{y}' {FONT} font-size='{size}' fill='{color}' text-anchor='{anchor}' font-weight='{weight}'>{s}</text>")

    def legend(self, items, y):
        x = 30
        for color, dash, label in items:
            self.line([(x, y), (x + 34, y)], color, dash=dash)
            self.text(x + 42, y + 4, label, 12, MUTE); x += 60 + 7 * len(label)

    def save(self, name):
        marks = "".join(f"<marker id='a{c[1:]}' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='7' markerHeight='7' orient='auto'><path d='M0,0 L10,5 L0,10 z' fill='{c}'/></marker>"
                        for c in (POWER, DATA, CTRL, AIR))
        svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {self.w} {self.h}' width='{self.w}' height='{self.h}'>"
               f"<defs>{marks}</defs><rect width='100%' height='100%' fill='#ffffff'/>" + "".join(self.e) + "</svg>\n")
        (HERE / name).write_text(svg)


total12 = NODES * NODE_W12 + SWITCH_W + NODES * FAN_W + CTRL_W
amps = total12 / 12

# --- block.svg: the whole system ---------------------------------------------------------------------------------
s = Sheet(1100, 640, "Portable cluster v0: system block diagram", f"{NODES} Strix Halo Mini-ITX nodes, one mains inlet, one network port, front-to-back air")
s.rect(40, 110, 150, 70, "Mains inlet", "IEC C14, fuse, switch", POWER)
s.rect(250, 110, 170, 70, "12 V supply", f"{PSU_W} W", POWER)
s.rect(480, 100, 210, 90, "Power distribution", f"{NODES} fused branches, monitors", POWER)
s.rect(760, 100, 300, 90, "Controller", "sequencing, fans, power readings", CTRL)
for i in range(NODES):
    x = 60 + i * 255
    s.rect(x, 300, 215, 120, "", "", INK, "#f8fafc")
    s.text(x + 107, 326, f"Node {i + 1}", 14, INK, "middle", 600); s.text(x + 107, 345, "Strix Halo, 128 GB", 11.5, MUTE, "middle")
    s.rect(x + 20, 360, 80, 44, "ATX", "picoPSU", POWER, size=12)
    s.rect(x + 115, 360, 80, 44, "NVMe", "models", INK, size=12)
    s.line([(585, 190), (585, 245), (x + 107, 245), (x + 107, 300)], POWER, arrow=True)
    s.line([(x + 107, 420), (x + 107, 500)], DATA, dash="7,5")
s.rect(390, 500, 320, 60, "Network switch", "5 Gbit, one port to the outside", DATA)
for i in range(NODES):
    s.line([(60 + i * 255 + 107, 500), (550, 500)], DATA, dash="7,5")
s.line([(710, 530), (1060, 530)], DATA, dash="7,5", arrow=True); s.text(905, 520, "local network", 12, DATA, "middle")
s.line([(190, 145), (250, 145)], POWER, arrow=True); s.line([(420, 145), (480, 145)], POWER, arrow=True)
s.line([(690, 145), (760, 145)], CTRL, dash="3,4", arrow=True)
s.legend([(POWER, None, "power"), (DATA, "7,5", "data"), (CTRL, "3,4", "control")], 620)
s.save("block.svg")

# --- power.svg: the power tree with numbers ----------------------------------------------------------------------
s = Sheet(1100, 680, "Portable cluster v0: power tree", f"{total12:.0f} W at 12 V ({amps:.0f} A) at full load, from one {PSU_W} W supply; estimates until measured")
s.rect(40, 110, 170, 70, "Mains", f"about {total12 / 0.9:.0f} W at the wall", POWER)
s.rect(270, 110, 180, 70, "12 V supply", f"{PSU_W} W, {PSU_W / 12:.0f} A", POWER)
s.rect(510, 100, 260, 90, "12 V bus", f"{amps:.0f} A: busbar or 8 AWG", POWER, "#fff7ed")
s.line([(210, 145), (270, 145)], POWER, arrow=True); s.line([(450, 145), (510, 145)], POWER, arrow=True)
branches = [(f"Node {i + 1}", f"{NODE_W12} W, {NODE_W12 / 12:.1f} A", "e-fuse 20 A, I2C monitor") for i in range(NODES)]
branches += [("Switch", f"{SWITCH_W} W", "fuse 3 A"), ("Fans", f"{NODES} x {FAN_W} W, PWM", "fuse 2 A"), ("Controller", f"{CTRL_W} W", "5 V / 3.3 V buck")]
for i, (name, load, prot) in enumerate(branches):
    x = 40 + i * 150
    s.line([(640, 190), (640, 240), (x + 65, 240), (x + 65, 290)], POWER, width=2)
    s.rect(x, 290, 130, 60, prot.split(",")[0], prot.split(",")[1].strip() if "," in prot else "", POWER, size=12)
    s.line([(x + 65, 350), (x + 65, 400)], POWER, width=2, arrow=True)
    s.rect(x, 400, 130, 70, name, load, INK, "#f8fafc", size=13)
    if name.startswith("Node"):
        s.text(x + 65, 495, "CPU: 12 V direct", 11, MUTE, "middle")
        s.text(x + 65, 512, "24-pin: picoPSU", 11, MUTE, "middle")
s.text(30, 570, "Sequencing: the controller enables one node every 2 s, so their inrush does not add up.", 13, INK)
s.text(30, 592, "Branch wiring 16 AWG at 14 A (estimate; check against the chosen connector). Monitors report to the controller on I2C.", 13, INK)
s.text(30, 614, "The CPU connector's pin count (8 or 12) is unconfirmed: verify on the board's drawing before choosing connectors.", 13, POWER)
s.save("power.svg")

# --- network.svg ------------------------------------------------------------------------------------------------
s = Sheet(1100, 520, "Portable cluster v0: network", "Each node's 5 Gbit Ethernet to one switch inside the case; USB4 between neighbours later")
s.rect(400, 120, 300, 70, "Switch, 5 Gbit", "inside the case", DATA)
s.line([(700, 155), (1000, 155)], DATA, arrow=True); s.text(850, 145, "one port to the local network", 12, DATA, "middle")
for i in range(NODES):
    x = 60 + i * 255
    s.rect(x, 300, 215, 90, f"Node {i + 1}", "5 GbE   USB4 x2", INK, "#f8fafc")
    s.line([(x + 107, 300), (x + 107, 250), (550, 250), (550, 190)], DATA, dash="7,5")
    if i < NODES - 1:
        s.line([(x + 215, 345), (x + 255, 345)], AIR, width=2, dash="4,3")
s.text(30, 440, "Fabric (fabric/moe.py, modelled): a model split by layers spends under 1% of each token on the network, even at 10 Gbit.", 13, INK)
s.text(30, 462, "So 5 Gbit is enough for v0. The grey links are USB4 between neighbours, for expert-parallel splits later.", 13, INK)
s.save("network.svg")

# --- layout.svg: top view, mm to scale ---------------------------------------------------------------------------
k = 1.9
W, D = NODES * LANE, FRONT + BOARD + REAR
s = Sheet(int(W * k) + 260, int(D * k) + 300, "Portable cluster v0: layout, top view", f"to scale; about {W} x {D} x {HEIGHT} mm, {W * D * HEIGHT / 1e6:.0f} litres (estimate until the board drawing)")
ox, oy = 120, 160
s.rect(ox, oy, W * k, D * k, "", "", INK)
for i in range(NODES):
    x = ox + i * LANE * k
    s.rect(x + 6, oy + FRONT * k, LANE * k - 12, BOARD * k, f"Node {i + 1}", "170 mm board", INK, "#f8fafc", size=13)
    s.rect(x + 18, oy + 6, LANE * k - 36, FRONT * k - 12, "", "", AIR, "#f1f5f9")
    s.line([(x + LANE * k / 2, oy - 42), (x + LANE * k / 2, oy - 4)], AIR, width=2, arrow=True)                  # intake
    s.line([(x + LANE * k / 2, oy + D * k + 4), (x + LANE * k / 2, oy + D * k + 42)], AIR, width=2, arrow=True)  # exhaust
by = oy + (FRONT + BOARD) * k
s.rect(ox + 10, by + 10, 150 * k, REAR * k - 20, "12 V supply", "", POWER, size=13)
s.rect(ox + 170 * k, by + 10, 110 * k, REAR * k - 20, "Distribution", "board", POWER, size=13)
s.rect(ox + 290 * k, by + 10, W * k - 290 * k - 10, REAR * k - 20, "Switch", "", DATA, size=13)
s.text(ox + W * k / 2, oy - 52, "air in: 4 x 120 mm fans behind a filtered grille", 12, AIR, "middle")
s.text(ox + W * k / 2, oy + D * k + 62, "air out: rear, past the supply and the switch", 12, AIR, "middle")
s.text(ox - 12, oy + FRONT * k / 2 + 4, f"{FRONT}", 11, MUTE, "end"); s.text(ox - 12, oy + (FRONT + BOARD / 2) * k, f"{BOARD}", 11, MUTE, "end")
s.text(ox - 12, by + REAR * k / 2, f"{REAR}", 11, MUTE, "end"); s.text(ox + W * k + 14, oy + D * k / 2, f"{W} mm wide", 11, MUTE); s.text(ox + W * k + 14, oy + D * k / 2 + 16, f"({NODES} lanes of {LANE})", 11, MUTE)
s.save("layout.svg")
print("drew block, power, network, layout;", f"{total12:.0f} W, {amps:.1f} A")
