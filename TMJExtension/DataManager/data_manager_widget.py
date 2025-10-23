"""
Data Manager Widget - 数据管理模块的UI界面
"""
import qt
import ctk
import slicer
from datetime import datetime
from .data_manager_logic import DataManagerLogic


class DataManagerWidget:
    """
    Data Manager 的UI组件类
    负责数据导入、管理和显示
    """

    def __init__(self, parent, logCallback):
        """
        初始化 Data Manager Widget
        
        :param parent: 父布局
        :param logCallback: 日志回调函数
        """
        self.parent = parent
        self.logCallback = logCallback
        self.logic = DataManagerLogic(logCallback=logCallback)
        
        # UI 组件引用
        self.fixedVolumeSelector = None
        self.movingVolumeSelector = None
        self.mainFolderNameEdit = None
        self.moduleFolderNameEdit = None
        self.loadDataButton = None
        self.statusLabel = None
        
        self.setupUI()

    def setupUI(self):
        """设置 Data Manager 的UI界面"""
        # Data Manager 区域
        dataManagerCollapsibleButton = ctk.ctkCollapsibleButton()
        dataManagerCollapsibleButton.text = "Data Manager"
        self.parent.addWidget(dataManagerCollapsibleButton)
        dataManagerFormLayout = qt.QFormLayout(dataManagerCollapsibleButton)

        # 从已加载数据中选择
        importLabel0 = qt.QLabel("从已加载数据中选择:")
        importLabel0.setStyleSheet("font-weight: bold;")
        dataManagerFormLayout.addRow(importLabel0)
        
        # Fixed Volume 选择器 (通常是 CT)
        fixedVolumeLayout = qt.QVBoxLayout()
        self.fixedVolumeSelector = slicer.qMRMLNodeComboBox()
        self.fixedVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.fixedVolumeSelector.selectNodeUponCreation = True
        self.fixedVolumeSelector.addEnabled = False
        self.fixedVolumeSelector.removeEnabled = False
        self.fixedVolumeSelector.noneEnabled = True
        self.fixedVolumeSelector.showHidden = False
        self.fixedVolumeSelector.showChildNodeTypes = False
        self.fixedVolumeSelector.setMRMLScene(slicer.mrmlScene)
        self.fixedVolumeSelector.setToolTip("选择固定图像 (CBCT)")
        fixedVolumeLayout.addWidget(self.fixedVolumeSelector)
        dataManagerFormLayout.addRow("Fixed Volume(CBCT): ", fixedVolumeLayout)

        # Moving Volume 选择器 (通常是 MR)
        movingVolumeLayout = qt.QVBoxLayout()
        self.movingVolumeSelector = slicer.qMRMLNodeComboBox()
        self.movingVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.movingVolumeSelector.selectNodeUponCreation = True
        self.movingVolumeSelector.addEnabled = False
        self.movingVolumeSelector.removeEnabled = False
        self.movingVolumeSelector.noneEnabled = True
        self.movingVolumeSelector.showHidden = False
        self.movingVolumeSelector.showChildNodeTypes = False
        self.movingVolumeSelector.setMRMLScene(slicer.mrmlScene)
        self.movingVolumeSelector.setToolTip("选择浮动图像 (MRI)")
        movingVolumeLayout.addWidget(self.movingVolumeSelector)
        dataManagerFormLayout.addRow("Moving Volume(MRI): ", movingVolumeLayout)

        # 或者导入新文件
        importLabel = qt.QLabel("或者从文件夹导入新的DICOM文件:")
        importLabel.setStyleSheet("font-weight: bold; margin-top: 2px;")
        dataManagerFormLayout.addRow(importLabel)

        importButtonsLayout = qt.QHBoxLayout()
        self.loadFixedButton = qt.QPushButton("加载 Fixed Volume")
        self.loadFixedButton.toolTip = "从文件导入 Fixed Volume"
        self.loadFixedButton.connect('clicked(bool)', self.onLoadFixedVolume)
        importButtonsLayout.addWidget(self.loadFixedButton)

        self.loadMovingButton = qt.QPushButton("加载 Moving Volume")
        self.loadMovingButton.toolTip = "从文件导入 Moving Volume"
        self.loadMovingButton.connect('clicked(bool)', self.onLoadMovingVolume)
        importButtonsLayout.addWidget(self.loadMovingButton)
        dataManagerFormLayout.addRow(importButtonsLayout)

        # 配准流程总文件夹名称
        folderLabel = qt.QLabel("场景文件夹设置:")
        folderLabel.setStyleSheet("font-weight: bold; margin-top: 2px;")
        dataManagerFormLayout.addRow(folderLabel)
        
        self.mainFolderNameEdit = qt.QLineEdit()
        self.mainFolderNameEdit.text = "TMJ_配准"
        self.mainFolderNameEdit.setToolTip("配准流程的总文件夹名称,所有模块的结果都将保存在此文件夹下")
        dataManagerFormLayout.addRow("场景总文件夹: ", self.mainFolderNameEdit)

        # 模块子文件夹名称
        self.moduleFolderNameEdit = qt.QLineEdit()
        self.moduleFolderNameEdit.text = "Data Manager"
        self.moduleFolderNameEdit.setToolTip("Data Manager在总场景文件夹下的子文件夹名称")
        dataManagerFormLayout.addRow("Data Manager场景子文件夹: ", self.moduleFolderNameEdit)

        # 加载到场景按钮
        self.loadDataButton = qt.QPushButton("加载配准数据")
        self.loadDataButton.toolTip = "将选择的 Fixed 和 Moving Volume 组织到配准流程文件夹中"
        self.loadDataButton.enabled = True
        self.loadDataButton.connect('clicked(bool)', self.onLoadData)
        dataManagerFormLayout.addRow(self.loadDataButton)

        # 状态信息
        self.statusLabel = qt.QLabel("状态: 等待选择数据")
        self.statusLabel.setStyleSheet("color: gray;")
        dataManagerFormLayout.addRow(self.statusLabel)

        # 添加模块末尾分隔线（黑色粗线）
        separator1 = qt.QFrame()
        separator1.setFrameShape(qt.QFrame.HLine)
        separator1.setFrameShadow(qt.QFrame.Plain)
        separator1.setLineWidth(2)
        separator1.setMidLineWidth(0)
        separator1.setStyleSheet("QFrame { background-color: #000000; max-height: 2px; margin: 15px 0px; }")
        dataManagerFormLayout.addRow(separator1)

        # 连接信号以更新按钮状态
        self.fixedVolumeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateButtonStates)
        self.movingVolumeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateButtonStates)

    def onLoadFixedVolume(self):
        """加载 Fixed Volume"""
        try:
            filePath = qt.QFileDialog.getOpenFileName(
                None, 
                "选择 Fixed Volume", 
                "", 
                "Medical Images (*.nrrd *.nii *.nii.gz *.dcm *.mha *.mhd);;All Files (*)"
            )
            if filePath:
                self.logCallback(f"正在加载 Fixed Volume: {filePath}")
                volumeNode = self.logic.loadVolume(filePath, "fixed_volume")
                if volumeNode:
                    self.fixedVolumeSelector.setCurrentNode(volumeNode)
                    self.logCallback(f"✓ Fixed Volume 加载成功: {volumeNode.GetName()}")
                    self.statusLabel.text = "状态: Fixed Volume 已加载"
                    self.statusLabel.setStyleSheet("color: green;")
        except Exception as e:
            self.showError(f"加载 Fixed Volume 失败: {str(e)}")

    def onLoadMovingVolume(self):
        """加载 Moving Volume"""
        try:
            filePath = qt.QFileDialog.getOpenFileName(
                None, 
                "选择 Moving Volume", 
                "", 
                "Medical Images (*.nrrd *.nii *.nii.gz *.dcm *.mha *.mhd);;All Files (*)"
            )
            if filePath:
                self.logCallback(f"正在加载 Moving Volume: {filePath}")
                volumeNode = self.logic.loadVolume(filePath, "moving_volume")
                if volumeNode:
                    self.movingVolumeSelector.setCurrentNode(volumeNode)
                    self.logCallback(f"✓ Moving Volume 加载成功: {volumeNode.GetName()}")
                    self.statusLabel.text = "状态: Moving Volume 已加载"
                    self.statusLabel.setStyleSheet("color: green;")
        except Exception as e:
            self.showError(f"加载 Moving Volume 失败: {str(e)}")

    def onLoadData(self):
        """加载配准数据到场景文件夹"""
        try:
            # 检查是否选择了体积
            fixedNode = self.fixedVolumeSelector.currentNode()
            movingNode = self.movingVolumeSelector.currentNode()
            
            if not fixedNode or not movingNode:
                self.showError("请选择 Fixed Volume 和 Moving Volume")
                return
            
            # 获取文件夹名称
            mainFolderName = self.mainFolderNameEdit.text
            moduleFolderName = self.moduleFolderNameEdit.text
            
            if not mainFolderName:
                self.showError("请输入配准流程总文件夹名称")
                return
            
            if not moduleFolderName:
                self.showError("请输入模块子文件夹名称")
                return
            
            self.logCallback(f"正在创建配准流程结构...")
            self.logCallback(f"  总文件夹: {mainFolderName}")
            self.logCallback(f"  Data Manager子文件夹: {moduleFolderName}")
            
            # 调用 Logic 加载数据到场景
            success = self.logic.loadDataToScene(fixedNode, movingNode, mainFolderName, moduleFolderName)
            
            if success:
                self.logCallback(f"✓ 配准数据已组织到场景文件夹")
                self.logCallback(f"  路径: {mainFolderName}/{moduleFolderName}")
                self.statusLabel.text = "状态: 配准数据已加载"
                self.statusLabel.setStyleSheet("color: green;")
            else:
                self.showError("加载配准数据失败")
                
        except Exception as e:
            self.showError(f"加载配准数据失败: {str(e)}")

    def updateButtonStates(self):
        """更新按钮状态"""
        hasFixed = self.fixedVolumeSelector.currentNode() is not None
        hasMoving = self.movingVolumeSelector.currentNode() is not None

        self.loadDataButton.enabled = hasFixed and hasMoving

        if hasFixed and hasMoving:
            self.statusLabel.text = "状态: 准备就绪,可以加载"
            self.statusLabel.setStyleSheet("color: green;")
        elif hasFixed or hasMoving:
            self.statusLabel.text = "状态: 已选择部分数据"
            self.statusLabel.setStyleSheet("color: orange;")

    def showError(self, errorMessage):
        """显示错误信息"""
        self.logCallback(f"✗ 错误: {errorMessage}")
        self.statusLabel.text = f"状态: 错误"
        self.statusLabel.setStyleSheet("color: red;")
        slicer.util.errorDisplay(errorMessage)
        import traceback
        self.logCallback(traceback.format_exc())

    def getMainFolderName(self):
        """获取主文件夹名称,供其他模块使用"""
        return self.mainFolderNameEdit.text
