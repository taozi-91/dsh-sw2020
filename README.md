# dsh-sw2020

给 DSH 用的 SolidWorks 2020 驱动插件。Win7 / Python 3.8 环境实测可用。

## 安装

把仓库放到一个固定目录，然后用 DSH 的插件管理器以本地链接方式装入：

```
plugin_manager install_bundle target=link:D:\plugins\dsh-sw2020
```

也可以手动在 profile 的 `package.json` 依赖里加一行：

```json
{ "dependencies": { "dsh-sw2020": "link:D:\\plugins\\dsh-sw2020" } }
```

装好后重启 DSH，调用 `sw2020_status` 验证——能返回 `connected: true` 和 SW 版本号就通了。

## 环境要求

- Windows 7 SP1 或更高（Win7 下 Python 3.8 是官方支持的最后版本，正好够用）
- Python 3.8，已 `pip install pywin32`
- SolidWorks 2020 已启动（插件连已运行的实例，不自己拉起）
- 中文版 SW 的基准面名是「前视基准面 / 上视基准面 / 右视基准面」，脚本里两种名字都能认

## 四个工具

| 工具 | 用途 |
|---|---|
| `sw2020_status` | 查连接状态、版本、打开文档数、零件模板路径。建模前先跑 |
| `sw2020_shaft` | 多段阶梯轴（默认五阶），每段给 `[直径, 长度]`，单位 mm |
| `sw2020_disc` | 带孔圆盘：外径/厚度/中心孔/均布螺栓孔 |
| `sw2020_run` | 跑 backend 目录下任意自建脚本，自己扩展的入口 |

## 自己加模板

在 `backend/` 下加一个 `tpl_xxx.py`，按现有模板的骨架写：

```python
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import swapi

def main():
    payload = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    m = swapi.new_part()
    m.begin_sketch("上视基准面")
    m.circle(0, 0, 30)
    m.end_sketch()
    m.extrude(10)
    print(json.dumps({"ok": True, "title": m.title}, ensure_ascii=False))
```

脚本约定：从 `argv[1]` 收 JSON 参数，往 stdout 打一行 JSON 结果。写好后用 `sw2020_run` 直接调，不用改插件代码。

## 建模约定（踩过坑的）

- 单位一律 mm，脚本内部自动转米
- 圆盘/法兰的孔草图**必须建在实体面上**（`begin_sketch_on_face`），建在基准面上 `FeatureCut3` 会静默返回 None
- `begin_sketch_on_face` 的选面点必须落在实体上，不能选已经切空的区域
- 旋转体（轴、法兰主体）轮廓要画在轴一侧，旋转轴用 `centerline`
- 圆角必须 `Options=2`（等半径），否则静默失败
- 多文档积累会拖慢甚至卡死，连续测试前先 `CloseAllDocuments(True)`

## 当前局限

- DXF / PDF 图纸自动建模：还没做
- 扫描件：没做
- 只有两个模板（轴、圆盘），法兰盘模板在 `backend/tpl_flange.py`，逻辑已按面草图改过但还没实测
