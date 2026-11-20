"""Check a KiCad XML export against the physical backplane wiring contract.

Usage: python verification/check_netlist.py path/to/backplane.xml
Generate XML with: kicad-cli sch export netlist --format kicadxml ...
"""
from pathlib import Path
import csv
import sys
from xml.etree import ElementTree as ET


def validate(xml_path):
    board = Path(__file__).resolve().parents[1]
    design = ET.parse(xml_path)
    actual = {}
    for net in design.findall("./nets/net"):
        endpoints = frozenset((node.attrib["ref"], node.attrib["pin"]) for node in net)
        if endpoints in actual:
            raise ValueError(f"Repeated endpoint set {endpoints}")
        actual[endpoints] = net.attrib["name"]

    expected = set()

    def require(endpoints, net_name=None):
        endpoints = frozenset(endpoints)
        if endpoints not in actual:
            raise ValueError(f"Missing or additional endpoints on {sorted(endpoints)}")
        if net_name is not None and actual[endpoints] != net_name:
            raise ValueError(f"Expected {net_name}, got {actual[endpoints]}")
        expected.add(endpoints)

    with (board / "slot_links.csv").open(encoding="utf-8-sig", newline="") as source:
        links = list(csv.DictReader(source))
    slots = [f"{group}{index}" for group in "CH" for index in range(1, 7)]
    signals = ["REFCLK", "SYNC", "SCLK", "CS_N", "MOSI", "MISO", "SLOT_OK_N", "RUN_PERMIT_N"]
    if len(links) != 96 or len({(r["slot"], r["signal"]) for r in links}) != 96:
        raise ValueError("Expected one row for every slot and differential signal")
    for row in links:
        slot = slots.index(row["slot"])
        signal = signals.index(row["signal"])
        for letter, side, polarity in [("a", "p", "P"), ("b", "n", "N")]:
            master = (f"J{2 + slot // 4}", f"{letter}{8 * (slot % 4) + signal + 1}")
            pwm = (f"J{11 + slot}", f"{letter}{signal + 1}")
            name = f"/{row['slot']}.{row['signal']}_{polarity}"
            if (row["master_ref"], row["master_" + side], row["pwm_ref"], row["pwm_" + side],
                row["kicad_net_" + side]) != (*master, *pwm, name):
                raise ValueError(f"Published pinout mismatch on {name}")
            require([master, pwm], name)

    require([("J1", "1"), ("F1", "1")])
    require([("F1", "2"), ("Q1", "2")])
    require([("Q1", "1"), ("D1", "2"), ("R1", "1")])
    require([("Q1", "3"), ("D1", "1"), ("TP1", "1"), ("F2", "1")]
            + [(f"F{i}", "1") for i in range(11, 23)], "+12V")
    require([("F2", "2"), ("TP3", "1"), ("J2", "c31"), ("J2", "c32")])
    ground = {("J1", "2"), ("TP2", "1"), ("R1", "2")}
    for connector in (2, 3, 4):
        for index in range(1, 31 if connector == 2 else 33):
            ground.add((f"J{connector}", f"c{index}"))
    for index in range(11, 23):
        socket = f"J{index}"
        require([(f"F{index}", "2"), (f"TP{index}", "1"), (socket, "a9"), (socket, "a10")])
        ground.update((socket, p) for p in ["b9", "b10"] + [f"c{i}" for i in range(1, 9)])
        for row in "abc":
            for pos in range(9, 17):
                if pos <= 10 and row in "ab":
                    continue
                endpoint = (socket, f"{row}{pos}")
                require([endpoint])
                if not actual[frozenset([endpoint])].startswith("unconnected-"):
                    raise ValueError(f"Missing no-connect on {endpoint}")
    require(ground, "GND")
    if expected != set(actual):
        raise ValueError(f"Unexpected nets: {set(actual) - expected}")

    # Verify the published purchase references, part numbers and URLs against the export.
    comps = design.findall("./components/comp")
    parts = {}
    for component in comps:
        fields = {f.attrib["name"]: f.text or "" for f in component.findall("fields/field")}
        ref = component.attrib["ref"]
        if ref.startswith("TP"):
            if component.findtext("footprint") != "TestPoint:TestPoint_Pad_D2.0mm":
                raise ValueError(f"Unexpected test pad {ref}")
            continue
        parts[ref] = (fields["MPN"], fields["Supplier_URL"], component.findtext("footprint"))
    with (board / "BOM.csv").open(encoding="utf-8-sig", newline="") as source:
        bom = list(csv.DictReader(source))
    purchased = {}
    for row in bom:
        refs = row["References"].split()
        if int(row["Quantity"]) != len(refs):
            raise ValueError(f"Quantity error on {row['MPN']}")
        for ref in refs:
            if ref in purchased:
                raise ValueError(f"Duplicate BOM reference {ref}")
            purchased[ref] = (row["MPN"], row["Purchase_URL"], row["Footprint"])
    if parts != purchased:
        raise ValueError("BOM and schematic export disagree")
    print(f"PASS: {len(actual)} nets, 96 differential pairs, 13 isolated fused outputs, "
          f"240 NC contacts, {len(parts)} purchased parts, {len(comps)-len(parts)} copper pads.")


if __name__ == "__main__":
    validate(sys.argv[1])
