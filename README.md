# TMJ Extension

这是一个用于3D Slicer的TMJ(颞下颌关节)分析扩展插件，包含多个模块用于医学影像配准和分析。

## 功能特性

### 1. Data Manager 模块

Data Manager 提供简单的配准数据组织功能:

- ✅ **选择已加载的体积**: 从 Slicer 场景中选择 Fixed/Moving Volume
- ✅ **导入新文件**: 支持 NRRD, NIfTI, DICOM, MHA 等格式
- ✅ **场景文件夹管理**: 在场景层次结构中创建文件夹来组织配准数据
- ✅ **保留原始数据**: 不进行重采样,保留原始 spacing/direction/origin
- ✅ **保留原始强度**: CT 数据保留 HU 值,MR 数据保留原始强度

### 2. Gold Standard Set 模块

手动配准和金标准设置:

- ✅ **手动配准**: 使用相似变换进行交互式手动配准
- ✅ **标注点管理**: 在配准后的图像上标注对应点对
- ✅ **金标准保存**: 保存手动配准结果作为金标准参考

### 3. Coarse Registration 模块

基于基准点的粗配准:

- ✅ **基准点选择**: 在 Fixed 和 Moving Volume 上选择对应的基准点
- ✅ **自动配准**: 基于基准点对自动计算相似变换
- ✅ **配准评估**: 提供配准精度评估
- ✅ **初始对齐**: 为后续精配准提供良好的初始位置

### 4. ROI Mask Set 模块

生成颞下颌关节ROI区域的掩膜:

- ✅ **自动生成掩膜**: 根据高分辨率ROI浮动图像的物理范围自动生成固定图像的ROI掩膜
- ✅ **膨胀处理**: 对掩膜进行可调膨胀，防止范围过于严格
- ✅ **精细配准准备**: 为后续基于ROI的精细配准提供掩膜约束
- ✅ **支持局部高分辨率**: 适用于整体图像分辨率较低但局部ROI有高分辨率扫描的场景

## 重要说明

**关于 VS Code 中的错误提示:**

在 VS Code 中打开本项目时,您会看到许多 Python 导入错误:
- `无法解析导入"slicer"`
- `无法解析导入"qt"`, `"ctk"`, `"vtk"`
- `未定义"ScriptedLoadableModule"`

**这些是正常的!** 因为:
1. 这些模块只在 3D Slicer 运行时环境中可用
2. VS Code 无法识别 Slicer 的特殊 Python 环境
3. 代码在 Slicer 中运行时完全正常

## 安装

### 方法 1: 直接使用(开发模式 - 推荐)

1. 打开 3D Slicer
2. 进入 `Edit` → `Application Settings` → `Modules`
3. 点击 `Additional module paths` 右侧的 `>>` 按钮
4. 点击 `Add` 添加路径: `E:\图像处理\TMJ_Extension\TMJExtension`
5. 点击 `OK` 保存设置
6. 重启 3D Slicer
7. 在模块菜单中找到 `TMJ Analysis` → `TMJ Extension - Data Manager`

### 方法 2: 从源代码构建

```bash
# 需要配置 CMake 和 Slicer 开发环境
cd E:\图像处理\TMJ_Extension
mkdir build
cd build
cmake -DSlicer_DIR:PATH=/path/to/Slicer-build ..
cmake --build .
```

## 使用方法

详细的使用说明请查看 [USAGE_GUIDE.md](USAGE_GUIDE.md)

### 工作流程建议

1. **Data Manager**: 加载和组织配准数据
2. **Coarse Registration**: 使用基准点进行粗配准（推荐先做）
3. **ROI Mask Set**: 切换到高分辨率局部MRI，生成ROI掩膜
4. **Gold Standard Set**: 手动精细配准设置金标准（用于评估）
5. **（后续模块）**: 基于互信息的自动精配准（在ROI掩膜约束下）
6. **（后续模块）**: 配准精度评估和可视化

## 项目结构

```
TMJ_Extension/
├── CMakeLists.txt                      # 主CMake配置文件
├── TMJExtension.s4ext                  # Slicer扩展描述文件
├── README.md                           # 本文件
├── USAGE_GUIDE.md                      # 详细使用指南
├── .gitignore                          # Git忽略文件配置
└── TMJExtension/                       # 模块文件夹
    ├── CMakeLists.txt                  # 模块CMake配置
    ├── TMJExtension.py                 # 主Python脚本（模块集成）
    ├── DataManager/                    # Data Manager 模块
    │   ├── __init__.py
    │   ├── data_manager_logic.py
    │   └── data_manager_widget.py
    ├── GoldStandardSet/                # Gold Standard Set 模块
    │   ├── __init__.py
    │   ├── gold_standard_logic.py
    │   └── gold_standard_widget.py
    ├── CoarseRegistration/             # Coarse Registration 模块
    │   ├── __init__.py
    │   ├── coarse_registration_logic.py
    │   └── coarse_registration_widget.py
    ├── ROIMaskSet/                     # ROI Mask Set 模块
    │   ├── __init__.py
    │   ├── roi_mask_set_logic.py
    │   └── roi_mask_set_widget.py
    └── Resources/
        └── Icons/
            └── TMJExtension.png        # 模块图标
```

## 技术细节

### 数据加载
- 使用 `slicer.util.loadVolume()` 保证原始数据完整性
- 不进行任何重采样或插值操作
- 保留原始文件的所有 header 信息

### 数据导出
- 使用 `slicer.util.saveNode()` 确保数据一致性
- NRRD 格式保留完整的医学影像元数据
- NIfTI 格式使用 gzip 压缩

### 元数据提取
- 自动提取 Origin, Spacing, Direction 矩阵
- 计算强度统计 (min, max, mean, std, median)
- 自动检测 CT/MR 数据类型

## 下一步开发计划

- [ ] 基于互信息的精细配准模块（支持ROI掩膜约束）
- [ ] 配准精度评估模块
- [ ] 分割模块
- [ ] 测量与分析模块
- [ ] 高级可视化工具

## 故障排除

### 问题: 模块未显示
- 确认路径正确添加到 Additional module paths
- 重启 3D Slicer
- 检查 Python 控制台是否有错误信息

### 问题: 加载文件失败
- 确认文件格式支持 (NRRD, NIfTI, DICOM, MHA, MHD)
- 检查文件是否损坏
- 查看日志区域的详细错误信息

### 问题: 导出失败
- 确认输出目录有写入权限
- 确认文件夹名称不包含特殊字符
- 查看日志区域的详细错误信息

## 许可证

请根据你的需求添加相应的许可证信息。

## 联系方式

- 作者: Your Name
- 组织: Your Organization
- 项目: TMJ Analysis Platform
