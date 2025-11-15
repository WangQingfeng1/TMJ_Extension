# Coarse Registration 模块

## 概述

Coarse Registration (粗配准) 模块是 TMJ Extension 的第三个核心模块，用于基于基准点的自动粗配准。该模块通过用户选择的对应基准点对自动计算相似变换，将 Moving Volume 对齐到 Fixed Volume，为后续精配准提供良好的初始位置。

## 功能特性

### 1. 基准点管理
- **持续放置模式**: 连续放置多个基准点对，无需重复操作
- **颜色编码**: Fixed 点显示为红色，Moving 点显示为绿色
- **实时计数**: 显示当前基准点对数量
- **验证机制**: 自动验证点对数量和匹配性

### 2. 自动配准
- **相似变换计算**: 使用 VTK LandmarkTransform 计算最优变换
- **参数解析**: 自动提取平移、旋转、缩放参数
- **RMS 误差评估**: 计算配准后的均方根误差
- **可视化反馈**: 根据误差大小提供颜色编码

### 3. 结果保存
- **场景文件夹**: 保存到配准流程总文件夹下的子文件夹
- **完整数据**: 包含配准后的图像、变换矩阵、基准点和配准信息
- **数据独立**: 使用深拷贝，不影响原始数据

## 使用流程

### 步骤 1: 选择数据
从 Data Manager 场景子文件夹中选择 Fixed_Volume 和 Moving_Volume。

### 步骤 2: 放置基准点 (分两步)

**2.1 标注 Fixed 基准点**
1. 点击"放置 Fixed 基准点"按钮
2. 在 Fixed Volume 上选择易识别的解剖标志点
3. Fixed 点显示为红色
4. 至少放置 3 个点 (建议 5-10 个)
5. 完成后再次点击按钮退出

**2.2 标注 Moving 基准点**
1. 点击"放置 Moving 基准点"按钮
2. 在 Moving Volume 上选择**与 Fixed 点对应的**解剖标志点
3. Moving 点显示为绿色
4. **必须按照 Fixed 点的顺序**标注
5. 确保点数与 Fixed 点相同
6. 完成后再次点击按钮退出

**基准点选择建议**:
- 选择稳定的骨性标志点 (如骨性突起、关节面、孔道等)
- 在感兴趣区域均匀分布
- 避免完全对称的点
- 确保 Fixed 和 Moving 上的点严格对应
- 按相同顺序标注对应点

### 步骤 3: 计算粗配准
1. 点击"计算粗配准变换"按钮
2. 系统自动计算相似变换矩阵
3. 查看 RMS 配准误差:
   - 🟢 绿色 (< 2.0 mm): 优秀
   - 🟠 橙色 (2.0-5.0 mm): 良好
   - 🔴 红色 (> 5.0 mm): 需检查

### 步骤 4: 保存结果
1. 设置场景子文件夹名称 (默认: "Coarse Registration")
2. 点击"保存粗配准结果到场景"
3. 结果保存到 `{总文件夹}/Coarse Registration/`

## 输出内容

保存的场景子文件夹包含:

| 节点名称 | 类型 | 说明 |
|---------|------|------|
| CoarseReg_Fixed | Volume | 固定图像 (参考) |
| CoarseReg_Moving | Volume | 粗配准后的浮动图像 (已绑定变换) |
| CoarseReg_Transform | Transform | 相似变换矩阵 |
| CoarseReg_Fixed_Fiducials | Fiducials | Fixed 基准点 (红色) |
| CoarseReg_Moving_Fiducials | Fiducials | Moving 基准点 (绿色) |
| CoarseReg_Info | Text | 配准信息 (点数、误差、坐标) |

## 技术细节

### 变换类型
相似变换 (Similarity Transform):
- **平移 (Translation)**: X, Y, Z 方向移动
- **旋转 (Rotation)**: 绕 X, Y, Z 轴旋转
- **统一缩放 (Uniform Scale)**: 各方向等比例缩放

### 算法
使用 VTK 的 `vtkLandmarkTransform`:
```python
landmarkTransform = vtk.vtkLandmarkTransform()
landmarkTransform.SetSourceLandmarks(movingPoints)
landmarkTransform.SetTargetLandmarks(fixedPoints)
landmarkTransform.SetModeToSimilarity()
landmarkTransform.Update()
```

### 误差计算
RMS (均方根误差):
```
RMS = sqrt(mean((p_transformed - p_target)²))
```

## 应用场景

### 1. 预配准
为基于互信息的精配准提供良好的初始位置，避免:
- 局部最优解
- 配准失败
- 过长的计算时间

### 2. 快速对齐
当需要快速对齐图像用于:
- 可视化比较
- 初步分析
- 验证数据质量

### 3. 基准点配准
当已知对应点的位置时:
- 手术规划
- 植入物定位
- 解剖标志对齐

## 常见问题

### Q: 为什么需要粗配准？
A: 粗配准提供良好的初始对齐，避免后续基于互信息的精配准因初始位置差异过大而失败或陷入局部最优。

### Q: 基准点需要多少个？
A: 至少 3 个 (计算相似变换的数学要求)，建议 5-10 个以提高精度和稳定性。Fixed 和 Moving 的点数必须相同。更多的点可以提高鲁棒性，但也可能引入噪声。

### Q: RMS 误差多少算合格？
A: 一般情况下:
- < 2 mm: 优秀，可直接用于后续处理
- 2-5 mm: 良好，满足粗配准要求
- > 5 mm: 需要检查基准点选择是否准确

具体标准取决于图像分辨率和应用场景。

### Q: 如果 RMS 误差很大怎么办？
A: 可能的原因和解决方法:
1. **基准点对应错误**: 检查 Fixed 和 Moving 上的点是否真正对应，顺序是否一致
2. **点数太少**: 增加基准点数量
3. **点分布不均**: 确保点在感兴趣区域均匀分布
4. **标注不准确**: 重新标注，确保点在两个图像上都准确定位到解剖标志点
5. **解剖变化**: 如果两个图像间存在显著的解剖变化，相似变换可能不够精确

### Q: 粗配准后还需要精配准吗？
A: 是的。粗配准只提供初始对齐，精配准 (如基于互信息的方法) 可以进一步优化配准精度，达到亚体素级别的精度。

### Q: 可以跳过粗配准直接精配准吗？
A: 如果初始位置已经比较接近 (如同一患者不同时间的扫描)，可以直接精配准。但对于差异较大的图像，粗配准可以显著提高精配准的成功率和效率。

## 文件结构

```
CoarseRegistration/
├── __init__.py                      # 模块初始化
├── coarse_registration_widget.py   # UI 组件
├── coarse_registration_logic.py    # 业务逻辑
└── README.md                        # 本文档
```

## 依赖

- **3D Slicer**: >= 5.0
- **VTK**: (Slicer 内置)
- **NumPy**: (Slicer 内置)

## 下一步

粗配准完成后，可以:
1. 使用 Volume Rendering 可视化配准效果
2. 保存场景供后续使用
3. 进行精配准 (计划中的模块)
4. 评估配准精度 (对比金标准)

## 参考

- [VTK vtkLandmarkTransform Documentation](https://vtk.org/doc/nightly/html/classvtkLandmarkTransform.html)
- [3D Slicer Documentation](https://slicer.readthedocs.io/)
- [Point-Based Registration Methods](https://en.wikipedia.org/wiki/Point_set_registration)

---

**作者**: Feng  
**创建日期**: 2025-01-29  
**版本**: 1.0
