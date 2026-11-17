# -*- coding: utf-8 -*-
"""五阶轴模板 —— 用旋转特征一次成型（轮廓=阶梯折线，旋转轴=X 轴）。

轴沿 X 方向摆放：X = 长度方向，Y = 半径方向。
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import swapi


def build_steps(m, sections):
    """sections: [(diameter_mm, length_mm), ...] 从 X=0 端开始。"""
    total = sum(l for _, l in sections)
    pts = [(0.0, 0.0)]
    x = 0.0
    for i, (d, l) in enumerate(sections):
        r = d / 2.0
        if i == 0:
            pts.append((x, r))
        else:
            pts.append((x, r))
        x += l
        pts.append((x, r))
    pts.append((x, 0.0))
    pts.append((0.0, 0.0))

    m.begin_sketch("前视基准面")
    m.centerline(-5.0, 0.0, total + 5.0, 0.0)
    m.polyline(pts)
    m.end_sketch()
    feat = m.revolve(360)
    return feat, total


def main():
    import json
    payload = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    sections = payload.get("sections") or [[20, 30], [30, 25], [40, 20], [30, 25], [20, 30]]
    save = payload.get("save")
    swapi.VISUAL_MODE = bool(payload.get("visual", False))

    sw = swapi.new_part()
    feat, total = build_steps(sw, [(float(d), float(l)) for d, l in sections])
    info = {"ok": feat is not None, "lengthMm": total,
            "sections": sections, "title": sw.title}
    if feat is not None:
        try:
            info["massprops"] = sw.massprops()
        except Exception as exc:
            info["masspropsError"] = str(exc)
    if save and feat is not None:
        info["save"] = sw.save(save)
    print(json.dumps(info, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
