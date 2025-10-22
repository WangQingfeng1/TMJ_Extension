# 两层文件夹结构设计说明

## 📐 设计目标

为 TMJ 配准流程建立一个可扩展的、有组织的场景文件夹结构,方便管理多个模块的输出结果。

## 🏗️ 文件夹结构

### 两层设计

```
📁 TMJ_配准流程_20250122_143000  ← 配准流程总文件夹
   │
   ├─ 📁 模块1_数据管理  ← 模块1的子文件夹
   │   ├─ 📄 Fixed_Volume
   │   └─ 📄 Moving_Volume
   │
   ├─ 📁 模块2_配准结果  ← 模块2的子文件夹(将来添加)
   │   ├─ 📄 配准后的图像
   │   └─ 📄 变换矩阵
   │
   ├─ 📁 模块3_分割结果  ← 模块3的子文件夹(将来添加)
   │   ├─ 📄 TMJ分割模型
   │   └─ 📄 ROI标注
   │
   └─ 📁 模块4_测量数据  ← 模块4的子文件夹(将来添加)
       ├─ 📄 距离测量
       └─ 📄 角度测量
```

## 💡 设计优势

### 1. 层次清晰
- **第一层(总文件夹)**: 代表整个配准流程
- **第二层(模块文件夹)**: 每个模块的输出独立存放

### 2. 易于管理
- 所有相关数据都在一个总文件夹下
- 可以清楚地看到整个流程包含哪些步骤
- 每个模块的结果互不干扰

### 3. 可扩展性强
- 添加新模块时,只需在总文件夹下创建新的子文件夹
- 不影响已有模块的数据结构
- 方便后续功能扩展

### 4. 智能复用
- 如果总文件夹已存在,直接使用(避免重复)
- 不同时间点的操作可以累积在同一流程下
- 便于多次实验和对比

## 🔧 实现细节

### UI 界面

```python
# 配准流程文件夹设置:
总文件夹名称:  [TMJ_配准流程_20250122_143000]
模块1子文件夹:  [模块1_数据管理]
[加载配准数据]
```

### 核心逻辑

```python
def loadDataToScene(fixedVolume, movingVolume, mainFolderName, moduleFolderName):
    # 1. 检查总文件夹是否存在
    if 总文件夹已存在:
        使用已存在的文件夹
    else:
        创建新的总文件夹
    
    # 2. 在总文件夹下创建模块子文件夹
    创建模块子文件夹
    
    # 3. 将数据放入模块子文件夹
    复制 Fixed Volume 到子文件夹
    复制 Moving Volume 到子文件夹
```

### 关键代码

```python
# 检查总文件夹是否已存在
mainFolderItemID = shNode.GetItemChildWithName(sceneItemID, mainFolderName)

if mainFolderItemID == 0:  # 不存在
    mainFolderItemID = shNode.CreateFolderItem(sceneItemID, mainFolderName)
else:  # 已存在
    # 直接使用,不重复创建

# 在总文件夹下创建模块子文件夹
moduleFolderItemID = shNode.CreateFolderItem(mainFolderItemID, moduleFolderName)
```

## 📊 使用场景

### 场景1: 首次使用
```
用户操作 → 创建总文件夹 → 创建模块1子文件夹 → 放入数据
结果: TMJ_配准流程_xxx/模块1_数据管理/
```

### 场景2: 添加配准模块
```
使用已有总文件夹 → 创建模块2子文件夹 → 放入配准结果
结果: TMJ_配准流程_xxx/模块2_配准结果/
```

### 场景3: 完整流程
```
总文件夹: TMJ_配准流程_20250122_143000
├─ 模块1_数据管理/
│   ├─ Fixed_Volume
│   └─ Moving_Volume
├─ 模块2_配准结果/
│   ├─ 配准后的图像
│   └─ 变换矩阵
├─ 模块3_分割结果/
│   └─ TMJ分割模型
└─ 模块4_测量数据/
    └─ 测量结果
```

## ✨ 用户体验

### 优点
1. ✅ **一目了然**: 所有数据都在一个总文件夹下
2. ✅ **易于追溯**: 可以清楚看到整个流程的步骤
3. ✅ **便于保存**: 保存场景时,所有数据都在一起
4. ✅ **支持多次实验**: 可以创建多个总文件夹对比不同配准流程

### 灵活性
1. ✅ 可以自定义总文件夹名称(如添加患者ID)
2. ✅ 可以自定义模块子文件夹名称
3. ✅ 支持在已有总文件夹中添加新模块结果

## 🔮 未来扩展

### 模块2: 配准模块
```python
# 读取模块1的数据
mainFolder = "TMJ_配准流程_xxx"
module1Data = getDataFrom(mainFolder + "/模块1_数据管理")

# 执行配准
registrationResult = doRegistration(module1Data)

# 保存到新的子文件夹
saveToFolder(mainFolder + "/模块2_配准结果")
```

### 模块3: 分割模块
```python
# 读取配准后的数据
registeredImage = getDataFrom(mainFolder + "/模块2_配准结果")

# 执行分割
segmentationResult = doSegmentation(registeredImage)

# 保存到新的子文件夹
saveToFolder(mainFolder + "/模块3_分割结果")
```

## 📝 总结

两层文件夹结构为 TMJ Extension 提供了:
- ✅ 清晰的数据组织
- ✅ 良好的可扩展性
- ✅ 便捷的数据管理
- ✅ 完整的流程追溯

这个设计将支持整个 TMJ 分析平台的长期发展! 🚀
