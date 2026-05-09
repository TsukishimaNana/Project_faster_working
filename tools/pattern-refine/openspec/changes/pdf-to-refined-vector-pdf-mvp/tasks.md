# Tasks

- [x] 添加扫描型 BJD 纸样 PDF 的 sample fixture 引用。
- [x] 实现 PDF page rendering 到 high-resolution images。
- [x] 实现从白底中提取 black-line。
- [x] 增加初始 raster-to-vector SVG conversion adapter。
- [x] 将 vectorized SVG 解析为可处理的 path geometry。
- [ ] 过滤文字/噪声碎片并输出主裁片轮廓候选，使 `cleaned.svg` 接近 `pink-dress-simple-reference.svg` 的对象级表达。
- [ ] 实现 corners、notches、right angles、triangle marks、short alignment marks 和 straight edges 的 feature classification。
- [ ] 对符合条件的 curve regions 实现 path smoothing。
- [ ] 增加 `0.2mm` maximum deviation validation。
- [x] 导出 `*.cleaned.svg` debug output。
- [ ] 导出 `*.refined.pdf` vector output。
- [ ] 围绕 sample PDF 和 feature preservation 增加 acceptance tests。
