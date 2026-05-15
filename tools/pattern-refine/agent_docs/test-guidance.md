# 测试细则

## 最小原则

- 只跑与当前改动直接相关的最小测试集，再视结果扩大范围。
- 先验证失败，再写实现，再验证通过。
- 如果测试环境尚未完成脚手架，明确说明“未执行”的原因，不要假装通过。

## 推荐顺序

```powershell
# 后端单测
cd backend
pytest -p no:cacheprovider tests/<path_to_test>.py -v

# 后端回归
pytest -p no:cacheprovider -q

# 前端单测
cd frontend
npm test -- --runInBand

# 前端构建
npm run build
```

## 提交前检查

- 后端改动：至少运行相关 `pytest -p no:cacheprovider`，避免 `.pytest_cache` 写入权限噪声影响验证判断
- 前端改动：至少运行相关 `vitest` 或 `npm test`
- API / 类型改动：同时检查前后端接口名称是否一致
- 导出 / 文件处理改动：补一条成功路径和一条失败路径验证

## 失败时的处理

- 先记录失败命令、失败现象、可能原因
- 不要跳过失败继续声称“已完成”
- 如果失败来自基线问题，明确标记为基线阻塞，再询问是否继续
