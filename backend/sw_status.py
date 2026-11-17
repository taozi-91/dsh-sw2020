# -*- coding: utf-8 -*-
"""连接状态自检：SolidWorks 是否在运行、版本、文档数、零件模板。"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import swapi


def main():
    try:
        sw = swapi.get_sw()
    except Exception as exc:
        print(json.dumps({"ok": False, "error": "连不上 SolidWorks: %s" % exc},
                         ensure_ascii=False))
        return

    docs = []
    try:
        d = sw.GetDocuments
        if isinstance(d, (tuple, list)):
            docs = [str(x.GetTitle) for x in d]
    except Exception:
        pass

    info = {
        "ok": True,
        "connected": True,
        "revision": str(getattr(sw, "RevisionNumber", "unknown")),
        "openDocuments": len(docs),
        "documentTitles": docs[:10],
        "partTemplate": str(swapi.get_part_template(sw)) if hasattr(swapi, "get_part_template") else None,
        "pythonVersion": sys.version.split()[0],
    }
    print(json.dumps(info, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
