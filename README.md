# TMJ Extension - Data Manager

这是一个用于3D Slicer的TMJ(颞下颌关节)分析扩展插件,第一个模块是 **Data Manager(数据管理器)**。

## 功能特性

### Data Manager 模块

Data Manager 提供简单的配准数据组织功能:

- ✅ **选择已加载的体积**: 从 Slicer 场景中选择 Fixed/Moving Volume
- ✅ **导入新文件**: 支持 NRRD, NIfTI, DICOM, MHA 等格式
- ✅ **场景文件夹管理**: 在场景层次结构中创建文件夹来组织配准数据
- ✅ **保留原始数据**: 不进行重采样,保留原始 spacing/direction/origin
- ✅ **保留原始强度**: CT 数据保留 HU 值,MR 数据保留原始强度
- ✅ **CT/MR 提示**: 提供选择提示,无强制验证
- ✅ **错误处理与日志**: 详细的日志记录和错误提示

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

### 1. 加载数据

**选项 A: 选择已加载的体积**
- 从 "Fixed Volume" 下拉菜单选择参考图像
- 从 "Moving Volume" 下拉菜单选择待配准图像

**选项 B: 导入新文件**
- 点击 "加载 Fixed Volume" 按钮导入参考图像
- 点击 "加载 Moving Volume" 按钮导入待配准图像

### 2. 配置输出

- **场景文件夹名称**: 在 3D Slicer 场景层次结构中创建的文件夹名称,用于组织管理体积节点
- **输出文件夹名称**: 默认自动生成带时间戳的名称,也可自定义
- **输出目录**: 选择要保存数据的磁盘目录
- **导出格式**: 选择 NRRD 或 NIfTI (.nii.gz)

### 3. 导出数据

- 点击 "导出数据" 按钮
- 系统会:
  - **在场景中**: 创建一个文件夹节点,并将体积副本放入其中进行管理
  - **在磁盘上**: 在指定目录创建文件夹并保存:
    - `fixed_volume.nrrd` (或 .nii.gz) - Fixed Volume
    - `moving_volume.nrrd` (或 .nii.gz) - Moving Volume
    - `metadata.json` - 完整的元数据信息

### 4. 查看日志

- 展开 "日志与错误信息" 区域
- 查看详细的操作日志和错误信息
- 点击 "清除日志" 清空日志内容

## 输出文件说明

### 体积文件

保留原始的医学影像数据:
- **CT 数据**: 保留 HU (Hounsfield Unit) 值
- **MR 数据**: 保留原始强度值
- **空间信息**: 保留原始 spacing, origin, direction

### metadata.json 示例

```json
{
  "export_time": "2025-10-21 14:30:00",
  "file_format": "nrrd",
  "resampled": false,
  "scene_folder": "TMJ_Registration_20251021_143000",
  "volumes": {
    "fixed": {
      "name": "fixed_volume",
      "data_type": "CT",
      "dimensions": [512, 512, 200],
      "spacing": [0.5, 0.5, 1.0],
      "origin": [0.0, 0.0, 0.0],
      "direction": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
      "scalar_type": "short",
      "number_of_components": 1,
      "intensity_statistics": {
        "min": -1024.0,
        "max": 3071.0,
        "mean": -150.5,
        "std": 450.2,
        "median": -200.0
      },
      "resampled": false,
      "notes": "Original HU values preserved"
    },
    "moving": { ... }
  }
}
```

## 项目结构

```
TMJ_Extension/
├── CMakeLists.txt                      # 主CMake配置文件
├── TMJExtension.s4ext                  # Slicer扩展描述文件
├── README.md                           # 本文件
├── .gitignore                          # Git忽略文件配置
└── TMJExtension/                       # 模块文件夹
    ├── CMakeLists.txt                  # 模块CMake配置
    ├── TMJExtension.py                 # 主Python脚本(核心代码)
    └── Resources/
        ├── Icons/
        │   └── TMJExtension.png        # 模块图标
        └── UI/
            └── TMJExtension.ui         # Qt用户界面文件
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

- [ ] 配准模块
- [ ] 分割模块
- [ ] 测量与分析模块
- [ ] 可视化工具

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
