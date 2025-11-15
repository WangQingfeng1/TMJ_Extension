"""
Coarse Registration Widget -         self.rmsErrorLabel = None
        self.pointPairsTable = None
        self.placeFixedButton = None
        self.placeMovingButton = None
        self.registerButton = None
        self.clearPointsButton = NoneUI界面
"""
import qt
import ctk
import slicer
from .coarse_registration_logic import CoarseRegistrationLogic


class CoarseRegistrationWidget:
    """
    Coarse Registration 的UI组件类
    负责基于基准点的粗配准界面
    """

    def __init__(self, parent, logCallback, getMainFolderNameCallback):
        """
        初始化 Coarse Registration Widget
        
        :param parent: 父布局
        :param logCallback: 日志回调函数
        :param getMainFolderNameCallback: 获取主文件夹名称的回调函数
        """
        self.parent = parent
        self.logCallback = logCallback
        self.getMainFolderNameCallback = getMainFolderNameCallback
        self.logic = CoarseRegistrationLogic(logCallback=logCallback)
        
        # UI 组件引用
        self.crFixedVolumeSelector = None
        self.crMovingVolumeSelector = None
        self.crFixedFiducialsSelector = None
        self.crMovingFiducialsSelector = None
        self.crModuleFolderNameEdit = None
        self.crStatusLabel = None
        self.pointPairsTable = None
        self.placePairButton = None
        self.registerButton = None
        self.pointAddedObserver = None
        
        self.setupUI()

    def setupUI(self):
        """设置 Coarse Registration 的UI界面"""
        # Coarse Registration 模块
        coarseRegCollapsibleButton = ctk.ctkCollapsibleButton()
        coarseRegCollapsibleButton.text = "Coarse Registration"
        coarseRegCollapsibleButton.collapsed = False
        self.parent.addWidget(coarseRegCollapsibleButton)
        coarseRegFormLayout = qt.QFormLayout(coarseRegCollapsibleButton)

        # 模块说明
        descLabel = qt.QLabel(
            "基于基准点的粗配准，避免后续精配准时因初始位置差异过大导致失败。\n"
            "使用相似变换（平移+旋转+统一缩放）将 Moving Volume 粗略对齐到 Fixed Volume。"
        )
        descLabel.setWordWrap(True)
        descLabel.setStyleSheet("color: #555; font-style: italic; margin-bottom: 10px;")
        coarseRegFormLayout.addRow(descLabel)

        # 从场景中选择数据
        selectLabel = qt.QLabel("选择配准数据 (通常从 Data Manager 场景子文件夹中选择):")
        selectLabel.setStyleSheet("font-weight: bold;")
        coarseRegFormLayout.addRow(selectLabel)

        # Fixed Volume 选择器
        self.crFixedVolumeSelector = slicer.qMRMLNodeComboBox()
        self.crFixedVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.crFixedVolumeSelector.selectNodeUponCreation = False
        self.crFixedVolumeSelector.addEnabled = False
        self.crFixedVolumeSelector.removeEnabled = False
        self.crFixedVolumeSelector.noneEnabled = True
        self.crFixedVolumeSelector.showHidden = False
        self.crFixedVolumeSelector.setMRMLScene(slicer.mrmlScene)
        self.crFixedVolumeSelector.setToolTip("选择 Fixed Volume (CBCT)")
        coarseRegFormLayout.addRow("Fixed Volume (CBCT): ", self.crFixedVolumeSelector)

        # Moving Volume 选择器
        self.crMovingVolumeSelector = slicer.qMRMLNodeComboBox()
        self.crMovingVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.crMovingVolumeSelector.selectNodeUponCreation = False
        self.crMovingVolumeSelector.addEnabled = False
        self.crMovingVolumeSelector.removeEnabled = False
        self.crMovingVolumeSelector.noneEnabled = True
        self.crMovingVolumeSelector.showHidden = False
        self.crMovingVolumeSelector.setMRMLScene(slicer.mrmlScene)
        self.crMovingVolumeSelector.setToolTip("选择 Moving Volume (MRI)")
        coarseRegFormLayout.addRow("Moving Volume (MRI): ", self.crMovingVolumeSelector)

        # 基准点选择
        fiducialsLabel = qt.QLabel("选择或创建基准点:")
        fiducialsLabel.setStyleSheet("font-weight: bold; margin-top: 10px;")
        coarseRegFormLayout.addRow(fiducialsLabel)

        # Fixed Fiducials
        self.crFixedFiducialsSelector = slicer.qMRMLNodeComboBox()
        self.crFixedFiducialsSelector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
        self.crFixedFiducialsSelector.selectNodeUponCreation = True
        self.crFixedFiducialsSelector.addEnabled = True
        self.crFixedFiducialsSelector.removeEnabled = True
        self.crFixedFiducialsSelector.noneEnabled = False
        self.crFixedFiducialsSelector.showHidden = False
        self.crFixedFiducialsSelector.setMRMLScene(slicer.mrmlScene)
        self.crFixedFiducialsSelector.setToolTip("Fixed Volume 上的基准点 (至少3个)")
        self.crFixedFiducialsSelector.baseName = "CoarseReg_Fixed_Points"
        coarseRegFormLayout.addRow("Fixed 基准点: ", self.crFixedFiducialsSelector)

        # Moving Fiducials
        self.crMovingFiducialsSelector = slicer.qMRMLNodeComboBox()
        self.crMovingFiducialsSelector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
        self.crMovingFiducialsSelector.selectNodeUponCreation = True
        self.crMovingFiducialsSelector.addEnabled = True
        self.crMovingFiducialsSelector.removeEnabled = True
        self.crMovingFiducialsSelector.noneEnabled = False
        self.crMovingFiducialsSelector.showHidden = False
        self.crMovingFiducialsSelector.setMRMLScene(slicer.mrmlScene)
        self.crMovingFiducialsSelector.setToolTip("Moving Volume 上的基准点 (至少3个)")
        self.crMovingFiducialsSelector.baseName = "CoarseReg_Moving_Points"
        coarseRegFormLayout.addRow("Moving 基准点: ", self.crMovingFiducialsSelector)

        # 基准点操作按钮
        fiducialButtonsLayout = qt.QHBoxLayout()
        
        self.placeFixedButton = qt.QPushButton("放置 Fixed 基准点")
        self.placeFixedButton.toolTip = "在 Fixed Volume 上标注解剖标志点"
        self.placeFixedButton.checkable = True
        self.placeFixedButton.connect('toggled(bool)', self.onPlaceFixed)
        fiducialButtonsLayout.addWidget(self.placeFixedButton)

        self.placeMovingButton = qt.QPushButton("放置 Moving 基准点")
        self.placeMovingButton.toolTip = "在 Moving Volume 上标注对应的解剖标志点"
        self.placeMovingButton.checkable = True
        self.placeMovingButton.connect('toggled(bool)', self.onPlaceMoving)
        fiducialButtonsLayout.addWidget(self.placeMovingButton)

        coarseRegFormLayout.addRow(fiducialButtonsLayout)

        clearButtonsLayout = qt.QHBoxLayout()
        self.clearPointsButton = qt.QPushButton("清除所有点")
        self.clearPointsButton.toolTip = "清除所有基准点"
        self.clearPointsButton.connect('clicked(bool)', self.onClearPoints)
        clearButtonsLayout.addWidget(self.clearPointsButton)
        coarseRegFormLayout.addRow(clearButtonsLayout)

        # 基准点对列表显示
        self.pointPairsTable = qt.QTableWidget()
        self.pointPairsTable.setColumnCount(2)
        self.pointPairsTable.setHorizontalHeaderLabels(["Fixed 点数", "Moving 点数"])
        self.pointPairsTable.setMaximumHeight(80)
        self.pointPairsTable.horizontalHeader().setStretchLastSection(True)
        self.pointPairsTable.setColumnWidth(0, 120)
        coarseRegFormLayout.addRow("基准点对数量:", self.pointPairsTable)

        # 提示信息
        hintLabel = qt.QLabel("💡 提示: 分别在 Fixed 和 Moving Volume 上选择对应的解剖标志点\n"
                             "步骤: 1) 先在 Fixed 上标注点  2) 再在 Moving 上标注对应的点  3) 确保点数相同且顺序对应")
        hintLabel.setWordWrap(True)
        hintLabel.setStyleSheet("color: #2196F3; margin: 5px 0px;")
        coarseRegFormLayout.addRow(hintLabel)

        # 粗配准按钮
        registrationLabel = qt.QLabel("执行粗配准:")
        registrationLabel.setStyleSheet("font-weight: bold; margin-top: 10px;")
        coarseRegFormLayout.addRow(registrationLabel)

        self.registerButton = qt.QPushButton("计算粗配准变换")
        self.registerButton.toolTip = "基于基准点对计算相似变换 (至少需要3对点)"
        self.registerButton.enabled = False
        self.registerButton.connect('clicked(bool)', self.onRegister)
        coarseRegFormLayout.addRow(self.registerButton)

        # 保存配准结果
        saveLabel = qt.QLabel("保存粗配准结果:")
        saveLabel.setStyleSheet("font-weight: bold; margin-top: 10px;")
        coarseRegFormLayout.addRow(saveLabel)

        # Coarse Registration 子文件夹名称
        self.crModuleFolderNameEdit = qt.QLineEdit()
        self.crModuleFolderNameEdit.text = "Coarse Registration"
        self.crModuleFolderNameEdit.setToolTip("Coarse Registration 模块在总场景文件夹下的子文件夹名称")
        coarseRegFormLayout.addRow("场景子文件夹: ", self.crModuleFolderNameEdit)

        self.saveResultButton = qt.QPushButton("保存粗配准结果到场景")
        self.saveResultButton.toolTip = "将粗配准后的体积、变换矩阵和基准点保存到场景文件夹"
        self.saveResultButton.enabled = False
        self.saveResultButton.connect('clicked(bool)', self.onSaveResult)
        coarseRegFormLayout.addRow(self.saveResultButton)

        # 状态信息
        self.crStatusLabel = qt.QLabel("状态: 等待选择数据")
        self.crStatusLabel.setStyleSheet("color: gray;")
        coarseRegFormLayout.addRow(self.crStatusLabel)

        # 添加模块末尾分隔线（黑色粗线）
        separator = qt.QFrame()
        separator.setFrameShape(qt.QFrame.HLine)
        separator.setFrameShadow(qt.QFrame.Plain)
        separator.setLineWidth(2)
        separator.setMidLineWidth(0)
        separator.setStyleSheet("QFrame { background-color: #000000; max-height: 2px; margin: 15px 0px; }")
        coarseRegFormLayout.addRow(separator)

        # 连接信号
        self.crFixedVolumeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateButtonStates)
        self.crMovingVolumeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateButtonStates)
        self.crFixedFiducialsSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateButtonStates)
        self.crMovingFiducialsSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateButtonStates)

        # 初始化表格
        self.updatePointPairsTable()

    def onPlaceFixed(self, checked):
        """放置 Fixed 基准点"""
        try:
            if checked:
                # 确保 Fixed 标注点节点存在
                fixedFiducials = self.crFixedFiducialsSelector.currentNode()
                if not fixedFiducials:
                    fixedFiducials = slicer.mrmlScene.AddNewNodeByClass(
                        "vtkMRMLMarkupsFiducialNode", 
                        "CoarseReg_Fixed_Points"
                    )
                    self.crFixedFiducialsSelector.setCurrentNode(fixedFiducials)
                
                # 设置 Fixed 标注点的显示属性（红色）
                displayNode = fixedFiducials.GetDisplayNode()
                if displayNode:
                    displayNode.SetSelectedColor(1.0, 0.0, 0.0)  # 红色
                    displayNode.SetGlyphScale(2.5)
                    displayNode.SetTextScale(2.5)
                
                # 关闭 Moving 放置模式
                self.placeMovingButton.setChecked(False)
                
                # 设置为持续放置模式
                interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
                interactionNode.SetPlaceModePersistence(1)
                
                # 激活 Fixed 标注点的放置模式
                selectionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
                selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")
                selectionNode.SetActivePlaceNodeID(fixedFiducials.GetID())
                interactionNode.SetCurrentInteractionMode(interactionNode.Place)
                
                self.logCallback("✓ Fixed 基准点放置模式已激活")
                self.logCallback("提示: 在 Fixed Volume 上点击标注解剖标志点 (红色)")
                self.crStatusLabel.text = "状态: 正在放置 Fixed 基准点"
                self.crStatusLabel.setStyleSheet("color: blue;")
            else:
                # 取消放置模式
                interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
                interactionNode.SetPlaceModePersistence(0)
                interactionNode.SetCurrentInteractionMode(interactionNode.ViewTransform)
                
                self.logCallback("✓ Fixed 基准点放置模式已关闭")
                self.crStatusLabel.text = "状态: 就绪"
                self.crStatusLabel.setStyleSheet("color: gray;")
            
            self.updatePointPairsTable()
            self.updateButtonStates()
            
        except Exception as e:
            self.showError(f"Fixed 基准点放置模式切换失败: {str(e)}")
            self.placeFixedButton.setChecked(False)
    
    def onPlaceMoving(self, checked):
        """放置 Moving 基准点"""
        try:
            if checked:
                # 确保 Moving 标注点节点存在
                movingFiducials = self.crMovingFiducialsSelector.currentNode()
                if not movingFiducials:
                    movingFiducials = slicer.mrmlScene.AddNewNodeByClass(
                        "vtkMRMLMarkupsFiducialNode", 
                        "CoarseReg_Moving_Points"
                    )
                    self.crMovingFiducialsSelector.setCurrentNode(movingFiducials)
                
                # 设置 Moving 标注点的显示属性（绿色）
                displayNode = movingFiducials.GetDisplayNode()
                if displayNode:
                    displayNode.SetSelectedColor(0.0, 1.0, 0.0)  # 绿色
                    displayNode.SetGlyphScale(2.5)
                    displayNode.SetTextScale(2.5)
                
                # 关闭 Fixed 放置模式
                self.placeFixedButton.setChecked(False)
                
                # 设置为持续放置模式
                interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
                interactionNode.SetPlaceModePersistence(1)
                
                # 激活 Moving 标注点的放置模式
                selectionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
                selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")
                selectionNode.SetActivePlaceNodeID(movingFiducials.GetID())
                interactionNode.SetCurrentInteractionMode(interactionNode.Place)
                
                self.logCallback("✓ Moving 基准点放置模式已激活")
                self.logCallback("提示: 在 Moving Volume 上点击标注对应的解剖标志点 (绿色)")
                self.crStatusLabel.text = "状态: 正在放置 Moving 基准点"
                self.crStatusLabel.setStyleSheet("color: blue;")
            else:
                # 取消放置模式
                interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
                interactionNode.SetPlaceModePersistence(0)
                interactionNode.SetCurrentInteractionMode(interactionNode.ViewTransform)
                
                self.logCallback("✓ Moving 基准点放置模式已关闭")
                self.crStatusLabel.text = "状态: 就绪"
                self.crStatusLabel.setStyleSheet("color: gray;")
            
            self.updatePointPairsTable()
            self.updateButtonStates()
            
        except Exception as e:
            self.showError(f"Moving 基准点放置模式切换失败: {str(e)}")
            self.placeMovingButton.setChecked(False)

    def updatePointPairsTable(self):
        """更新基准点对列表显示"""
        try:
            fixedFiducials = self.crFixedFiducialsSelector.currentNode()
            movingFiducials = self.crMovingFiducialsSelector.currentNode()

            fixedCount = fixedFiducials.GetNumberOfControlPoints() if fixedFiducials else 0
            movingCount = movingFiducials.GetNumberOfControlPoints() if movingFiducials else 0

            self.pointPairsTable.setRowCount(1)
            
            fixedItem = qt.QTableWidgetItem(str(fixedCount))
            movingItem = qt.QTableWidgetItem(str(movingCount))
            
            # 根据点数设置颜色
            if fixedCount != movingCount:
                # 点数不匹配 - 红色
                fixedItem.setForeground(qt.QColor(255, 0, 0))
                movingItem.setForeground(qt.QColor(255, 0, 0))
            elif fixedCount >= 3:
                # 点数足够 - 绿色
                fixedItem.setForeground(qt.QColor(0, 128, 0))
                movingItem.setForeground(qt.QColor(0, 128, 0))
            elif fixedCount > 0:
                # 点数不足 - 橙色
                fixedItem.setForeground(qt.QColor(255, 140, 0))
                movingItem.setForeground(qt.QColor(255, 140, 0))
            
            self.pointPairsTable.setItem(0, 0, fixedItem)
            self.pointPairsTable.setItem(0, 1, movingItem)

        except Exception as e:
            self.logCallback(f"更新基准点对表格失败: {str(e)}")

    def onClearPoints(self):
        """清除所有基准点"""
        try:
            reply = qt.QMessageBox.question(
                None,
                "确认清除",
                "确定要清除所有基准点吗？此操作不可撤销。",
                qt.QMessageBox.Yes | qt.QMessageBox.No
            )

            if reply == qt.QMessageBox.Yes:
                fixedFiducials = self.crFixedFiducialsSelector.currentNode()
                movingFiducials = self.crMovingFiducialsSelector.currentNode()

                if fixedFiducials:
                    fixedFiducials.RemoveAllControlPoints()
                    self.logCallback("✓ 已清除 Fixed 基准点")

                if movingFiducials:
                    movingFiducials.RemoveAllControlPoints()
                    self.logCallback("✓ 已清除 Moving 基准点")

                self.updatePointPairsTable()
                self.updateButtonStates()
                
                # 重置 RMS 误差

        except Exception as e:
            self.showError(f"清除基准点失败: {str(e)}")

    def updateButtonStates(self):
        """更新按钮状态"""
        try:
            hasFixed = self.crFixedVolumeSelector.currentNode() is not None
            hasMoving = self.crMovingVolumeSelector.currentNode() is not None
            
            fixedFiducials = self.crFixedFiducialsSelector.currentNode()
            movingFiducials = self.crMovingFiducialsSelector.currentNode()
            
            fixedCount = fixedFiducials.GetNumberOfControlPoints() if fixedFiducials else 0
            movingCount = movingFiducials.GetNumberOfControlPoints() if movingFiducials else 0
            
            # 至少需要3对点
            hasEnoughPoints = (fixedCount >= 3 and movingCount >= 3 and fixedCount == movingCount)
            
            # 更新配准按钮状态
            self.registerButton.enabled = hasFixed and hasMoving and hasEnoughPoints
            
            # 更新状态标签
            if not hasFixed or not hasMoving:
                self.crStatusLabel.text = "状态: 请选择 Fixed 和 Moving Volume"
                self.crStatusLabel.setStyleSheet("color: orange;")
            elif fixedCount < 3 or movingCount < 3:
                self.crStatusLabel.text = f"状态: 基准点不足 (需要至少3对，当前{min(fixedCount, movingCount)}对)"
                self.crStatusLabel.setStyleSheet("color: orange;")
            elif fixedCount != movingCount:
                self.crStatusLabel.text = f"状态: 基准点数量不匹配 (Fixed:{fixedCount}, Moving:{movingCount})"
                self.crStatusLabel.setStyleSheet("color: red;")
            elif hasEnoughPoints:
                self.crStatusLabel.text = f"状态: 准备就绪，可以计算粗配准 ({fixedCount}对基准点)"
                self.crStatusLabel.setStyleSheet("color: green;")
            
        except Exception as e:
            self.logCallback(f"更新按钮状态失败: {str(e)}")

    def onRegister(self):
        """执行粗配准"""
        try:
            fixedVolume = self.crFixedVolumeSelector.currentNode()
            movingVolume = self.crMovingVolumeSelector.currentNode()
            fixedFiducials = self.crFixedFiducialsSelector.currentNode()
            movingFiducials = self.crMovingFiducialsSelector.currentNode()

            if not fixedVolume or not movingVolume:
                self.showError("请选择 Fixed 和 Moving Volume")
                return

            if not fixedFiducials or not movingFiducials:
                self.showError("请选择基准点")
                return

            fixedCount = fixedFiducials.GetNumberOfControlPoints()
            movingCount = movingFiducials.GetNumberOfControlPoints()

            if fixedCount < 3 or movingCount < 3:
                self.showError(f"至少需要3对基准点 (当前{min(fixedCount, movingCount)}对)")
                return

            if fixedCount != movingCount:
                self.showError(f"基准点数量不匹配 (Fixed:{fixedCount}, Moving:{movingCount})")
                return

            self.logCallback(f"===== 开始粗配准 =====")
            self.logCallback(f"使用{fixedCount}对基准点计算相似变换...")
            self.logCallback(f"注意: Moving 点将配准到对应的 Fixed 点")

            # 计算相似变换 (从 Moving 到 Fixed)
            self.transformNode = self.logic.computeSimilarityTransform(
                fixedFiducials, 
                movingFiducials
            )

            if self.transformNode:
                self.logCallback(f"✓ 粗配准计算成功")
                self.crStatusLabel.text = f"状态: 粗配准完成"
                self.crStatusLabel.setStyleSheet("color: green;")

                # 启用保存按钮
                self.saveResultButton.enabled = True

                qt.QMessageBox.information(
                    None,
                    "粗配准完成",
                    f"粗配准计算成功！\n\n"
                    f"基准点对数量: {fixedCount}\n\n"
                    f"请点击\"保存粗配准结果到场景\"按钮保存结果。"
                )
            else:
                self.showError("粗配准计算失败")

        except Exception as e:
            self.showError(f"粗配准失败: {str(e)}")

    def onSaveResult(self):
        """保存粗配准结果到场景"""
        try:
            if not hasattr(self, 'transformNode') or not self.transformNode:
                self.showError("请先执行粗配准")
                return

            fixedVolume = self.crFixedVolumeSelector.currentNode()
            movingVolume = self.crMovingVolumeSelector.currentNode()
            fixedFiducials = self.crFixedFiducialsSelector.currentNode()
            movingFiducials = self.crMovingFiducialsSelector.currentNode()

            # 获取文件夹名称
            mainFolderName = self.getMainFolderNameCallback()
            moduleFolderName = self.crModuleFolderNameEdit.text

            if not mainFolderName or not moduleFolderName:
                self.showError("请输入文件夹名称")
                return

            self.logCallback(f"正在保存粗配准结果到场景...")
            self.logCallback(f"  总文件夹: {mainFolderName}")
            self.logCallback(f"  Coarse Registration 子文件夹: {moduleFolderName}")

            # 调用 Logic 保存粗配准结果
            success = self.logic.saveCoarseRegistrationToScene(
                fixedVolume, movingVolume, self.transformNode,
                fixedFiducials, movingFiducials,
                mainFolderName, moduleFolderName
            )

            if success:
                self.logCallback(f"✓ 粗配准结果已保存到场景文件夹")
                self.logCallback(f"  路径: {mainFolderName}/{moduleFolderName}")
                self.crStatusLabel.text = "状态: 粗配准结果已保存"
                self.crStatusLabel.setStyleSheet("color: green;")

                qt.QMessageBox.information(
                    None,
                    "保存成功",
                    f"粗配准结果已成功保存到场景文件夹:\n"
                    f"{mainFolderName}/{moduleFolderName}\n\n"
                    f"包含内容:\n"
                    f"- CoarseReg_Moving (粗配准后的浮动图像)\n"
                    f"- CoarseReg_Transform (相似变换矩阵)\n"
                    f"- CoarseReg_Fixed_Fiducials (基准点)\n"
                    f"- CoarseReg_Moving_Fiducials (基准点)"
                )
            else:
                self.showError("保存粗配准结果失败")

        except Exception as e:
            self.showError(f"保存粗配准结果失败: {str(e)}")

    def showError(self, errorMessage):
        """显示错误信息"""
        self.logCallback(f"✗ 错误: {errorMessage}")
        self.crStatusLabel.text = f"状态: 错误"
        self.crStatusLabel.setStyleSheet("color: red;")
        slicer.util.errorDisplay(errorMessage)
        import traceback
        self.logCallback(traceback.format_exc())
