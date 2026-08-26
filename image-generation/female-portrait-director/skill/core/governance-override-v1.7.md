# Female Portrait Director Governance Override V1.7

本文件是 V1.7 上层治理合同。若旧 `conflict-resolution.md`、Route、Overlay、Tool 或历史示例与本文件冲突，以本文件为准。

## 1. 任务模式先于风格路由

先判断：

- reference identity preserving
- fictional/new portrait
- restoration/preserve
- reconstruction/recompose

Route 只能在任务模式确定后选择。

## 2. 统一优先级

1. 安全、成年、授权。
2. 用户本轮明确任务、数量、画幅、保留项和修改项。
3. 身份保留任务中未被用户要求改变的人物身份不变量。
4. 用户确认的长期 Profile。
5. 解剖、重力、衣料与环境物理。
6. 摄影事件与空间关系。
7. Route、构图、灯光、美颜、镜头。
8. Overlay、平台适配和默认补全。

用户本轮明确改变发型、服装、背景、姿态或其他可变字段时，应作为本轮 override，不得被参考图默认值抢回。需要保持“同一个人”时，未被点名改变的脸型、五官比例、自然不对称和独特身份特征继续锁定。

## 3. 美颜

“医美级美颜”统一解释为 `医美级自然精修`，表示高完成度 retouch quality。

默认允许：临时瑕疵清理、肤色与反射优化、偶发疲态减轻、眼神/眉睫/唇纹/发丝细节提升。

身份保留任务默认禁止：模板脸、换骨相、改眼距、改鼻型、改唇形、年龄坍缩、塑料磨皮、夸张毛孔锐化。

## 4. 构图

- `preserve`：原图修复、保背景、原图构图不变。只做校正、安全裁切、必要扩边和局部优化。
- `recompose`：用户允许重新构图或重建场景时，Route 才能重设机位、主体位置和空间层级。

“自动完美构图”不能静默把 preserve 任务升级成 recompose。

## 5. 光影

- `preserve-source`：保留原现场主光方向，优化曝光、反差、白平衡、局部补光与阴影可读性。
- `relight`：用户允许重新打光时，才重新设计主辅光与轮廓光。

具体灯光风格属于策略层，不能覆盖任务模式。

## 6. 输出数量

用户明确数量最高。主任务决定默认 batch count，Route、Overlay、情绪词和动作库不得擅自扩大数量。

“大师出片 + 情绪大片”时，若主任务定义为单张，则情绪只改变画面表达，不自动变成五张。

## 7. 历史参考图

历史成片及其 Prompt 默认属于 example / eval / historical-output。只有用户当前上传的授权参考图或已登记的 identity/body/unique-feature anchor 才能进入人物真值层。

## 8. Parameter propagation

最终 fused prompt 前必须检查：

- 用户所有显式字段仍在。
- Route 没有覆盖用户字段。
- reference lock 没有把用户明确修改的可变字段强制恢复。
- 美颜没有改变未授权身份结构。
- 构图和光影模式与任务类型一致。
- batch count 没有被子模块改变。
