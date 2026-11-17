# -*- coding: utf-8 -*-
"""带孔圆盘模板 —— 已验证：Φ60×10 圆盘 + Φ20 中心孔 + 4×Φ6 均布孔。

体积自校验：V = π/4·(D² - d² - n·db²)·t
"""
import sys
import os
import json
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import swapi


def build(m, diameter, thickness, hole_d=0.0, bolt_n=0, bolt_d=0.0, pcd=0.0):
    m.begin_sketch("上视基准面")
    m.circle(0, 0, diameter / 2.0)
    m.end_sketch()
    if m.extrude(thickness) is None:
        raise RuntimeError("盘体拉伸失败")

    # 孔草图必须建在实体面上；选面点不能落在已切空的区域
    if hole_d > 0:
        px = (hole_d / 2.0 + diameter / 2.0) / 2.0
        m.begin_sketch_on_face(px, 0, thickness)
        m.circle(0, 0, hole_d / 2.0)
        m.end_sketch()
        if m.cut(through=True) is None:
            raise RuntimeError("中心孔切除失败")

    if bolt_n and bolt_d > 0 and pcd > 0:
        r = pcd / 2.0
        m.begin_sketch_on_face(r, 0, thickness)
        for i in range(bolt_n):
            ang = 2.0 * math.pi * i / bolt_n + math.radians(45)
            m.circle(r * math.cos(ang), r * math.sin(ang), bolt_d / 2.0)
        m.end_sketch()
        if m.cut(through=True) is None:
            raise RuntimeError("螺栓孔切除失败")
    return True


def expected_volume(diameter, thickness, hole_d, bolt_n, bolt_d):
    base = math.pi / 4.0 * diameter ** 2 * thickness
    center = math.pi / 4.0 * hole_d ** 2 * thickness if hole_d else 0.0
    holes = bolt_n * math.pi / 4.0 * bolt_d ** 2 * thickness
    return base - center - holes


def main():
    payload = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    diameter = float(payload.get("diameter", 60))
    thickness = float(payload.get("thickness", 10))
    hole_d = float(payload.get("holeDiameter", 20))
    bolt_n = int(payload.get("boltCount", 4))
    bolt_d = float(payload.get("boltD", 6))
    pcd = float(payload.get("pcd", 40))
    save = payload.get("save")
    swapi.VISUAL_MODE = bool(payload.get("visual", False))

    m = swapi.new_part()
    build(m, diameter, thickness, hole_d, bolt_n, bolt_d, pcd)

    got = m.massprops()
    vol = got.get("volume_mm3", 0.0)
    want = expected_volume(diameter, thickness, hole_d, bolt_n, bolt_d)
    info = {
        "ok": True, "diameter": diameter, "thickness": thickness,
        "holeDiameter": hole_d, "boltCount": bolt_n, "boltD": bolt_d, "pcd": pcd,
        "expectedVolume": round(want, 2), "actualVolume": round(vol, 2),
        "deviationPct": round((vol - want) / want * 100.0, 3) if want else None,
        "title": m.title,
    }
    if save:
        info["save"] = m.save(save)
    print(json.dumps(info, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
