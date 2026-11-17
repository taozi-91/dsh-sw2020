// dsh-sw2020 —— SolidWorks 2020 驱动插件（Win7 / Python 3.8）
// 通过后端 Python 脚本（win32com IDispatch 后期绑定）驱动已运行的 SolidWorks。
import { spawnSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export const name = 'dsh-sw2020'
export const inject = ['tools']

const HERE = path.dirname(fileURLToPath(import.meta.url))
const BACKEND = path.join(HERE, 'backend')

const DEFAULT_TIMEOUT = 300000

function toolDef(spec) {
  return {
    name: spec.name,
    description: spec.description,
    parameters: spec.parameters,
    timeoutMs: spec.timeoutMs ?? DEFAULT_TIMEOUT,
    output: {
      schema: spec.outputSchema ?? { type: 'string' },
      render: (_args, value) => [{
        type: 'text',
        text: typeof value === 'string' ? value : JSON.stringify(value, null, 2),
      }],
    },
    execute: spec.execute,
  }
}

function pythonBin(config) {
  return (config && config.pythonPath) || process.env.DSH_SW_PYTHON || 'python'
}

function runBackend(config, script, payload, timeoutMs) {
  const file = path.join(BACKEND, script)
  const args = [file, JSON.stringify(payload || {})]
  const res = spawnSync(pythonBin(config), args, {
    encoding: 'utf8',
    timeout: timeoutMs ?? DEFAULT_TIMEOUT,
    windowsHide: true,
    env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1' },
  })
  if (res.error) {
    return `[sw2020] 调用后端失败：${res.error.message}\n脚本：${file}`
  }
  const stdout = String(res.stdout || '').trim()
  const stderr = String(res.stderr || '').trim()
  const lines = stdout.split(/\r?\n/).filter(Boolean)
  for (let i = lines.length - 1; i >= 0; i -= 1) {
    try {
      return format(JSON.parse(lines[i]))
    } catch {
      // 继续往前找
    }
  }
  if (stderr) return `[sw2020] 后端报错：\n${stderr}`
  return `[sw2020] 无有效输出（exit ${res.status}）\n${stdout}`.trim()
}

function format(obj) {
  if (obj == null || typeof obj !== 'object') return String(obj)
  if (obj.ok === false) {
    return `❌ 失败：${obj.error || '后端返回 ok=false'}`
  }
  const rows = []
  for (const [k, v] of Object.entries(obj)) {
    if (k === 'ok') continue
    if (v && typeof v === 'object') {
      rows.push(`${k}: ${JSON.stringify(v, null, 2)}`)
    } else {
      rows.push(`${k}: ${v}`)
    }
  }
  return `✅ ok\n${rows.join('\n')}`
}

export function apply(ctx, config = {}) {
  const cfg = { ...config }

  // ── 1. 连接状态 ─────────────────────────────────────────────────────────
  ctx.effect(() => ctx.tools.register(toolDef({
    name: 'sw2020_status',
    description: '检查 SolidWorks 2020 连接状态：是否已启动、版本号、当前打开的文档数、零件模板路径。建模前先跑这个。',
    parameters: { type: 'object', properties: {}, additionalProperties: false },
    execute: async () => runBackend(cfg, 'sw_status.py', {}),
  })))

  // ── 2. 五阶轴 ───────────────────────────────────────────────────────────
  ctx.effect(() => ctx.tools.register(toolDef({
    name: 'sw2020_shaft',
    description: '用旋转特征建多段阶梯轴（默认五阶）。轴沿 X 轴，每段给直径和长度，单位 mm。体积会自动和手算值比对。',
    parameters: {
      type: 'object',
      properties: {
        sections: {
          type: 'array',
          description: '每段 [直径mm, 长度mm]，按顺序从一端到另一端',
          items: { type: 'array', items: { type: 'number' }, minItems: 2, maxItems: 2 },
        },
        save: { type: 'string', description: '保存路径（.sldprt），不填则不保存' },
        visual: { type: 'boolean', description: '是否逐步展示建模过程（默认 false 快速建模）' },
      },
      additionalProperties: false,
    },
    execute: async (args) => runBackend(cfg, 'tpl_shaft.py', a2o(args)),
  })))

  // ── 3. 带孔圆盘 ─────────────────────────────────────────────────────────
  ctx.effect(() => ctx.tools.register(toolDef({
    name: 'sw2020_disc',
    description: '建带孔圆盘：外径/厚度/中心孔/均布螺栓孔，单位 mm。孔草图建在实体顶面上（已验证的切除路径）。',
    parameters: {
      type: 'object',
      properties: {
        diameter: { type: 'number', description: '圆盘外径 mm，默认 60' },
        thickness: { type: 'number', description: '厚度 mm，默认 10' },
        holeDiameter: { type: 'number', description: '中心孔直径 mm，0 表示不开，默认 20' },
        boltCount: { type: 'number', description: '均布螺栓孔数量，0 表示不开，默认 4' },
        boltD: { type: 'number', description: '螺栓孔直径 mm，默认 6' },
        pcd: { type: 'number', description: '螺栓孔分布圆直径 mm，默认 40' },
        save: { type: 'string', description: '保存路径（.sldprt）' },
        visual: { type: 'boolean', description: '是否逐步展示建模过程' },
      },
      additionalProperties: false,
    },
    execute: async (args) => runBackend(cfg, 'tpl_disc.py', a2o(args)),
  })))

  // ── 4. 跑任意后端脚本（自己扩展的入口）──────────────────────────────────
  ctx.effect(() => ctx.tools.register(toolDef({
    name: 'sw2020_run',
    description: '运行 backend 目录下的自定义 Python 脚本（自己加的建模脚本用这个入口）；脚本从 argv[1] 收 JSON、往 stdout 打 JSON。',
    parameters: {
      type: 'object',
      properties: {
        script: { type: 'string', description: 'backend 目录下的脚本文件名，例如 tpl_flange.py' },
        payload: { type: 'object', description: '传给脚本的 JSON 参数', additionalProperties: true },
      },
      required: ['script'],
      additionalProperties: false,
    },
    execute: async (args) => {
      const script = String(args?.script || '')
      if (!script || script.includes('..') || script.includes('/') || script.includes('\\')) {
        return '❌ script 必须是 backend 目录下的纯文件名'
      }
      return runBackend(cfg, script, args?.payload || {})
    },
  })))
}

function a2o(args) {
  const out = {}
  for (const [k, v] of Object.entries(args || {})) {
    if (v !== undefined && v !== null) out[k] = v
  }
  return out
}
