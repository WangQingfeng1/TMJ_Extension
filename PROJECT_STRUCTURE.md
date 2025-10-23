# TMJ Extension 项目结构可视化

## 📁 完整文件树

```
TMJ_Extension/                          (项目根目录)
│
├── 📄 CMakeLists.txt                   (构建配置)
├── 📄 TMJExtension.s4ext               (扩展描述文件)
├── 📄 README.md                        (项目说明)
├── 📄 MODULE_STRUCTURE.md              (模块结构文档) ⭐ 新增
├── 📄 MIGRATION_GUIDE.md               (迁移指南) ⭐ 新增
├── 📄 PROJECT_STRUCTURE.md             (本文件) ⭐ 新增
│
└── 📂 TMJExtension/                    (插件代码目录)
    ├── 📄 CMakeLists.txt
    ├── 📄 TMJExtension.py              (原始单文件 ~1500行) 💾 备份
    ├── 📄 TMJExtension_Modular.py      (模块化主入口 ~150行) ⭐ 新增
    │
    ├── 📂 DataManager/                  ⭐ 新增模块
    │   ├── 📄 __init__.py              (模块初始化)
    │   ├── 📄 data_manager_widget.py   (UI界面 ~210行)
    │   └── 📄 data_manager_logic.py    (业务逻辑 ~360行)
    │
    ├── 📂 GoldStandardSet/              ⭐ 新增模块
    │   ├── 📄 __init__.py              (模块初始化)
    │   ├── 📄 gold_standard_widget.py  (UI界面 ~580行)
    │   └── 📄 gold_standard_logic.py   (业务逻辑 ~230行)
    │
    ├── 📂 Resources/
    │   └── 📂 Icons/
    │       └── 🖼️ TMJExtension.png
    │
    └── 📂 __pycache__/                 (Python缓存)
        └── TMJExtension.cpython-39.pyc
```

## 🎯 模块职责划分

### 1️⃣ Data Manager 模块

```
📦 DataManager/
│
├── 📄 data_manager_widget.py (UI层)
│   ├── 🎨 体积选择器 (Fixed/Moving)
│   ├── 📂 文件导入按钮
│   ├── 📝 场景文件夹配置
│   ├── ✅ 状态显示
│   └── 🔗 连接到 Logic 层
│
└── 📄 data_manager_logic.py (逻辑层)
    ├── 📥 loadVolume() - 加载医学影像
    ├── 📤 loadDataToScene() - 组织场景结构
    ├── 💾 exportData() - 导出数据
    ├── 🔍 _extractVolumeMetadata() - 提取元数据
    └── 🏗️ _createVolumeInFolder() - 创建体积副本
```

### 2️⃣ Gold Standard Set 模块

```
📦 GoldStandardSet/
│
├── 📄 gold_standard_widget.py (UI层)
│   ├── 🎨 体积选择器
│   ├── 🔄 变换控制 (平移/旋转/缩放)
│   ├── 📍 标注点管理
│   ├── 💾 保存金标准按钮
│   ├── 📊 点对显示表格
│   └── 🔗 连接到 Logic 层
│
└── 📄 gold_standard_logic.py (逻辑层)
    ├── 💾 saveGoldStandardToScene() - 保存金标准
    ├── 🏗️ _createVolumeInFolder() - 创建体积副本
    ├── 📍 _copyFiducials() - 复制标注点
    ├── 🔄 _copyFiducialsWithTransform() - 应用变换
    ├── 🎨 _copyDisplayProperties() - 复制显示属性
    └── 🧹 _cleanupTemporaryNodes() - 清理临时节点
```

### 3️⃣ 主入口模块

```
📄 TMJExtension_Modular.py (主入口)
│
├── 📦 TMJExtension (类)
│   └── 模块元信息和配置
│
├── 🎨 TMJExtensionWidget (主界面)
│   ├── 创建 DataManagerWidget
│   ├── 创建 GoldStandardWidget
│   └── 统一日志管理
│
└── 🧠 TMJExtensionLogic (主逻辑)
    ├── 持有 DataManagerLogic
    └── 持有 GoldStandardLogic
```

## 🔄 数据流向图

```
用户操作
   │
   ▼
┌─────────────────────────────────────┐
│   TMJExtensionWidget (主界面)       │
│   ├── 日志系统                       │
│   └── 模块组合                       │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌─────────────┐  ┌──────────────────┐
│ DataManager │  │ GoldStandardSet  │
│   Widget    │  │     Widget       │
└──────┬──────┘  └────────┬─────────┘
       │                  │
       ▼                  ▼
┌─────────────┐  ┌──────────────────┐
│ DataManager │  │ GoldStandardSet  │
│   Logic     │  │     Logic        │
└──────┬──────┘  └────────┬─────────┘
       │                  │
       └──────────┬────────┘
                  │
                  ▼
         ┌────────────────┐
         │  Slicer Scene  │
         │  ├── Volumes   │
         │  ├── Transforms│
         │  └── Fiducials │
         └────────────────┘
```

## 📊 代码行数对比

### 原始版本 (单文件)
```
TMJExtension.py:  ~1500行 ❌ 难以维护
```

### 模块化版本 (6个文件)
```
TMJExtension_Modular.py:           ~150行  ✅ 精简
DataManager/data_manager_widget.py: ~210行  ✅ 清晰
DataManager/data_manager_logic.py:  ~360行  ✅ 独立
GoldStandardSet/gold_standard_widget.py: ~580行 ✅ 完整
GoldStandardSet/gold_standard_logic.py:  ~230行 ✅ 专注
其他 __init__.py 文件:              ~20行   ✅ 简洁
─────────────────────────────────────────────
总计:                              ~1550行  ✅ 模块化
```

## 🎨 UI 布局结构

```
┌─────────────────────────────────────────────┐
│         TMJ Extension 主界面                 │
├─────────────────────────────────────────────┤
│                                             │
│  📦 Data Manager 模块                        │
│  ├── 从已加载数据中选择                       │
│  │   ├── Fixed Volume (CBCT)  [选择器]      │
│  │   └── Moving Volume (MRI)  [选择器]      │
│  ├── 或者从文件夹导入                        │
│  │   ├── [加载 Fixed Volume]  按钮          │
│  │   └── [加载 Moving Volume] 按钮          │
│  ├── 场景文件夹设置                          │
│  │   ├── 场景总文件夹: [TMJ_配准]           │
│  │   └── Data Manager子文件夹: [Data Manager]│
│  ├── [加载配准数据] 按钮                     │
│  └── 状态: 等待选择数据                      │
│                                             │
│  ─────────────────────────────────────────  │
│                                             │
│  📦 Gold Standard Set 模块                   │
│  ├── 选择需要配准的数据                       │
│  │   ├── Fixed Volume (CBCT)  [选择器]      │
│  │   └── Moving Volume (MRI)  [选择器]      │
│  ├── 手动配准                               │
│  │   ├── 变换节点: [选择器]                  │
│  │   ├── [应用变换到浮动图像] 按钮           │
│  │   └── [打开 Transforms 模块] 按钮        │
│  ├── 快捷变换控制                           │
│  │   ├── 平移 (X/Y/Z) [滑块]                │
│  │   ├── 旋转 (X/Y/Z) [滑块]                │
│  │   ├── 统一缩放    [滑块]                 │
│  │   └── [重置变换] 按钮                     │
│  ├── 标注点对管理                           │
│  │   ├── Fixed 标注点:  [选择器]            │
│  │   ├── Moving 标注点: [选择器]            │
│  │   ├── [放置点对] [清除所有点] 按钮        │
│  │   └── 点对数量: [表格]                   │
│  ├── 保存金标准                             │
│  │   ├── Gold Standard子文件夹: [输入框]     │
│  │   ├── [保存金标准到场景] 按钮             │
│  │   └── 状态: 等待选择数据                  │
│                                             │
│  ─────────────────────────────────────────  │
│                                             │
│  📋 日志与错误信息 (可折叠)                   │
│  ├── [日志文本区域]                          │
│  └── [清除日志] 按钮                         │
│                                             │
└─────────────────────────────────────────────┘
```

## 🔑 关键概念

### 模块独立性
- ✅ 每个模块可独立开发和测试
- ✅ 修改一个模块不影响其他模块
- ✅ 清晰的接口定义

### 分层架构
```
UI层 (Widget) ──调用──> Logic层 ──操作──> Slicer Scene
     ↓                    ↓                  ↓
  用户交互            业务逻辑           数据存储
```

### 代码复用
- Widget 类负责界面
- Logic 类负责业务逻辑
- 相同功能的代码提取为私有方法

## 📝 下一步建议

1. **立即采用模块化版本** ✅
   - 更易维护
   - 更清晰的结构
   - 便于团队协作

2. **未来可扩展的模块**
   - AutoRegistration/ (自动配准模块)
   - Evaluation/ (结果评估模块)
   - Visualization/ (可视化模块)
   - Export/ (导出报告模块)

3. **持续优化**
   - 添加单元测试
   - 完善文档注释
   - 性能优化

---

**最后更新**: 2025-10-23
**版本**: 1.0 (模块化版本)
