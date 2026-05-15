# 状态包模板

所有子代理必须用明确状态返回，禁止只写“未完成”或“有问题”。

## 状态码

| 状态 | 含义 |
|---|---|
| `DONE` | 任务完成，允许范围内验证已通过 |
| `DONE_WITH_CONCERNS` | 任务完成，但有风险、假设或未覆盖项 |
| `NEEDS_CONTEXT` | 缺少上下文，父级可以补充 |
| `NEEDS_MAIN_THREAD_COMMAND` | 需要主线程执行命令，例如全量测试、build、Git 状态 |
| `BLOCKED_PERMISSION` | 遇到权限、安装、网络、Git 写入、长期服务或全局配置 |
| `FAILED_VALIDATION` | 实现后验证失败 |

## 通用模板

```text
STATUS:
SCOPE:
CHANGED_FILES:
VALIDATION:
RISKS:
NEXT:
```

当前项目若涉及几何或验收，建议额外填写：

```text
DELIVERY_IMPACT: 对 reference-guided final SVG / per-piece 0.2mm 的影响
ROUTE_CHECK: 是否存在继续沿 outline 或 scan-only centerline 主线漂移的风险
RESULT_STATE_HINT: 建议主线程将当前结果视为继续开发 / 内测版 / 可交付 MVP 中的哪一种
```

## 权限阻塞模板

```text
STATUS: BLOCKED_PERMISSION
COMMAND:
WHY:
DONE_SO_FAR:
CHANGED_FILES:
RISK:
NEXT:
```

## 阶段完成模板

```text
STATUS:
SCOPE:
OPEN_SPEC_TASKS:
CHANGED_FILES:
DIFF_REVIEW:
VALIDATION:
MAIN_THREAD_COMMANDS:
RISKS:
NEXT:
```

当前项目阶段完成包若涉及 MVP 进展，还应明确：

```text
DELIVERY_IMPACT:
PER_PIECE_EVIDENCE:
ROUTE_CHECK:
RESULT_STATE_HINT:
```
