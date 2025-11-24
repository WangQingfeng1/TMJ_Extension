"""
ROI Mask Set Widget - UI界面
"""
import qt
import ctk
import slicer
from .roi_mask_set_logic import ROIMaskSetLogic


class ROIMaskSetWidget:
    """
    ROI Mask Set 的UI组件类
    负责基于高分辨率ROI浮动图像生成固定图像的掩膜
    """

    def __init__(self, parent, logCallback, getMainFolderNameCallback):
        """
        初始化 ROI Mask Set Widget
        
        :param parent: 父布局
        :param logCallback: 日志回调函数
        :param getMainFolderNameCallback: 获取主文件夹名称的回调函数
        """
        self.parent = parent
        self.logCallback = logCallback
        self.getMainFolderNameCallback = getMainFolderNameCallback
        self.logic = ROIMaskSetLogic(logCallback=logCallback)
        
        # UI 组件引用
        self.roiFixedVolumeSelector = None
        self.roiMovingVolumeSelector = None
        self.expansionSlider = None
        self.generateMaskButton = None
        self.saveResultButton = None
        self.roiStatusLabel = None
        self.roiModuleFolderNameEdit = None
        
        # 生成的掩膜节点
        self.maskVolume = None
        
        self.setupUI()

    def setupUI(self):
        """设置 ROI Mask Set 的UI界面"""
        # ROI Mask Set 模块
        roiMaskCollapsibleButton = ctk.ctkCollapsibleButton()
        roiMaskCollapsibleButton.text = "ROI Mask Set"
        roiMaskCollapsibleButton.collapsed = False
        self.parent.addWidget(roiMaskCollapsibleButton)
        roiMaskFormLayout = qt.QFormLayout(roiMaskCollapsibleButton)

        # 模块说明
        descLabel = qt.QLabel(
            "本模块用于生成颞下颌关节ROI区域的掩膜，用于后续精细配准。\n"
            "策略：基于高分辨率ROI Moving Volume的物理范围自动生成Fixed Volume的掩膜。\n"
            "提示：请从Data Manager场景文件夹中选择已添加的ROI高分辨率MRI图像。"
        )
        descLabel.setWordWrap(True)
        descLabel.setStyleSheet("color: #2E86AB; margin: 5px 0px; padding: 5px; background-color: #E8F4F8;")
        roiMaskFormLayout.addRow(descLabel)

        # 选择数据
        selectLabel = qt.QLabel("选择配准数据:")
        selectLabel.setStyleSheet("font-weight: bold; margin-top: 10px;")
        roiMaskFormLayout.addRow(selectLabel)

        # Fixed Volume 选择器
        self.roiFixedVolumeSelector = slicer.qMRMLNodeComboBox()
        self.roiFixedVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.roiFixedVolumeSelector.selectNodeUponCreation = False
        self.roiFixedVolumeSelector.addEnabled = False
        self.roiFixedVolumeSelector.removeEnabled = False
        self.roiFixedVolumeSelector.noneEnabled = True
        self.roiFixedVolumeSelector.showHidden = False
        self.roiFixedVolumeSelector.setMRMLScene(slicer.mrmlScene)
        self.roiFixedVolumeSelector.setToolTip("选择 Fixed Volume (CBCT)，通常从Data Manager文件夹选择")
        roiMaskFormLayout.addRow("Fixed Volume (CBCT): ", self.roiFixedVolumeSelector)

        # ROI Moving Volume 选择器
        self.roiMovingVolumeSelector = slicer.qMRMLNodeComboBox()
        self.roiMovingVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.roiMovingVolumeSelector.selectNodeUponCreation = False
        self.roiMovingVolumeSelector.addEnabled = False
        self.roiMovingVolumeSelector.removeEnabled = False
        self.roiMovingVolumeSelector.noneEnabled = True
        self.roiMovingVolumeSelector.showHidden = False
        self.roiMovingVolumeSelector.setMRMLScene(slicer.mrmlScene)
        self.roiMovingVolumeSelector.setToolTip(
            "选择高分辨率的 ROI Moving Volume (局部MRI)\n"
            "如：ROI_Right_Sagittal、ROI_Left_Sagittal、ROI_Right_Coronal、ROI_Left_Coronal"
        )
        roiMaskFormLayout.addRow("ROI Moving Volume (局部MRI): ", self.roiMovingVolumeSelector)

        # 重要提示
        warningLabel = qt.QLabel(
            "⚠️ 重要提示：请先对ROI Moving Volume应用粗配准产生的变换！"
        )
        warningLabel.setWordWrap(True)
        warningLabel.setStyleSheet(
            "color: #D32F2F; font-weight: bold; margin: 10px 0px; "
            "padding: 8px; background-color: #FFEBEE; border-left: 4px solid #D32F2F;"
        )
        roiMaskFormLayout.addRow(warningLabel)

        # 掩膜参数设置
        paramLabel = qt.QLabel("掩膜参数设置:")
        paramLabel.setStyleSheet("font-weight: bold; margin-top: 10px;")
        roiMaskFormLayout.addRow(paramLabel)

        # 膨胀量滑块
        expansionLayout = qt.QHBoxLayout()
        
        expansionLabel = qt.QLabel("膨胀量 (mm):")
        expansionLayout.addWidget(expansionLabel)
        
        self.expansionSlider = ctk.ctkSliderWidget()
        self.expansionSlider.minimum = 0
        self.expansionSlider.maximum = 30
        self.expansionSlider.value = 10
        self.expansionSlider.singleStep = 1
        self.expansionSlider.setToolTip(
            "掩膜膨胀量，防止ROI范围太死。\n"
            "建议值：10-20mm（因为是基于粗配准生成掩膜）"
        )
        expansionLayout.addWidget(self.expansionSlider)
        
        roiMaskFormLayout.addRow(expansionLayout)

        # 生成掩膜按钮
        generateLabel = qt.QLabel("生成ROI掩膜:")
        generateLabel.setStyleSheet("font-weight: bold; margin-top: 10px;")
        roiMaskFormLayout.addRow(generateLabel)

        self.generateMaskButton = qt.QPushButton("生成ROI掩膜")
        self.generateMaskButton.toolTip = "基于ROI Moving Volume的物理范围自动生成掩膜"
        self.generateMaskButton.enabled = False
        self.generateMaskButton.connect('clicked(bool)', self.onGenerateMask)
        roiMaskFormLayout.addRow(self.generateMaskButton)

        # 保存结果
        saveLabel = qt.QLabel("保存ROI掩膜结果:")
        saveLabel.setStyleSheet("font-weight: bold; margin-top: 10px;")
        roiMaskFormLayout.addRow(saveLabel)

        # ROI Mask Set 子文件夹名称
        self.roiModuleFolderNameEdit = qt.QLineEdit()
        self.roiModuleFolderNameEdit.text = "ROI Mask Set"
        self.roiModuleFolderNameEdit.setToolTip("ROI Mask Set 模块在总场景文件夹下的子文件夹名称")
        roiMaskFormLayout.addRow("ROI Mask Set场景子文件夹:", self.roiModuleFolderNameEdit)

        self.saveResultButton = qt.QPushButton("保存ROI掩膜结果到场景")
        self.saveResultButton.toolTip = "将掩膜和相关数据保存到场景文件夹"
        self.saveResultButton.enabled = False
        self.saveResultButton.connect('clicked(bool)', self.onSaveResult)
        roiMaskFormLayout.addRow(self.saveResultButton)

        # 状态信息
        self.roiStatusLabel = qt.QLabel("状态: 等待选择数据")
        self.roiStatusLabel.setStyleSheet("color: gray;")
        roiMaskFormLayout.addRow(self.roiStatusLabel)

        # 添加模块末尾分隔线
        separator = qt.QFrame()
        separator.setFrameShape(qt.QFrame.HLine)
        separator.setFrameShadow(qt.QFrame.Plain)
        separator.setLineWidth(2)
        separator.setMidLineWidth(0)
        separator.setStyleSheet("QFrame { background-color: #000000; max-height: 2px; margin: 15px 0px; }")
        roiMaskFormLayout.addRow(separator)

        # 连接信号
        self.roiFixedVolumeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateButtonStates)
        self.roiMovingVolumeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateButtonStates)

    def updateButtonStates(self):
        """更新按钮状态"""
        try:
            hasFixed = self.roiFixedVolumeSelector.currentNode() is not None
            hasROIMoving = self.roiMovingVolumeSelector.currentNode() is not None
            
            # 生成掩膜按钮需要两个数据都选中
            self.generateMaskButton.enabled = hasFixed and hasROIMoving
            
            # 更新状态标签
            if not hasFixed or not hasROIMoving:
                self.roiStatusLabel.text = "状态: 请选择 Fixed Volume 和 ROI Moving Volume"
                self.roiStatusLabel.setStyleSheet("color: orange;")
            else:
                self.roiStatusLabel.text = "状态: 准备就绪，可以生成掩膜"
                self.roiStatusLabel.setStyleSheet("color: green;")
            
        except Exception as e:
            self.logCallback(f"更新按钮状态失败: {str(e)}")

    def onGenerateMask(self):
        """生成ROI掩膜"""
        try:
            fixedVolume = self.roiFixedVolumeSelector.currentNode()
            roiMovingVolume = self.roiMovingVolumeSelector.currentNode()
            expansionMm = self.expansionSlider.value

            if not fixedVolume or not roiMovingVolume:
                self.showError("请选择 Fixed Volume 和 ROI Moving Volume")
                return

            # 再次提醒用户应用变换
            reply = qt.QMessageBox.question(
                None,
                "确认",
                "请确认您已经对 ROI Moving Volume 应用了粗配准产生的变换。\n\n"
                "如果还没有应用变换，请先在 Transforms 模块中应用变换，\n"
                "然后再生成掩膜。\n\n"
                "是否继续生成掩膜？",
                qt.QMessageBox.Yes | qt.QMessageBox.No
            )

            if reply != qt.QMessageBox.Yes:
                self.logCallback("用户取消了掩膜生成")
                return

            self.logCallback(f"===== 开始生成 ROI 掩膜 =====")
            self.roiStatusLabel.text = "状态: 正在生成掩膜..."
            self.roiStatusLabel.setStyleSheet("color: blue;")

            # 调用Logic生成掩膜
            self.maskVolume = self.logic.generateROIMask(
                fixedVolume, 
                roiMovingVolume, 
                expansionMm
            )

            if self.maskVolume:
                self.logCallback(f"✓ ROI掩膜生成完成")
                self.roiStatusLabel.text = "状态: 掩膜生成成功"
                self.roiStatusLabel.setStyleSheet("color: green;")

                # 启用保存按钮
                self.saveResultButton.enabled = True

                qt.QMessageBox.information(
                    None,
                    "掩膜生成完成",
                    f"ROI掩膜已成功生成！\n\n"
                    f"掩膜节点: {self.maskVolume.GetName()}\n"
                    f"膨胀量: {expansionMm} mm\n\n"
                    f"掩膜已在场景中显示（红色半透明）。\n"
                    f"请点击\"保存ROI掩膜结果到场景\"按钮保存结果。"
                )
            else:
                self.showError("掩膜生成失败")

        except Exception as e:
            self.showError(f"生成掩膜失败: {str(e)}")

    def onSaveResult(self):
        """保存ROI掩膜结果到场景"""
        try:
            if not self.maskVolume:
                self.showError("请先生成掩膜")
                return

            fixedVolume = self.roiFixedVolumeSelector.currentNode()
            roiMovingVolume = self.roiMovingVolumeSelector.currentNode()

            # 获取文件夹名称
            mainFolderName = self.getMainFolderNameCallback()
            moduleFolderName = self.roiModuleFolderNameEdit.text

            if not mainFolderName or not moduleFolderName:
                self.showError("请输入文件夹名称")
                return

            self.logCallback(f"正在保存 ROI 掩膜结果到场景...")
            self.logCallback(f"  总文件夹: {mainFolderName}")
            self.logCallback(f"  ROI Mask Set 子文件夹: {moduleFolderName}")

            # 调用 Logic 保存结果
            success = self.logic.saveROIMaskToScene(
                fixedVolume, roiMovingVolume, self.maskVolume,
                mainFolderName, moduleFolderName
            )

            if success:
                self.logCallback(f"✓ ROI掩膜结果已保存到场景文件夹")
                self.logCallback(f"  路径: {mainFolderName}/{moduleFolderName}")
                self.roiStatusLabel.text = "状态: 结果已保存"
                self.roiStatusLabel.setStyleSheet("color: green;")

                qt.QMessageBox.information(
                    None,
                    "保存成功",
                    f"ROI掩膜结果已成功保存到场景文件夹:\n"
                    f"{mainFolderName}/{moduleFolderName}\n\n"
                    f"包含内容:\n"
                    f"- ROIMask_Fixed_Volume.nrrd (固定图像)\n"
                    f"- ROIMask_ROI_Moving_Volume.nrrd (ROI浮动图像)\n"
                    f"- ROI_Mask.nrrd (生成的掩膜)"
                )
            else:
                self.showError("保存结果失败")

        except Exception as e:
            self.showError(f"保存结果失败: {str(e)}")

    def showError(self, errorMessage):
        """显示错误信息"""
        self.logCallback(f"✗ 错误: {errorMessage}")
        self.roiStatusLabel.text = f"状态: 错误"
        self.roiStatusLabel.setStyleSheet("color: red;")
        slicer.util.errorDisplay(errorMessage)
        import traceback
        self.logCallback(traceback.format_exc())
