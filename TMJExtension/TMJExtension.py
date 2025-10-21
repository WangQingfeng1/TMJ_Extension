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
        self.parent.title = "TMJ Extension - Data Manager"
        self.parent.categories = ["TMJ Analysis"]
        self.parent.dependencies = []
        self.parent.contributors = ["Your Name"]
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
        importLabel0.setStyleSheet("font-weight: bold; margin-top: 10px;")
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
        importLabel.setStyleSheet("font-weight: bold; margin-top: 10px;")
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

        # 配准流程文件夹名称
        self.sceneFolderNameEdit = qt.QLineEdit()
        self.sceneFolderNameEdit.text = "TMJ_Registration_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        self.sceneFolderNameEdit.setToolTip("在场景中创建的配准流程文件夹名称")
        dataManagerFormLayout.addRow("创建配准流程文件夹为:", self.sceneFolderNameEdit)

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
            
            # 获取场景文件夹名称
            folderName = self.sceneFolderNameEdit.text
            if not folderName:
                self.showError("请输入配准流程文件夹名称")
                return
            
            self.addLog(f"正在组织配准数据到文件夹: {folderName}")
            
            # 调用 Logic 加载数据到场景
            success = self.logic.loadDataToScene(fixedNode, movingNode, folderName)
            
            if success:
                self.addLog(f"✓ 配准数据已组织到场景文件夹")
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
        创建体积的副本并将其放入指定的场景文件夹中
        
        :param sourceVolume: 源体积节点
        :param newName: 新体积的名称
        :param shNode: Subject Hierarchy 节点
        :param folderItemID: 文件夹项目 ID
        :return: 新创建的体积节点
        """
        # 克隆体积节点
        volumeNode = slicer.mrmlScene.AddNewNodeByClass(sourceVolume.GetClassName(), newName)
        volumeNode.Copy(sourceVolume)
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

    def loadDataToScene(self, fixedVolume, movingVolume, folderName):
        """
        将配准数据加载到场景文件夹中
        
        :param fixedVolume: Fixed volume 节点
        :param movingVolume: Moving volume 节点
        :param folderName: 场景文件夹名称
        :return: 成功状态
        """
        try:
            # 获取 Subject Hierarchy 节点
            shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
            
            # 在场景根目录下创建文件夹
            sceneItemID = shNode.GetSceneItemID()
            folderItemID = shNode.CreateFolderItem(sceneItemID, folderName)
            self.log(f"✓ 配准流程文件夹已创建: {folderName}")
            
            # 将 Fixed Volume 复制到文件夹中
            if fixedVolume:
                fixedCopy = self._createVolumeInFolder(fixedVolume, "Fixed_Volume", shNode, folderItemID)
                self.log(f"✓ Fixed Volume 已添加到配准流程文件夹")
            
            # 将 Moving Volume 复制到文件夹中
            if movingVolume:
                movingCopy = self._createVolumeInFolder(movingVolume, "Moving_Volume", shNode, folderItemID)
                self.log(f"✓ Moving Volume 已添加到配准流程文件夹")
            
            return True
            
        except Exception as e:
            self.log(f"加载数据到场景时出错: {str(e)}")
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
