import os
import unittest
import logging
import vtk, qt, ctk, slicer
import json
import numpy as np
from datetime import datetime
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

#
# TMJExtension
#

class TMJExtension(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "TMJ Extension"
        self.parent.categories = ["TMJ Analysis"]
        self.parent.dependencies = []
        self.parent.contributors = ["Feng"]
        self.parent.helpText = """
这是一个用于TMJ(颞下颌关节)分析的3D Slicer插件。
Data Manager 模块用于导入、管理和导出医学影像数据，保留原始 HU/强度信息。
"""
        self.parent.acknowledgementText = """
This module was developed for TMJ research.
"""

#
# TMJExtensionWidget
#

class TMJExtensionWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self.errorLogText = ""

    def setup(self):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Create logic class
        self.logic = TMJExtensionLogic()
        self.logic.logCallback = self.addLog

        #
        # Data Manager 区域
        #
        dataManagerCollapsibleButton = ctk.ctkCollapsibleButton()
        dataManagerCollapsibleButton.text = "Data Manager"
        self.layout.addWidget(dataManagerCollapsibleButton)
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
        separator1.setFrameShadow(qt.QFrame.Plain)  # Plain 样式，配合背景色实现纯黑
        separator1.setLineWidth(2)
        separator1.setMidLineWidth(0)
        separator1.setStyleSheet("QFrame { background-color: #000000; max-height: 2px; margin: 15px 0px; }")
        dataManagerFormLayout.addRow(separator1)

        #
        # Gold Standard Set 模块
        #
        goldStandardCollapsibleButton = ctk.ctkCollapsibleButton()
        goldStandardCollapsibleButton.text = "Gold Standard Set"
        goldStandardCollapsibleButton.collapsed = False
        self.layout.addWidget(goldStandardCollapsibleButton)
        goldStandardFormLayout = qt.QFormLayout(goldStandardCollapsibleButton)

        # 从场景中选择数据
        selectLabel = qt.QLabel("选择需要配准的数据，一般为Data Manage创建的Fixed_Volume和Moving_Volume:")
        selectLabel.setStyleSheet("font-weight: bold;")
        goldStandardFormLayout.addRow(selectLabel)

        # Fixed Volume 选择器
        self.gsFixedVolumeSelector = slicer.qMRMLNodeComboBox()
        self.gsFixedVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.gsFixedVolumeSelector.selectNodeUponCreation = False
        self.gsFixedVolumeSelector.addEnabled = False
        self.gsFixedVolumeSelector.removeEnabled = False
        self.gsFixedVolumeSelector.noneEnabled = True
        self.gsFixedVolumeSelector.showHidden = False
        self.gsFixedVolumeSelector.setMRMLScene(slicer.mrmlScene)
        self.gsFixedVolumeSelector.setToolTip("选择 Fixed Volume(CBCT)")
        goldStandardFormLayout.addRow("Fixed Volume(CBCT): ", self.gsFixedVolumeSelector)

        # Moving Volume 选择器
        self.gsMovingVolumeSelector = slicer.qMRMLNodeComboBox()
        self.gsMovingVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.gsMovingVolumeSelector.selectNodeUponCreation = False
        self.gsMovingVolumeSelector.addEnabled = False
        self.gsMovingVolumeSelector.removeEnabled = False
        self.gsMovingVolumeSelector.noneEnabled = True
        self.gsMovingVolumeSelector.showHidden = False
        self.gsMovingVolumeSelector.setMRMLScene(slicer.mrmlScene)
        self.gsMovingVolumeSelector.setToolTip("选择 Moving Volume (MRI)")
        goldStandardFormLayout.addRow("Moving Volume(MRI): ", self.gsMovingVolumeSelector)

        # 手动配准控制
        transformLabel = qt.QLabel("手动配准:")
        transformLabel.setStyleSheet("font-weight: bold; margin-top: 2px;")
        goldStandardFormLayout.addRow(transformLabel)

        # Transform 选择器
        self.transformSelector = slicer.qMRMLNodeComboBox()
        self.transformSelector.nodeTypes = ["vtkMRMLLinearTransformNode"]
        self.transformSelector.selectNodeUponCreation = True
        self.transformSelector.addEnabled = True
        self.transformSelector.removeEnabled = True
        self.transformSelector.noneEnabled = False
        self.transformSelector.showHidden = False
        self.transformSelector.setMRMLScene(slicer.mrmlScene)
        self.transformSelector.setToolTip("选择或创建用于手动配准的空间变换（相似变换）")
        self.transformSelector.baseName = "ManualSimilarityTransform"
        goldStandardFormLayout.addRow("变换节点: ", self.transformSelector)

        transformButtonsLayout = qt.QHBoxLayout()
        self.applyTransformButton = qt.QPushButton("应用变换到浮动图像")
        self.applyTransformButton.toolTip = "将变换应用到Moving Volume，可进行交互式调整"
        self.applyTransformButton.connect('clicked(bool)', self.onApplyTransform)
        transformButtonsLayout.addWidget(self.applyTransformButton)

        self.openTransformsButton = qt.QPushButton("打开 Transforms 模块")
        self.openTransformsButton.toolTip = "打开 Slicer 的 Transforms 模块进行详细调整"
        self.openTransformsButton.connect('clicked(bool)', self.onOpenTransforms)
        transformButtonsLayout.addWidget(self.openTransformsButton)
        goldStandardFormLayout.addRow(transformButtonsLayout)
        
        # 快捷变换控制（相似变换：平移 + 旋转 + 缩放）
        quickTransformLabel = qt.QLabel("快捷变换控制:")
        quickTransformLabel.setStyleSheet("font-style: oblique; color: gray; margin-top: 2px; font-size: 15px;")
        goldStandardFormLayout.addRow(quickTransformLabel)
        
        # 平移控制
        translationGroup = qt.QGroupBox("平移 (Translation)")
        translationLayout = qt.QFormLayout(translationGroup)
        
        self.translateXSlider = ctk.ctkSliderWidget()
        self.translateXSlider.minimum = -200
        self.translateXSlider.maximum = 200
        self.translateXSlider.value = 0
        self.translateXSlider.singleStep = 0.1
        self.translateXSlider.suffix = " mm"
        self.translateXSlider.connect('valueChanged(double)', lambda v: self.onTransformChanged())
        translationLayout.addRow("X:", self.translateXSlider)
        
        self.translateYSlider = ctk.ctkSliderWidget()
        self.translateYSlider.minimum = -200
        self.translateYSlider.maximum = 200
        self.translateYSlider.value = 0
        self.translateYSlider.singleStep = 0.1
        self.translateYSlider.suffix = " mm"
        self.translateYSlider.connect('valueChanged(double)', lambda v: self.onTransformChanged())
        translationLayout.addRow("Y:", self.translateYSlider)
        
        self.translateZSlider = ctk.ctkSliderWidget()
        self.translateZSlider.minimum = -200
        self.translateZSlider.maximum = 200
        self.translateZSlider.value = 0
        self.translateZSlider.singleStep = 0.1
        self.translateZSlider.suffix = " mm"
        self.translateZSlider.connect('valueChanged(double)', lambda v: self.onTransformChanged())
        translationLayout.addRow("Z:", self.translateZSlider)
        
        goldStandardFormLayout.addRow(translationGroup)
        
        # 旋转控制
        rotationGroup = qt.QGroupBox("旋转 (Rotation)")
        rotationLayout = qt.QFormLayout(rotationGroup)
        
        self.rotateXSlider = ctk.ctkSliderWidget()
        self.rotateXSlider.minimum = -180
        self.rotateXSlider.maximum = 180
        self.rotateXSlider.value = 0
        self.rotateXSlider.singleStep = 0.5
        self.rotateXSlider.suffix = " °"
        self.rotateXSlider.connect('valueChanged(double)', lambda v: self.onTransformChanged())
        rotationLayout.addRow("X:", self.rotateXSlider)
        
        self.rotateYSlider = ctk.ctkSliderWidget()
        self.rotateYSlider.minimum = -180
        self.rotateYSlider.maximum = 180
        self.rotateYSlider.value = 0
        self.rotateYSlider.singleStep = 0.5
        self.rotateYSlider.suffix = " °"
        self.rotateYSlider.connect('valueChanged(double)', lambda v: self.onTransformChanged())
        rotationLayout.addRow("Y:", self.rotateYSlider)
        
        self.rotateZSlider = ctk.ctkSliderWidget()
        self.rotateZSlider.minimum = -180
        self.rotateZSlider.maximum = 180
        self.rotateZSlider.value = 0
        self.rotateZSlider.singleStep = 0.5
        self.rotateZSlider.suffix = " °"
        self.rotateZSlider.connect('valueChanged(double)', lambda v: self.onTransformChanged())
        rotationLayout.addRow("Z:", self.rotateZSlider)
        
        goldStandardFormLayout.addRow(rotationGroup)
        
        # 缩放控制（相似变换 - 只有统一缩放）
        scaleGroup = qt.QGroupBox("缩放 (Scale)")
        scaleLayout = qt.QFormLayout(scaleGroup)
        
        self.uniformScaleSlider = ctk.ctkSliderWidget()
        self.uniformScaleSlider.minimum = 0.5
        self.uniformScaleSlider.maximum = 2.0
        self.uniformScaleSlider.value = 1.0
        self.uniformScaleSlider.singleStep = 0.01
        self.uniformScaleSlider.decimals = 3
        self.uniformScaleSlider.suffix = "x"
        self.uniformScaleSlider.setToolTip("统一缩放所有方向，保持形状比例不变")
        self.uniformScaleSlider.connect('valueChanged(double)', lambda v: self.onTransformChanged())
        scaleLayout.addRow("统一缩放:", self.uniformScaleSlider)
        
        goldStandardFormLayout.addRow(scaleGroup)
        
        # 变换控制按钮
        transformControlLayout = qt.QHBoxLayout()
        
        self.resetTransformButton = qt.QPushButton("重置变换")
        self.resetTransformButton.toolTip = "将所有变换参数重置为初始值"
        self.resetTransformButton.connect('clicked(bool)', self.onResetTransform)
        transformControlLayout.addWidget(self.resetTransformButton)
        
        goldStandardFormLayout.addRow(transformControlLayout)

        # Fiducials 点对管理
        fiducialsLabel = qt.QLabel("标注点对管理:")
        fiducialsLabel.setStyleSheet("font-weight: bold; margin-top: 2px;")
        goldStandardFormLayout.addRow(fiducialsLabel)

        # Fixed Fiducials
        self.fixedFiducialsSelector = slicer.qMRMLNodeComboBox()
        self.fixedFiducialsSelector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
        self.fixedFiducialsSelector.selectNodeUponCreation = True
        self.fixedFiducialsSelector.addEnabled = True
        self.fixedFiducialsSelector.removeEnabled = True
        self.fixedFiducialsSelector.noneEnabled = False
        self.fixedFiducialsSelector.showHidden = False
        self.fixedFiducialsSelector.setMRMLScene(slicer.mrmlScene)
        self.fixedFiducialsSelector.setToolTip("Fixed Volume 上的标注点")
        self.fixedFiducialsSelector.baseName = "Fixed_Fiducials"
        goldStandardFormLayout.addRow("Fixed 标注点: ", self.fixedFiducialsSelector)

        # Moving Fiducials
        self.movingFiducialsSelector = slicer.qMRMLNodeComboBox()
        self.movingFiducialsSelector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
        self.movingFiducialsSelector.selectNodeUponCreation = True
        self.movingFiducialsSelector.addEnabled = True
        self.movingFiducialsSelector.removeEnabled = True
        self.movingFiducialsSelector.noneEnabled = False
        self.movingFiducialsSelector.showHidden = False
        self.movingFiducialsSelector.setMRMLScene(slicer.mrmlScene)
        self.movingFiducialsSelector.setToolTip("Moving Volume 上的标注点")
        self.movingFiducialsSelector.baseName = "Moving_Fiducials"
        goldStandardFormLayout.addRow("Moving 标注点: ", self.movingFiducialsSelector)

        # 点对操作按钮
        fiducialButtonsLayout = qt.QHBoxLayout()
        
        self.placePairButton = qt.QPushButton("放置点对")
        self.placePairButton.toolTip = "在同一位置同时创建 Fixed 和 Moving 标注点对"
        self.placePairButton.checkable = True
        self.placePairButton.connect('toggled(bool)', self.onPlacePair)
        fiducialButtonsLayout.addWidget(self.placePairButton)

        self.clearPointsButton = qt.QPushButton("清除所有点")
        self.clearPointsButton.toolTip = "清除所有标注点"
        self.clearPointsButton.connect('clicked(bool)', self.onClearPoints)
        fiducialButtonsLayout.addWidget(self.clearPointsButton)

        goldStandardFormLayout.addRow(fiducialButtonsLayout)

        # 点对列表显示
        self.pointPairsTable = qt.QTableWidget()
        self.pointPairsTable.setColumnCount(2)
        self.pointPairsTable.setHorizontalHeaderLabels(["Fixed上点数", "Moving上点数"])
        self.pointPairsTable.setMaximumHeight(80)
        # 设置列宽自适应,让边框显示完整
        self.pointPairsTable.horizontalHeader().setStretchLastSection(True)
        self.pointPairsTable.setColumnWidth(0, 120)  # Fixed 点数列宽度
        goldStandardFormLayout.addRow("点对数量:", self.pointPairsTable)

        # 保存金标准
        saveLabel = qt.QLabel("保存金标准:")
        saveLabel.setStyleSheet("font-weight: bold; margin-top: 2px;")
        goldStandardFormLayout.addRow(saveLabel)

        # Gold Standard 子文件夹名称
        self.gsModuleFolderNameEdit = qt.QLineEdit()
        self.gsModuleFolderNameEdit.text = "Gold Standard Set"
        self.gsModuleFolderNameEdit.setToolTip("Gold Standard 模块在总场景文件夹下的子文件夹名称")
        goldStandardFormLayout.addRow("Gold Standard Set场景子文件夹: ", self.gsModuleFolderNameEdit)

        self.saveGoldStandardButton = qt.QPushButton("保存金标准到场景")
        self.saveGoldStandardButton.toolTip = "将配准后的金标准体积、变换矩阵和标注点保存到场景文件夹"
        self.saveGoldStandardButton.connect('clicked(bool)', self.onSaveGoldStandard)
        goldStandardFormLayout.addRow(self.saveGoldStandardButton)

        # Gold Standard 状态
        self.gsStatusLabel = qt.QLabel("状态: 等待选择数据")
        self.gsStatusLabel.setStyleSheet("color: gray;")
        goldStandardFormLayout.addRow(self.gsStatusLabel)
        
        # 初始化时禁用变换控制
        self.enableTransformControls(False)

        # 添加模块末尾分隔线（黑色粗线）
        separator2 = qt.QFrame()
        separator2.setFrameShape(qt.QFrame.HLine)
        separator2.setFrameShadow(qt.QFrame.Plain)  # Plain 样式，配合背景色实现纯黑
        separator2.setLineWidth(2)
        separator2.setMidLineWidth(0)
        separator2.setStyleSheet("QFrame { background-color: #000000; max-height: 2px; margin: 15px 0px; }")
        goldStandardFormLayout.addRow(separator2)

        #
        # 日志区域
        #
        logCollapsibleButton = ctk.ctkCollapsibleButton()
        logCollapsibleButton.text = "日志与错误信息"
        logCollapsibleButton.collapsed = True
        self.layout.addWidget(logCollapsibleButton)
        logFormLayout = qt.QVBoxLayout(logCollapsibleButton)

        self.logTextEdit = qt.QTextEdit()
        self.logTextEdit.setReadOnly(True)
        self.logTextEdit.setMaximumHeight(200)
        logFormLayout.addWidget(self.logTextEdit)

        clearLogButton = qt.QPushButton("清除日志")
        clearLogButton.connect('clicked(bool)', self.onClearLog)
        logFormLayout.addWidget(clearLogButton)

        # 添加垂直间距
        self.layout.addStretch(1)

        # 连接信号以更新按钮状态
        self.fixedVolumeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateButtonStates)
        self.movingVolumeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateButtonStates)

    def cleanup(self):
        """
        Called when the application closes and the module widget is destroyed.
        """
        self.removeObservers()

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
                self.addLog(f"正在加载 Fixed Volume: {filePath}")
                volumeNode = self.logic.loadVolume(filePath, "fixed_volume")
                if volumeNode:
                    self.fixedVolumeSelector.setCurrentNode(volumeNode)
                    self.addLog(f"✓ Fixed Volume 加载成功: {volumeNode.GetName()}")
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
                self.addLog(f"正在加载 Moving Volume: {filePath}")
                volumeNode = self.logic.loadVolume(filePath, "moving_volume")
                if volumeNode:
                    self.movingVolumeSelector.setCurrentNode(volumeNode)
                    self.addLog(f"✓ Moving Volume 加载成功: {volumeNode.GetName()}")
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
            
            self.addLog(f"正在创建配准流程结构...")
            self.addLog(f"  总文件夹: {mainFolderName}")
            self.addLog(f"  Data Manager子文件夹: {moduleFolderName}")
            
            # 调用 Logic 加载数据到场景
            success = self.logic.loadDataToScene(fixedNode, movingNode, mainFolderName, moduleFolderName)
            
            if success:
                self.addLog(f"✓ 配准数据已组织到场景文件夹")
                self.addLog(f"  路径: {mainFolderName}/{moduleFolderName}")
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

    def addLog(self, message):
        """添加日志信息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        logMessage = f"[{timestamp}] {message}"
        self.logTextEdit.append(logMessage)
        logging.info(message)

    def onClearLog(self):
        """清除日志"""
        self.logTextEdit.clear()
        self.addLog("日志已清除")

    def showError(self, errorMessage):
        """显示错误信息"""
        self.addLog(f"✗ 错误: {errorMessage}")
        self.statusLabel.text = f"状态: 错误"
        self.statusLabel.setStyleSheet("color: red;")
        slicer.util.errorDisplay(errorMessage)
        import traceback
        self.addLog(traceback.format_exc())

    # ========================================
    # Gold Standard Set 模块方法
    # ========================================

    def onApplyTransform(self):
        """将变换应用到 Moving Volume"""
        try:
            movingNode = self.gsMovingVolumeSelector.currentNode()
            transformNode = self.transformSelector.currentNode()

            if not movingNode:
                self.showError("请选择 Moving Volume")
                return

            if not transformNode:
                # 自动创建 Linear Transform（相似变换）
                transformNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLinearTransformNode", "ManualSimilarityTransform")
                self.transformSelector.setCurrentNode(transformNode)
                self.addLog("✓ 已创建相似变换节点")

            # 应用变换
            movingNode.SetAndObserveTransformNodeID(transformNode.GetID())
            
            # 启用快捷控制
            self.enableTransformControls(True)
            
            self.addLog(f"✓ 变换已应用到 Moving Volume: {movingNode.GetName()}")
            self.addLog("提示: 使用下方滑块进行平移、旋转和统一缩放调整（相似变换）")
            self.gsStatusLabel.text = "状态: 变换已应用，可使用快捷控制调整"
            self.gsStatusLabel.setStyleSheet("color: green;")

        except Exception as e:
            self.showError(f"应用变换失败: {str(e)}")
    
    def enableTransformControls(self, enabled):
        """启用/禁用变换控制滑块"""
        self.translateXSlider.enabled = enabled
        self.translateYSlider.enabled = enabled
        self.translateZSlider.enabled = enabled
        self.rotateXSlider.enabled = enabled
        self.rotateYSlider.enabled = enabled
        self.rotateZSlider.enabled = enabled
        self.uniformScaleSlider.enabled = enabled
        self.resetTransformButton.enabled = enabled
    
    def onTransformChanged(self):
        """当变换参数改变时更新变换矩阵（相似变换）"""
        try:
            transformNode = self.transformSelector.currentNode()
            if not transformNode:
                return
            
            import vtk
            
            # 获取当前参数
            tx = self.translateXSlider.value
            ty = self.translateYSlider.value
            tz = self.translateZSlider.value
            
            rx = self.rotateXSlider.value
            ry = self.rotateYSlider.value
            rz = self.rotateZSlider.value
            
            # 相似变换：统一缩放
            scale = self.uniformScaleSlider.value
            
            # 构建变换矩阵: T * Rz * Ry * Rx * S
            # 1. 统一缩放矩阵（相似变换的特征）
            scaleMatrix = vtk.vtkMatrix4x4()
            scaleMatrix.Identity()
            scaleMatrix.SetElement(0, 0, scale)
            scaleMatrix.SetElement(1, 1, scale)
            scaleMatrix.SetElement(2, 2, scale)
            
            # 2. 旋转矩阵 (使用欧拉角，顺序: X -> Y -> Z)
            transform = vtk.vtkTransform()
            transform.PostMultiply()
            transform.RotateX(rx)
            transform.RotateY(ry)
            transform.RotateZ(rz)
            rotationMatrix = transform.GetMatrix()
            
            # 3. 组合缩放和旋转
            combinedMatrix = vtk.vtkMatrix4x4()
            vtk.vtkMatrix4x4.Multiply4x4(rotationMatrix, scaleMatrix, combinedMatrix)
            
            # 4. 添加平移
            combinedMatrix.SetElement(0, 3, tx)
            combinedMatrix.SetElement(1, 3, ty)
            combinedMatrix.SetElement(2, 3, tz)
            
            # 应用变换矩阵
            transformNode.SetMatrixTransformToParent(combinedMatrix)
            
        except Exception as e:
            self.addLog(f"更新变换失败: {str(e)}")
    
    def onResetTransform(self):
        """重置所有变换参数"""
        try:
            # 断开信号
            self.translateXSlider.blockSignals(True)
            self.translateYSlider.blockSignals(True)
            self.translateZSlider.blockSignals(True)
            self.rotateXSlider.blockSignals(True)
            self.rotateYSlider.blockSignals(True)
            self.rotateZSlider.blockSignals(True)
            self.uniformScaleSlider.blockSignals(True)
            
            # 重置值
            self.translateXSlider.value = 0
            self.translateYSlider.value = 0
            self.translateZSlider.value = 0
            self.rotateXSlider.value = 0
            self.rotateYSlider.value = 0
            self.rotateZSlider.value = 0
            self.uniformScaleSlider.value = 1.0
            
            # 恢复信号
            self.translateXSlider.blockSignals(False)
            self.translateYSlider.blockSignals(False)
            self.translateZSlider.blockSignals(False)
            self.rotateXSlider.blockSignals(False)
            self.rotateYSlider.blockSignals(False)
            self.rotateZSlider.blockSignals(False)
            self.uniformScaleSlider.blockSignals(False)
            
            # 更新变换（恢复到单位矩阵）
            self.onTransformChanged()
            
            self.addLog("✓ 变换参数已重置")
            
        except Exception as e:
            self.showError(f"重置变换失败: {str(e)}")

    def onOpenTransforms(self):
        """打开 Transforms 模块进行交互式手动配准"""
        try:
            slicer.util.selectModule("Transforms")
            
            # 如果有选中的变换节点,自动选中它
            transformNode = self.transformSelector.currentNode()
            if transformNode:
                # 设置 Transforms 模块的当前变换节点
                transformsWidget = slicer.modules.transforms.widgetRepresentation()
                if transformsWidget:
                    transformSelector = transformsWidget.findChild(slicer.qMRMLNodeComboBox, "TransformNodeSelector")
                    if transformSelector:
                        transformSelector.setCurrentNode(transformNode)
            
            self.addLog("✓ 已打开 Transforms 模块")
            self.addLog("提示: 使用 Translation/Rotation sliders 来交互式调整 Moving Volume 位置")
        except Exception as e:
            self.showError(f"打开 Transforms 模块失败: {str(e)}")

    def onPlacePair(self, checked):
        """同步放置点对 - 在同一位置同时创建 Fixed 和 Moving 标注点"""
        try:
            if checked:
                # 确保 Fixed 和 Moving 标注点节点存在
                fixedFiducials = self.fixedFiducialsSelector.currentNode()
                if not fixedFiducials:
                    fixedFiducials = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "Fixed_Fiducials")
                    self.fixedFiducialsSelector.setCurrentNode(fixedFiducials)
                    # 设置 Fixed 标注点的显示属性（红色）
                    displayNode = fixedFiducials.GetDisplayNode()
                    if displayNode:
                        displayNode.SetSelectedColor(1.0, 0.0, 0.0)  # 红色
                        displayNode.SetGlyphScale(2.0)  # 稍大一点
                        displayNode.SetTextScale(2.0)
                
                movingFiducials = self.movingFiducialsSelector.currentNode()
                if not movingFiducials:
                    movingFiducials = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "Moving_Fiducials")
                    self.movingFiducialsSelector.setCurrentNode(movingFiducials)
                    # 设置 Moving 标注点的显示属性（绿色）
                    displayNode = movingFiducials.GetDisplayNode()
                    if displayNode:
                        displayNode.SetSelectedColor(0.0, 1.0, 0.0)  # 绿色
                        displayNode.SetGlyphScale(2.0)  # 稍大一点
                        displayNode.SetTextScale(2.0)
                
                # 如果标注点节点已存在，也设置颜色
                fixedDisplayNode = fixedFiducials.GetDisplayNode()
                if fixedDisplayNode:
                    fixedDisplayNode.SetSelectedColor(1.0, 0.0, 0.0)  # 红色
                    fixedDisplayNode.SetGlyphScale(2.0)
                    fixedDisplayNode.SetTextScale(2.0)
                
                movingDisplayNode = movingFiducials.GetDisplayNode()
                if movingDisplayNode:
                    movingDisplayNode.SetSelectedColor(0.0, 1.0, 0.0)  # 绿色
                    movingDisplayNode.SetGlyphScale(2.0)
                    movingDisplayNode.SetTextScale(2.0)
                
                # 设置为持续放置模式（可以连续放置多个点）
                interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
                interactionNode.SetPlaceModePersistence(1)  # 持续放置模式
                
                # 激活 Fixed 标注点的放置模式
                selectionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
                selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")
                selectionNode.SetActivePlaceNodeID(fixedFiducials.GetID())
                interactionNode.SetCurrentInteractionMode(interactionNode.Place)
                
                # 添加观察者,监听 Fixed 标注点的添加事件
                self.pointAddedObserver = fixedFiducials.AddObserver(
                    slicer.vtkMRMLMarkupsNode.PointPositionDefinedEvent,
                    lambda caller, event: self.onFixedPointAdded(caller)
                )
                
                self.addLog("✓ 点对放置模式已激活 (持续放置)")
                self.addLog("提示: Fixed 点显示为红色，Moving 点显示为绿色")
                self.addLog("提示: 可连续点击放置多个点对，完成后点击按钮退出")
                self.gsStatusLabel.text = "状态: 正在放置点对 (持续模式)"
                self.gsStatusLabel.setStyleSheet("color: blue;")
            else:
                # 取消放置模式
                interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
                interactionNode.SetPlaceModePersistence(0)  # 恢复默认
                interactionNode.SetCurrentInteractionMode(interactionNode.ViewTransform)
                
                # 移除观察者
                fixedFiducials = self.fixedFiducialsSelector.currentNode()
                if fixedFiducials and hasattr(self, 'pointAddedObserver'):
                    fixedFiducials.RemoveObserver(self.pointAddedObserver)
                    del self.pointAddedObserver
                
                self.addLog("✓ 点对放置模式已关闭")
                self.gsStatusLabel.text = "状态: 就绪"
                self.gsStatusLabel.setStyleSheet("color: gray;")
            
            self.updatePointPairsTable()
            
        except Exception as e:
            self.showError(f"点对放置模式切换失败: {str(e)}")
            self.placePairButton.setChecked(False)
    
    def onFixedPointAdded(self, fixedFiducials):
        """当 Fixed 标注点添加时,在相同位置添加 Moving 标注点"""
        try:
            movingFiducials = self.movingFiducialsSelector.currentNode()
            if not movingFiducials:
                return
            
            # 获取最后添加的 Fixed 点的位置
            numPoints = fixedFiducials.GetNumberOfControlPoints()
            if numPoints > 0:
                lastIndex = numPoints - 1
                pos = [0, 0, 0]
                fixedFiducials.GetNthControlPointPosition(lastIndex, pos)
                fixedLabel = fixedFiducials.GetNthControlPointLabel(lastIndex)
                
                # 修改 Fixed 点的标签，添加 "F-" 前缀
                fixedFiducials.SetNthControlPointLabel(lastIndex, f"F-{numPoints}")
                
                # 在相同位置添加 Moving 点，使用 "M-" 前缀
                movingFiducials.AddControlPoint(pos, f"M-{numPoints}")
                
                self.addLog(f"✓ 点对 #{numPoints} 已添加: F-{numPoints}(红) 和 M-{numPoints}(绿)")
                self.updatePointPairsTable()
                
        except Exception as e:
            self.showError(f"同步添加 Moving 点失败: {str(e)}")

    def updatePointPairsTable(self):
        """更新点对列表显示"""
        try:
            fixedFiducials = self.fixedFiducialsSelector.currentNode()
            movingFiducials = self.movingFiducialsSelector.currentNode()

            fixedCount = fixedFiducials.GetNumberOfControlPoints() if fixedFiducials else 0
            movingCount = movingFiducials.GetNumberOfControlPoints() if movingFiducials else 0

            self.pointPairsTable.setRowCount(1)
            
            fixedItem = qt.QTableWidgetItem(str(fixedCount))
            movingItem = qt.QTableWidgetItem(str(movingCount))
            
            # 如果点数不匹配,用红色标记
            if fixedCount != movingCount:
                fixedItem.setForeground(qt.QColor(255, 0, 0))
                movingItem.setForeground(qt.QColor(255, 0, 0))
            elif fixedCount > 0:
                fixedItem.setForeground(qt.QColor(0, 128, 0))
                movingItem.setForeground(qt.QColor(0, 128, 0))
            
            self.pointPairsTable.setItem(0, 0, fixedItem)
            self.pointPairsTable.setItem(0, 1, movingItem)

        except Exception as e:
            self.addLog(f"更新点对表格失败: {str(e)}")

    def onClearPoints(self):
        """清除所有标注点"""
        try:
            reply = qt.QMessageBox.question(
                None,
                "确认清除",
                "确定要清除所有标注点吗？此操作不可撤销。",
                qt.QMessageBox.Yes | qt.QMessageBox.No
            )

            if reply == qt.QMessageBox.Yes:
                fixedFiducials = self.fixedFiducialsSelector.currentNode()
                movingFiducials = self.movingFiducialsSelector.currentNode()

                if fixedFiducials:
                    fixedFiducials.RemoveAllControlPoints()
                    self.addLog("✓ 已清除 Fixed 标注点")

                if movingFiducials:
                    movingFiducials.RemoveAllControlPoints()
                    self.addLog("✓ 已清除 Moving 标注点")

                self.updatePointPairsTable()

        except Exception as e:
            self.showError(f"清除标注点失败: {str(e)}")

    def onSaveGoldStandard(self):
        """保存金标准到场景"""
        try:
            # 检查必要的数据
            fixedNode = self.gsFixedVolumeSelector.currentNode()
            movingNode = self.gsMovingVolumeSelector.currentNode()
            transformNode = self.transformSelector.currentNode()
            fixedFiducials = self.fixedFiducialsSelector.currentNode()
            movingFiducials = self.movingFiducialsSelector.currentNode()

            if not fixedNode or not movingNode:
                self.showError("请选择 Fixed 和 Moving Volume")
                return

            if not transformNode:
                self.showError("请选择变换节点")
                return

            # 获取文件夹名称
            mainFolderName = self.mainFolderNameEdit.text
            moduleFolderName = self.gsModuleFolderNameEdit.text

            if not mainFolderName or not moduleFolderName:
                self.showError("请输入文件夹名称")
                return

            self.addLog(f"正在保存金标准到场景...")
            self.addLog(f"  总文件夹: {mainFolderName}")
            self.addLog(f"  Gold Standard 子文件夹: {moduleFolderName}")

            # 调用 Logic 保存金标准
            success = self.logic.saveGoldStandardToScene(
                fixedNode, movingNode, transformNode,
                fixedFiducials, movingFiducials,
                mainFolderName, moduleFolderName
            )

            if success:
                self.addLog(f"✓ 金标准已保存到场景文件夹")
                self.addLog(f"  路径: {mainFolderName}/{moduleFolderName}")
                self.gsStatusLabel.text = "状态: 金标准已保存"
                self.gsStatusLabel.setStyleSheet("color: green;")
                
                qt.QMessageBox.information(
                    None,
                    "保存成功",
                    f"金标准已成功保存到场景文件夹:\n{mainFolderName}/{moduleFolderName}"
                )
            else:
                self.showError("保存金标准失败")

        except Exception as e:
            self.showError(f"保存金标准失败: {str(e)}")


#
# TMJExtensionLogic
#

class TMJExtensionLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self):
        """
        Called when the logic class is instantiated. Can be used for initializing member variables.
        """
        ScriptedLoadableModuleLogic.__init__(self)
        self.logCallback = None

    def log(self, message):
        """日志输出"""
        logging.info(message)
        if self.logCallback:
            self.logCallback(message)

    def loadVolume(self, filePath, nodeName=None):
        """
        加载体积文件,保留原始数据(不重采样,不改变spacing/direction)
        
        :param filePath: 文件路径
        :param nodeName: 节点名称
        :return: 加载的体积节点
        """
        try:
            if not os.path.exists(filePath):
                raise ValueError(f"文件不存在: {filePath}")

            self.log(f"加载文件: {filePath}")

            # 使用 Slicer 的加载函数,这会保留原始数据
            loadedNode = slicer.util.loadVolume(filePath, returnNode=True)[1]
            
            if not loadedNode:
                raise ValueError("加载体积失败")

            # 设置节点名称
            if nodeName:
                loadedNode.SetName(nodeName)
            
            self.log(f"体积加载成功: {loadedNode.GetName()}")
            self.log(f"  - 维度: {loadedNode.GetImageData().GetDimensions()}")
            self.log(f"  - 间距: {loadedNode.GetSpacing()}")
            self.log(f"  - 原点: {loadedNode.GetOrigin()}")
            
            return loadedNode

        except Exception as e:
            self.log(f"加载体积时出错: {str(e)}")
            raise

    def exportData(self, fixedVolume, movingVolume, outputDir, folderName, sceneFolderName, fileFormat="nrrd"):
        """
        导出体积数据和元数据,并在场景中创建文件夹节点来组织管理
        
        :param fixedVolume: Fixed volume 节点
        :param movingVolume: Moving volume 节点
        :param outputDir: 输出目录
        :param folderName: 输出文件夹名称
        :param sceneFolderName: 场景中的文件夹名称
        :param fileFormat: 文件格式 ('nrrd' 或 'nii.gz')
        :return: (成功状态, 文件夹节点)
        """
        try:
            # 1. 在场景中创建文件夹节点
            self.log("创建场景文件夹节点...")
            folderNode = slicer.vtkMRMLFolderDisplayNode()
            folderNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLSubjectHierarchyNode())
            shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
            
            # 创建文件夹在场景根目录下
            sceneItemID = shNode.GetSceneItemID()
            folderItemID = shNode.CreateFolderItem(sceneItemID, sceneFolderName)
            self.log(f"✓ 场景文件夹已创建: {sceneFolderName}")
            
            # 2. 创建磁盘输出文件夹
            outputFolder = os.path.join(outputDir, folderName)
            if not os.path.exists(outputFolder):
                os.makedirs(outputFolder)
                self.log(f"创建输出文件夹: {outputFolder}")

            metadata = {
                "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "file_format": fileFormat,
                "resampled": False,
                "scene_folder": sceneFolderName,
                "volumes": {}
            }

            # 3. 处理 Fixed Volume
            if fixedVolume:
                self.log("导出 Fixed Volume...")
                fixedPath = os.path.join(outputFolder, f"fixed_volume.{fileFormat}")
                
                # 创建该体积的副本并放入场景文件夹
                fixedCopy = self._createVolumeInFolder(fixedVolume, "fixed_volume", shNode, folderItemID)
                
                # 导出到磁盘
                self._exportVolume(fixedCopy, fixedPath, fileFormat)
                metadata["volumes"]["fixed"] = self._extractVolumeMetadata(fixedCopy)
                self.log(f"✓ Fixed Volume 已保存: {fixedPath}")
                self.log(f"✓ Fixed Volume 已添加到场景文件夹")

            # 4. 处理 Moving Volume
            if movingVolume:
                self.log("导出 Moving Volume...")
                movingPath = os.path.join(outputFolder, f"moving_volume.{fileFormat}")
                
                # 创建该体积的副本并放入场景文件夹
                movingCopy = self._createVolumeInFolder(movingVolume, "moving_volume", shNode, folderItemID)
                
                # 导出到磁盘
                self._exportVolume(movingCopy, movingPath, fileFormat)
                metadata["volumes"]["moving"] = self._extractVolumeMetadata(movingCopy)
                self.log(f"✓ Moving Volume 已保存: {movingPath}")
                self.log(f"✓ Moving Volume 已添加到场景文件夹")

            # 5. 保存 metadata.json
            metadataPath = os.path.join(outputFolder, "metadata.json")
            with open(metadataPath, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            self.log(f"✓ 元数据已保存: {metadataPath}")

            return True, shNode

        except Exception as e:
            self.log(f"导出数据时出错: {str(e)}")
            raise

    def _createVolumeInFolder(self, sourceVolume, newName, shNode, folderItemID):
        """
        创建体积的深度副本并将其放入指定的场景文件夹中
        
        :param sourceVolume: 源体积节点
        :param newName: 新体积的名称
        :param shNode: Subject Hierarchy 节点
        :param folderItemID: 文件夹项目 ID
        :return: 新创建的体积节点
        """
        # 创建新的体积节点
        volumeNode = slicer.mrmlScene.AddNewNodeByClass(sourceVolume.GetClassName(), newName)
        
        # 深拷贝图像数据（创建独立的图像数据副本）
        imageData = vtk.vtkImageData()
        imageData.DeepCopy(sourceVolume.GetImageData())
        volumeNode.SetAndObserveImageData(imageData)
        
        # 复制其他属性
        volumeNode.SetOrigin(sourceVolume.GetOrigin())
        volumeNode.SetSpacing(sourceVolume.GetSpacing())
        
        # 复制方向矩阵
        directionMatrix = vtk.vtkMatrix4x4()
        sourceVolume.GetIJKToRASDirectionMatrix(directionMatrix)
        volumeNode.SetIJKToRASDirectionMatrix(directionMatrix)
        
        # 设置名称
        volumeNode.SetName(newName)
        
        # 将新节点移动到文件夹中
        volumeItemID = shNode.GetItemByDataNode(volumeNode)
        shNode.SetItemParent(volumeItemID, folderItemID)
        
        return volumeNode

    def _exportVolume(self, volumeNode, outputPath, fileFormat):
        """
        导出单个体积,保留原始数据
        
        :param volumeNode: 体积节点
        :param outputPath: 输出路径
        :param fileFormat: 文件格式
        """
        try:
            # 使用 Slicer 的保存功能,保留原始数据
            properties = {}
            if fileFormat == "nii.gz":
                properties["useCompression"] = 1
            
            success = slicer.util.saveNode(volumeNode, outputPath, properties)
            
            if not success:
                raise ValueError(f"保存体积失败: {outputPath}")

        except Exception as e:
            raise ValueError(f"导出体积时出错: {str(e)}")

    def _extractVolumeMetadata(self, volumeNode):
        """
        提取体积的元数据
        
        :param volumeNode: 体积节点
        :return: 元数据字典
        """
        try:
            imageData = volumeNode.GetImageData()
            
            # 获取基本信息
            dimensions = imageData.GetDimensions()
            spacing = volumeNode.GetSpacing()
            origin = volumeNode.GetOrigin()
            
            # 获取方向矩阵
            directionMatrix = vtk.vtkMatrix4x4()
            volumeNode.GetIJKToRASDirectionMatrix(directionMatrix)
            direction = []
            for i in range(3):
                row = []
                for j in range(3):
                    row.append(directionMatrix.GetElement(i, j))
                direction.append(row)

            # 获取数组数据用于统计
            import vtk.util.numpy_support as vtk_np
            imageArray = vtk_np.vtk_to_numpy(imageData.GetPointData().GetScalars())
            
            # 计算统计信息
            stats = {
                "min": float(np.min(imageArray)),
                "max": float(np.max(imageArray)),
                "mean": float(np.mean(imageArray)),
                "std": float(np.std(imageArray)),
                "median": float(np.median(imageArray))
            }

            # 检测数据类型 (CT通常是 HU 值,范围约 -1000 到 3000)
            dataType = "MR"
            if stats["min"] < -500 and stats["max"] > 1000:
                dataType = "CT"
                self.log(f"  检测到 CT 数据 (HU 值范围: {stats['min']:.1f} 到 {stats['max']:.1f})")
            else:
                self.log(f"  检测到 MR 数据 (强度范围: {stats['min']:.1f} 到 {stats['max']:.1f})")

            metadata = {
                "name": volumeNode.GetName(),
                "data_type": dataType,
                "dimensions": list(dimensions),
                "spacing": list(spacing),
                "origin": list(origin),
                "direction": direction,
                "scalar_type": imageData.GetScalarTypeAsString(),
                "number_of_components": imageData.GetNumberOfScalarComponents(),
                "intensity_statistics": stats,
                "resampled": False,
                "notes": f"Original {'HU' if dataType == 'CT' else 'intensity'} values preserved"
            }

            return metadata

        except Exception as e:
            self.log(f"提取元数据时出错: {str(e)}")
            raise

    def loadDataToScene(self, fixedVolume, movingVolume, mainFolderName, moduleFolderName):
        """
        将配准数据加载到场景文件夹中(两层结构)
        
        :param fixedVolume: Fixed volume 节点
        :param movingVolume: Moving volume 节点
        :param mainFolderName: 配准流程总文件夹名称
        :param moduleFolderName: 模块子文件夹名称
        :return: 成功状态
        """
        try:
            # 获取 Subject Hierarchy 节点
            shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
            sceneItemID = shNode.GetSceneItemID()
            
            # 检查总文件夹是否已存在
            mainFolderItemID = shNode.GetItemChildWithName(sceneItemID, mainFolderName)
            
            if mainFolderItemID == 0:  # 不存在,创建新的总文件夹
                mainFolderItemID = shNode.CreateFolderItem(sceneItemID, mainFolderName)
                self.log(f"✓ 创建配准流程总文件夹: {mainFolderName}")
            else:
                self.log(f"✓ 使用已存在的总文件夹: {mainFolderName}")
            
            # 在总文件夹下创建模块子文件夹
            moduleFolderItemID = shNode.CreateFolderItem(mainFolderItemID, moduleFolderName)
            self.log(f"✓ 创建模块子文件夹: {moduleFolderName}")
            
            # 将 Fixed Volume 复制到模块子文件夹中
            if fixedVolume:
                fixedCopy = self._createVolumeInFolder(fixedVolume, "Fixed_Volume", shNode, moduleFolderItemID)
                self.log(f"✓ Fixed Volume 已添加到 {moduleFolderName}")
            
            # 将 Moving Volume 复制到模块子文件夹中
            if movingVolume:
                movingCopy = self._createVolumeInFolder(movingVolume, "Moving_Volume", shNode, moduleFolderItemID)
                self.log(f"✓ Moving Volume 已添加到 {moduleFolderName}")
            
            return True
            
        except Exception as e:
            self.log(f"加载数据到场景时出错: {str(e)}")
            raise

    def saveGoldStandardToScene(self, fixedVolume, movingVolume, transformNode, 
                                fixedFiducials, movingFiducials,
                                mainFolderName, moduleFolderName):
        """
        将金标准数据保存到场景文件夹中
        
        :param fixedVolume: Fixed volume 节点
        :param movingVolume: Moving volume 节点  
        :param transformNode: 变换节点
        :param fixedFiducials: Fixed 标注点
        :param movingFiducials: Moving 标注点
        :param mainFolderName: 配准流程总文件夹名称
        :param moduleFolderName: 模块子文件夹名称
        :return: 成功状态
        """
        try:
            # 获取 Subject Hierarchy 节点
            shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
            sceneItemID = shNode.GetSceneItemID()
            
            # 检查总文件夹是否已存在
            mainFolderItemID = shNode.GetItemChildWithName(sceneItemID, mainFolderName)
            
            if mainFolderItemID == 0:  # 不存在,创建新的总文件夹
                mainFolderItemID = shNode.CreateFolderItem(sceneItemID, mainFolderName)
                self.log(f"✓ 创建配准流程总文件夹: {mainFolderName}")
            else:
                self.log(f"✓ 使用已存在的总文件夹: {mainFolderName}")
            
            # 在总文件夹下创建模块子文件夹
            moduleFolderItemID = shNode.CreateFolderItem(mainFolderItemID, moduleFolderName)
            self.log(f"✓ 创建模块子文件夹: {moduleFolderName}")
            
            # 1. 保存配准后的 Fixed Volume (原始的,不需要变换)
            if fixedVolume:
                fixedCopy = self._createVolumeInFolder(fixedVolume, "GoldStandard_Fixed", shNode, moduleFolderItemID)
                self.log(f"✓ Fixed Volume 已保存")
            
            # 2. 先保存变换矩阵（因为后面要用）
            transformCopy = None
            if transformNode:
                transformCopy = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLinearTransformNode", "GoldStandard_Transform")
                
                # 复制变换矩阵
                transformMatrix = vtk.vtkMatrix4x4()
                transformNode.GetMatrixTransformToParent(transformMatrix)
                transformCopy.SetMatrixTransformToParent(transformMatrix)
                
                # 移动到文件夹
                transformItemID = shNode.GetItemByDataNode(transformCopy)
                shNode.SetItemParent(transformItemID, moduleFolderItemID)
                self.log(f"✓ 变换矩阵已保存")
            
            # 3. 保存 Moving Volume（深拷贝创建完全独立的副本）
            movingCopy = None
            if movingVolume:
                # 使用 _createVolumeInFolder 创建深拷贝的独立副本
                movingCopy = slicer.mrmlScene.AddNewNodeByClass(movingVolume.GetClassName(), "GoldStandard_Moving")
                
                # 深拷贝图像数据（确保完全独立）
                imageData = vtk.vtkImageData()
                imageData.DeepCopy(movingVolume.GetImageData())
                movingCopy.SetAndObserveImageData(imageData)
                
                # 复制几何属性
                movingCopy.SetOrigin(movingVolume.GetOrigin())
                movingCopy.SetSpacing(movingVolume.GetSpacing())
                
                # 复制方向矩阵
                directionMatrix = vtk.vtkMatrix4x4()
                movingVolume.GetIJKToRASDirectionMatrix(directionMatrix)
                movingCopy.SetIJKToRASDirectionMatrix(directionMatrix)
                
                # 确保新副本没有任何变换绑定
                movingCopy.SetAndObserveTransformNodeID(None)
                
                # 绑定到新的 GoldStandard_Transform
                if transformCopy:
                    movingCopy.SetAndObserveTransformNodeID(transformCopy.GetID())
                    self.log(f"✓ GoldStandard_Moving 已绑定到 GoldStandard_Transform")
                
                # 移动到文件夹
                movingItemID = shNode.GetItemByDataNode(movingCopy)
                shNode.SetItemParent(movingItemID, moduleFolderItemID)
                
                self.log(f"✓ Moving Volume 已深拷贝保存为 GoldStandard_Moving（完全独立）")
            
            # 4. 保存 Fixed Fiducials
            if fixedFiducials and fixedFiducials.GetNumberOfControlPoints() > 0:
                fixedFidCopy = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "GoldStandard_Fixed_Fiducials")
                
                # 复制所有标注点
                for i in range(fixedFiducials.GetNumberOfControlPoints()):
                    pos = [0, 0, 0]
                    fixedFiducials.GetNthControlPointPosition(i, pos)
                    label = fixedFiducials.GetNthControlPointLabel(i)
                    fixedFidCopy.AddControlPoint(pos, label)
                
                # 复制显示属性（颜色、大小等）
                fixedDisplayNode = fixedFiducials.GetDisplayNode()
                if fixedDisplayNode:
                    fixedCopyDisplayNode = fixedFidCopy.GetDisplayNode()
                    if fixedCopyDisplayNode:
                        # 复制颜色
                        color = fixedDisplayNode.GetSelectedColor()
                        fixedCopyDisplayNode.SetSelectedColor(color[0], color[1], color[2])
                        fixedCopyDisplayNode.SetColor(color[0], color[1], color[2])
                        
                        # 复制大小
                        fixedCopyDisplayNode.SetGlyphScale(fixedDisplayNode.GetGlyphScale())
                        fixedCopyDisplayNode.SetTextScale(fixedDisplayNode.GetTextScale())
                        
                        # 复制透明度
                        fixedCopyDisplayNode.SetOpacity(fixedDisplayNode.GetOpacity())
                        
                        self.log(f"  - Fixed 标注点显示属性已复制（红色，大小 {fixedDisplayNode.GetGlyphScale()}）")
                
                # 移动到文件夹
                fixedFidItemID = shNode.GetItemByDataNode(fixedFidCopy)
                shNode.SetItemParent(fixedFidItemID, moduleFolderItemID)
                self.log(f"✓ Fixed 标注点已保存 ({fixedFiducials.GetNumberOfControlPoints()} 个点)")
            
            # 5. 保存 Moving Fiducials (应用变换后的位置)
            if movingFiducials and movingFiducials.GetNumberOfControlPoints() > 0:
                movingFidCopy = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "GoldStandard_Moving_Fiducials")
                
                # 复制所有标注点(应用变换)
                for i in range(movingFiducials.GetNumberOfControlPoints()):
                    pos = [0, 0, 0]
                    movingFiducials.GetNthControlPointPosition(i, pos)
                    
                    # 如果 Moving 有变换,应用变换
                    if movingVolume and movingVolume.GetTransformNodeID():
                        transformNode = slicer.mrmlScene.GetNodeByID(movingVolume.GetTransformNodeID())
                        if transformNode:
                            pos4 = [pos[0], pos[1], pos[2], 1.0]
                            transformMatrix = vtk.vtkMatrix4x4()
                            transformNode.GetMatrixTransformToParent(transformMatrix)
                            transformedPos = transformMatrix.MultiplyPoint(pos4)
                            pos = [transformedPos[0], transformedPos[1], transformedPos[2]]
                    
                    label = movingFiducials.GetNthControlPointLabel(i)
                    movingFidCopy.AddControlPoint(pos, label)
                
                # 复制显示属性（颜色、大小等）
                movingDisplayNode = movingFiducials.GetDisplayNode()
                if movingDisplayNode:
                    movingCopyDisplayNode = movingFidCopy.GetDisplayNode()
                    if movingCopyDisplayNode:
                        # 复制颜色
                        color = movingDisplayNode.GetSelectedColor()
                        movingCopyDisplayNode.SetSelectedColor(color[0], color[1], color[2])
                        movingCopyDisplayNode.SetColor(color[0], color[1], color[2])
                        
                        # 复制大小
                        movingCopyDisplayNode.SetGlyphScale(movingDisplayNode.GetGlyphScale())
                        movingCopyDisplayNode.SetTextScale(movingDisplayNode.GetTextScale())
                        
                        # 复制透明度
                        movingCopyDisplayNode.SetOpacity(movingDisplayNode.GetOpacity())
                        
                        self.log(f"  - Moving 标注点显示属性已复制（绿色，大小 {movingDisplayNode.GetGlyphScale()}）")
                
                # 移动到文件夹
                movingFidItemID = shNode.GetItemByDataNode(movingFidCopy)
                shNode.SetItemParent(movingFidItemID, moduleFolderItemID)
                self.log(f"✓ Moving 标注点已保存 ({movingFiducials.GetNumberOfControlPoints()} 个点)")
            
            # 6. 验证点对数量
            fixedCount = fixedFiducials.GetNumberOfControlPoints() if fixedFiducials else 0
            movingCount = movingFiducials.GetNumberOfControlPoints() if movingFiducials else 0
            
            if fixedCount == movingCount and fixedCount > 0:
                self.log(f"✓ 点对验证通过: {fixedCount} 对点")
            elif fixedCount == 0 and movingCount == 0:
                self.log(f"⚠ 警告: 未保存标注点")
            else:
                self.log(f"⚠ 警告: 点对数量不匹配 (Fixed: {fixedCount}, Moving: {movingCount})")
            
            # 7. 删除临时节点
            self.log("--- 清理临时节点 ---")
            
            # 删除手动配准使用的变换节点
            if transformNode:
                slicer.mrmlScene.RemoveNode(transformNode)
                self.log(f"✓ 删除临时变换节点: {transformNode.GetName()}")
            
            # 删除 Fixed 标注点
            if fixedFiducials:
                slicer.mrmlScene.RemoveNode(fixedFiducials)
                self.log(f"✓ 删除临时 Fixed 标注点")
            
            # 删除 Moving 标注点
            if movingFiducials:
                slicer.mrmlScene.RemoveNode(movingFiducials)
                self.log(f"✓ 删除临时 Moving 标注点")
            
            # 解除 Moving Volume 的原始变换绑定
            if movingVolume:
                movingVolume.SetAndObserveTransformNodeID(None)
                self.log(f"✓ 解除原始 Moving Volume 的变换绑定")
            
            self.log(f"✓ 金标准数据保存完成")
            self.log(f"  - 保存的体积: GoldStandard_Fixed, GoldStandard_Moving")
            self.log(f"  - 变换关系: GoldStandard_Moving → GoldStandard_Transform")
            self.log(f"  - 标注点对: {min(fixedCount, movingCount)} 对")
            
            return True
            
        except Exception as e:
            self.log(f"保存金标准到场景时出错: {str(e)}")
            raise


#
# TMJExtensionTest
#

class TMJExtensionTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_TMJExtension1()

    def test_TMJExtension1(self):
        """ Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # TODO: Add your test code here

        self.delayDisplay('Test passed')
