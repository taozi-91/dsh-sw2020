# -*- coding: utf-8 -*-
"""法兰盘模板 —— 环形盘体 + 内孔 + 圆周分布螺栓通孔。

体积自校验：V = π/4·((D²-d²) - n·db²)·t
"""
import sys
import os
import json
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import swapi


def build(m, outer_d, inner_d, thickness, bolt_n=4, bolt_d=0.0, pcd=0.0, flip_holes=False):
    m.begin_sketch("上视基准面")
    m.circle(0, 0, outer_d / 2.0)
    m.end_sketch()
    body = m.extrude(thickness)
    if body is None:
        raise RuntimeError("盘体拉伸失败")

    # 关键：孔草图必须建在实体面上（begin_sketch_on_face），
    # 建在基准面上的草图 FeatureCut 找不到轮廓会静默返回 None。
    if inner_d > 0:
        ring_x = (inner_d / 2.0 + outer_d / 2.0) / 2.0
        m.begin_sketch_on_face(ring_x, 0, thickness)
        m.circle(0, 0, inner_d / 2.0)
        m.end_sketch()
        if m.cut(through=True) is None:
            raise RuntimeError("内孔切除失败")

    if bolt_n and bolt_d > 0 and pcd > 0:
        m.begin_sketch_on_face(pcd / 2.0, 0, thickness)
        r = pcd / 2.0
        for i in range(bolt_n):
            ang = 2.0 * math.pi * i / bolt_n + math.radians(45)
            m.circle(r * math.cos(ang), r * math.sin(ang), bolt_d / 2.0)
        m.end_sketch()
        if m.cut(through=True) is None:
            raise RuntimeError("螺栓孔切除失败")
    return True


def expected_volume(outer_d, inner_d, thickness, bolt_n, bolt_d):
    base = math.pi / 4.0 * (outer_d ** 2 - inner_d ** 2) * thickness
    holes = bolt_n * math.pi / 4.0 * bolt_d ** 2 * thickness
    return base - holes


def main():
    payload = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    outer_d = float(payload.get("outerD", 130))
    inner_d = float(payload.get("innerD", 42))
    thickness = float(payload.get("thickness", 12))
    bolt_n = int(payload.get("boltCount", 4))
    bolt_d = float(payload.get("boltD", 7))
    pcd = float(payload.get("pcd", 114))
    save = payload.get("save")
    swapi.VISUAL_MODE = bool(payload.get("visual", False))

    sw = swapi.new_part()
    build(sw, outer_d, inner_d, thickness, bolt_n, bolt_d, pcd)

    got = sw.massprops()
    want = expected_volume(outer_d, inner_d, thickness, bolt_n, bolt_d)
    vol = got.get("volume_mm3", 0.0)
    info = {
        "ok": True, "outerD": outer_d, "innerD": inner_d, "thickness": thickness,
        "boltCount": bolt_n, "boltD": bolt_d, "pcd": pcd,
        "expectedVolume": round(want, 1), "actualVolume": round(vol, 1),
        "deviationPct": round((vol - want) / want * 100.0, 2) if want else None,
        "title": sw.title,
    }
    if save:
        info["save"] = sw.save(save)
    print(json.dumps(info, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
