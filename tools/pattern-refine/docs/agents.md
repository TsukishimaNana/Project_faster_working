# BJD 服装原型生成网站 — AI 编程助理规范

服装参数化纸样生成工具，所有纸样线条由数学函数驱动，禁止 AI 绘图。
技术栈：Next.js 14.2 · React 18.3 · TypeScript 5.4 · Tailwind 3.4 · Zustand 4.5 · pdf-lib 1.17 · next-intl 3.15

---

## 目录结构

```
app/               # 页面路由（App Router）
components/
├── canvas/        # SVG 纸样画布相关
├── doll/          # 人形选择 / 录入 / 胸围档位
├── panel/         # 参数调整面板
└── ui/            # Shadcn/ui 基础组件（不要手写）
lib/
├── patterns/      # 🔑 纸样计算引擎（纯函数，核心）
│   ├── types.ts   # 所有类型定义
│   ├── geometry.ts# 几何工具（曲线/交点/法向量）
│   ├── pants.ts   # 各服装类型计算函数
│   └── constants.ts # 中国式原型系数 + BJD 比例系数
├── layout/        # 自动排版算法（MaxRects）
├── export/        # PDF / DXF 文件生成
├── presets/       # 内置人形数据（JSON）
├── store/         # Zustand 全局状态
└── adapters/      # 数据存取层（v1.0=localStorage，v2.0=API）
public/fonts/      # NotoSansSC-Regular.ttf（PDF 中文字体，必须存在）
```

---

## 常用命令

```bash
npm run dev          # 启动开发服务器 http://localhost:3000
npm run build        # 静态导出构建（输出 /out 目录）
npm run type-check   # TypeScript 类型检查（不运行构建）
npm run lint         # ESLint 检查
```

> `next.config.ts` 中 `output: 'export'` 为 v1.0 静态模式，**构建产物是纯 HTML/JS/CSS**，不支持 Server Components 写数据库、不支持 API Routes 运行时逻辑。

---

## 领域约定（必须掌握，本项目特有）

### 单位系统
- **内部统一使用 mm**，所有 `PatternPiece` 坐标、参数值均为毫米浮点数
- SVG 渲染时：`svgPx = mm × zoomFactor`（zoomFactor 由画布组件提供，不要硬编码）
- PDF 生成时：`pt = mm × 2.8346`（pdf-lib 使用 pt 单位，必须换算）
- DXF 生成时：坐标直接用 mm，**但 Y 轴需要翻转**（SVG Y 向下，DXF/CAD Y 向上）

```typescript
// DXF 导出时的 Y 翻转公式（patternHeight 为当前裁片包围盒高度）
const dxfY = patternHeight - svgY
```

### 纸样计算函数规范

所有服装类型的计算函数**必须是纯函数**，无副作用，无全局状态访问：

```typescript
// ✅ 正确
export function calculatePantsPattern(
  measurements: DollMeasurements,
  params: PantsParameters
): PatternPiece[] { ... }

// ❌ 错误：不能读取 store、不能调用 API、不能修改外部变量
```

函数内几何不合法时（如脚口宽 > 臀围/2），必须 `throw new PatternGeometryError('描述')` 而非返回空数组或残缺裁片。

### 布纹线旋转约束
自动排版时裁片**只允许旋转 0° 或 180°**，禁止 90°/270°（会改变布纹经纬方向）。排版算法用包围盒（AABB）而非精确轮廓计算。

### 路径闭合要求
每个 `PatternPiece` 的 `segments` 必须形成**闭合路径**（最后一段终点 = 原点）。几何工具函数 `validateClosedPath()` 可用于断言。

### 数据存取层
v1.0 所有读写通过 `lib/adapters/` 接口操作，**不要在组件或 store 里直接调用 `localStorage`**：

```typescript
// ✅ 正确
import { profileRepository } from '@/lib/adapters/profileRepository'
await profileRepository.save(profile)

// ❌ 错误
localStorage.setItem('profiles', JSON.stringify(...))
```

---

## 编码规范

- 所有函数必须有完整 TypeScript 类型标注，包括返回值
- 组件文件 PascalCase，工具函数文件 camelCase，常量文件 camelCase
- 组件内**禁止**包含纸样计算逻辑，计算逻辑只在 `lib/patterns/` 中
- Zustand store 只存 UI 状态和计算结果，不存原始测量数据（测量数据由 adapter 持有）
- 新增服装类型：在 `lib/patterns/` 新建文件，在 `lib/patterns/types.ts` 扩展类型，**不修改已有文件的函数**
- 错误处理：组件层用 try-catch 捕获 `PatternGeometryError` 并展示为红色警告；禁止空 catch

### 编码与中文文件约束
- 仓库内所有**文本文件**统一为 **UTF-8（无 BOM）+ LF**
- 新建或重写中文文档、JSON、TS/TSX、SVG、脚本文件时，先确保编辑器按 UTF-8 打开，再写入
- 禁止把“终端显示乱码”直接等同于“文件内容已损坏”；终端、Git、编辑器三者必须先分别核对
- 读取中文文件优先使用显式 UTF-8 的方式；修改前先确认 source-of-truth 是磁盘文件本身，不是终端渲染结果
- PowerShell 下处理中文路径时，优先使用 `-LiteralPath`、`Get-ChildItem` 返回的对象路径、或脚本内 UTF-8 字符串对象；禁止手敲一段乱码路径继续覆盖写入

### 故障处置原则
- 发现乱码、路径异常、缓存错位、快照不一致时，先判断是**显示层问题**、**读写编码问题**、还是**真实数据已坏**
- 禁止只修“眼前能跑”的症状；必须优先修 source-of-truth、编码基线、失效策略、路径解析这类根因
- 若某次修复通过绕过原有校验、改用临时快照、复制旧数据、手动重命名乱码文件等方式“暂时成功”，默认视为**风险修复**而不是完成修复
- 对中文相关问题，结论必须附带证据：文件真实编码、读取方式、终端显示方式、以及修改前后的校验结果

---

## Git 上传规范

### 简化 Git Flow
- 默认保护分支为 `main`
- 日常开发从 `main` 切分支，不直接在 `main` 上堆未整理的提交
- 分支命名保持简单：`feat/...`、`fix/...`、`refactor/...`、`docs/...`、`test/...`
- 一个分支只做一类任务；如果任务已经明显跨模块，拆成多个 commit，不要混成一坨
- 合并或上传前，先确保 `npm run build`、`npm run lint`、`npm run type-check` 全通过
- 只有在用户明确说“上传 Git 仓库”时才执行 `git push`

### 提交粒度
- 一个 commit 对应一个完整任务
- 不把“样式微调 + 公式修正 + 导出改动”混在同一个 commit
- 未完成的中间试验代码不要提交
- 生成的 commit 应该满足：只看该 commit 的标题和 diff，就能知道它完成了什么

### Commit Message 格式
- 统一格式：`type: 简短中文动作描述`
- 推荐类型：`feat`、`fix`、`refactor`、`docs`、`test`、`chore`
- 示例：
  - `feat: 实现邮箱注册功能`
  - `fix: 修复登录 token 过期问题`
  - `test: 添加用户模块单元测试`
  - `refactor: 重构 API 错误处理逻辑`
  - `docs: 补充袖山高六等分构造说明`
  - `chore: 初始化 Shadcn 基础组件`

### 本项目执行规则
- 开发顺序：改代码 -> 本地验证 -> 整理 commit -> 等待用户确认上传
- 如果当前工作树不干净，先辨认哪些是本次任务，哪些是历史遗留，不允许把无关改动一起提交
- 上传前如需整理历史，只允许做安全的线性整理；禁止为了“看起来干净”而丢掉用户改动
- `knowledge_base/original_scan/` 视为用户提供的原始知识库，只读，不覆盖、不改名、不移动
- AI 生成的分析稿、步骤标注 SVG、派生 TXT 一律放到独立目录，例如 `knowledge_base/derived_stepwise/`

---

## 红线（绝对不能违反）

- **禁止 `any` 类型**，用 `unknown` + 类型守卫替代
- **禁止在纸样计算函数中产生副作用**（不得读写 store、DOM、localStorage、网络）
- **禁止混用 mm 和 px**（代码里出现魔法数字 `96`、`72`、`px` 单位的 mm 换算必须质疑）
- **禁止修改 `next.config.ts` 中的 `output: 'export'`**（v2.0 前不能删除）
- **禁止在 `app/api/` 下创建任何有实际逻辑的路由文件**（v1.0 该目录保持空占位）
- **禁止提交 `.env` 文件到 Git**
- **禁止旋转裁片 90° 或 270°**（排版算法里写死只允许 0 或 180）

---

## 已知陷阱

| 场景 | 错误做法 | 正确做法 |
|---|---|---|
| PDF 写入裁片坐标 | 直接传 mm 值 | mm × 2.8346 转换为 pt |
| DXF 写入 Y 坐标 | 直接用 SVG 的 y 值 | `dxfY = pieceHeight - svgY` |
| Next.js 14.2 配置文件 | 使用 `next.config.ts` 并指望 `next lint` / `next build` 正常工作 | 使用 `next.config.js` 或 `next.config.mjs`，同时保留 `output: 'export'` |
| 依赖安装版本 | 只按宽松范围安装，导致 `@supabase/supabase-js` 被解到需要 Node 20 的版本 | 按技术文档锁定兼容版本，并先检查当前 Node 版本与依赖 `engine` 要求 |
| `npm run type-check` 的 `.next/types` | 在 `.next/types` 尚未生成或增量状态异常时直接跑 `tsc`，可能报找不到 `app/*.ts` | 先运行一次 `next build`/`next dev` 生成类型产物，再重新执行 `npm run type-check` |
| `next lint` 改写 `tsconfig.json` | 手动删掉 `.next/types/**/*.ts` 后继续把 `tsc` 当作稳定工作流 | 接受 Next 14.2 会把该 include 写回；将校验顺序固定为先 `next build`/`next dev`，再执行 `npm run type-check` |
| Shadcn CLI 版本 | 直接把最新 `shadcn` CLI 包留在运行时依赖，或忽略 Node 18 的 `engine` 警告 | 仅用 `npx shadcn@latest ...` 做生成，不把 `shadcn` 包保留为运行时依赖；如需重复执行，先确认当前 Node 版本 |
| Shadcn 初始化改写布局 | 直接接受 CLI 写入的 `Geist` 字体和 `app/layout.tsx` 改动 | 回到项目原有字体/布局约束；生成组件后逐项复查 `layout.tsx`、`globals.css`、`package.json` |
| Shadcn 初始化改写全局样式 | 直接保留 `@import "shadcn/tailwind.css"` 和依赖 token 的 `@apply` | 保留本地 CSS 变量方案，删除仓库里不存在的样式导入，并避免使用当前 Tailwind 配置未声明的 utility token |
| `pdf-lib` 中文字体嵌入 | 只调用 `embedFont()` 加载 TTF 文件 | 先安装并注册 `@pdf-lib/fontkit`，再嵌入 `public/fonts/NotoSansSC-Regular.ttf` |
| 对称裁片排版 | 排两张 | 排一张，标注 `×2`，quantity 字段已存数量 |
| 添加新服装类型参数 | 直接改 `PantsParameters` | 新建独立 interface，在 `types.ts` 中 union |
| 中文字体 PDF 渲染 | 不嵌入字体 | 必须用 `pdf-lib` embed `NotoSansSC-Regular.ttf`，文件在 `public/fonts/` |
| 比例尺精度验证 | 肉眼看 | 导出 PDF 后量取 `ScaleBar` 组件标注的 3cm 刻度，误差须 < 0.5mm |
| 胸围档位切换后 | 直接重算所有纸样 | 只重算依赖胸围的服装类型（上衣/袖子），裤子/裙子不受影响 |
| 上衣尺寸调校 | 把背长、肩宽差异全塞进 `bustEase` / `shoulderDart` 两个参数 | 肩宽、胸围、背长优先进 `DollMeasurements`，`TopParameters` 只负责制图校正 |
| 背长建模 | 一律用 `臂长/2 + 常数` 代替背长 | 优先读取 `measurements.backLength`，缺失时才回退到臂长推导 |
| 在 `knowledge_base/original_scan/` 里生成或细修派生文件 | 直接把 AI 产物写回原始扫描目录，覆盖用户原件 | 原始扫描目录只读；派生文件写入 `knowledge_base/derived_stepwise/` 等独立目录 |
| 中文文本文件 | 看见乱码后继续局部修补、转存或覆盖写回 | 先确认文件真实编码；统一转成 UTF-8（无 BOM）后再继续修改，避免把显示层问题写回 source-of-truth |
| PowerShell 处理中文路径或内容 | 依赖终端渲染结果拼接路径、判断内容是否损坏 | 路径一律走 `-LiteralPath` 或对象路径；内容一律按 UTF-8 核对磁盘真实值，再决定是否重写 |
| 中文问题修复 | 通过改临时目录、手动复制文件、绕过原逻辑“先跑起来” | 先修编码基线、路径解析、读取方式和 source-of-truth；没有根因修复与复核证据，不算完成 |

### 纸样重构补充陷阱（本轮暴露）

#### 重复错误归纳

| 类型 | 反复出现的问题 | 长期规则 |
|---|---|---|
| 几何真值降级 | 明明有步骤标注 SVG / 最终 SVG，却继续用经验比例、旧 spline 或肉眼微调代替 | SVG 与步骤线是 source-of-truth；先抽锚点、分段、比例尺和目标坐标系，再写函数 |
| 表达层混淆 | 把调试线、叠图对照线、止口线、裁剪线混进默认主轮廓或默认界面，造成页面混乱 | 默认 `PatternPiece.segments` 只表达净样线；helper、overlay、seam/cut/export 必须走独立字段或独立渲染/导出层 |
| 锚点映射不一致 | 改了模板组源起终点，却忘记同步目标起终点，导致曲线被拉向旧锚点 | 每次修改模板组边界，都要同步检查 source start/end、target start/end、闭合顺序和相邻线段连接 |
| 默认参数误判 | UI 默认值已写入 store，却仍把“未设置”当作模板命中条件，导致四分默认走变体公式 | 基准判断必须比较“参数值是否等于基准值”，不能只判断 `null` / `undefined` |
| 局部坐标混用 | 前片、后片、镜像后坐标、世界坐标混算，导致下游袖山/裤线锚点漂移 | 上游先输出统一坐标系的参考几何；下游只消费明确命名的 world/local 锚点 |
| 修复范围失控 | 为了看叠图临时打开大量 helper 或覆盖主轮廓，修完后遗留到默认界面 | 调试显示必须默认收窄；提交前检查默认页面只显示目标用户需要的线层 |

| 场景 | 错误做法 | 正确做法 |
|---|---|---|
| 读取步骤标注线 SVG | 把步骤图当“帮助理解的参考”，继续用经验比例或 spline 猜曲线 | 把步骤标注线 SVG 和最终不含止口 SVG 当作几何真值；先抽锚点/模板，再写函数 |
| 四分基准叠图校准 | 一边看叠图一边微调 `0.2/0.3/0.4`、`1/4`、`2/3` 之类的经验比例 | 先确认当前页面是否命中“四分基准模板分支”；未命中前，任何叠图对比都不可靠 |
| 模板分支命中条件 | 只在参数为 `null` / “未设置” 时命中模板，忽略 UI 默认值实际已写入 store | 默认参数等于基准值时也应命中模板；不要把“默认值”误判成“用户已进入变体模式” |
| 上游几何供下游使用 | 混用前片局部坐标、后片局部坐标、镜像后坐标，直接计算袖山/辅助线 | 先在统一坐标系中输出袖子/裤子需要的参考几何，再由下游组装轮廓 |
| 路径未闭合排查 | 直接调控制点或怀疑 `validateClosedPath()` 太严格 | 先核对 `origin` 是否与轮廓片段顺序一致；再检查模板分段方向、末段终点和局部锚点是否一致 |
| 四分裤子模板 | 直接把原始 SVG 坐标当 mm 使用 | 先按比例尺把模板单位换算成 mm，再参与轮廓构建与叠图比对 |
| 四分裤子默认参数 | 默认参数回退到估算裆深、估算裤长，导致模板分支永远不命中 | 四分基准应优先吃实测 `crotchDepth` 与对应默认参数，确保默认页面能直接进入模板口径 |
| 页面辅助线调试 | 在轮廓还没对上时同时展示过多 helper 文字与线，误导叠图判断 | 先收窄默认辅助线显示，只保留关键基准线；轮廓稳定后再逐层放开调试线 |
| 净样线与裁剪线 | 用含 5mm 止口的外放裁剪线覆盖 `PatternPiece.segments` 主轮廓 | 主轮廓默认保持净样线；需要显示/导出裁剪线时，拆分 `seam/cut` 表达并按缝份量生成 |
| 模板组锚点调整 | 源 SVG 曲线终点改成臀围接点，但目标终点仍传腰中心等旧锚点 | 修改模板组边界后，同步更新映射目标锚点，并检查相邻直线/曲线连接关系 |
