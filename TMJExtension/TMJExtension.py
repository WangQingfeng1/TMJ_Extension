"""
TMJ Extension - 主入口文件（模块化版本）
将代码拆分为 Data Manager 和 Gold Standard Set 两个独立模块
"""
import os
import sys
import unittest
import logging
import vtk, qt, ctk, slicer
from datetime import datetime
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

# 确保子模块路径在 sys.path 中
_module_dir = os.path.dirname(os.path.abspath(__file__))
if _module_dir not in sys.path:
    sys.path.insert(0, _module_dir)

# 导入模块化组件
from DataManager.data_manager_widget import DataManagerWidget
from DataManager.data_manager_logic import DataManagerLogic
from GoldStandardSet.gold_standard_widget import GoldStandardWidget
from GoldStandardSet.gold_standard_logic import GoldStandardLogic


#
# TMJExtension
#

class TMJExtension(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class"""

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "TMJ Extension"
        self.parent.categories = ["TMJ Analysis"]
        self.parent.dependencies = []
        self.parent.contributors = ["Feng"]
        self.parent.helpText = """
这是一个用于TMJ(颞下颌关节)分析的3D Slicer插件。
Data Manager 模块用于导入、管理和导出医学影像数据，保留原始 HU/强度信息。
Gold Standard Set 模块用于手动配准和金标准设置。
"""
        self.parent.acknowledgementText = """
This module was developed for TMJ research.
"""


#
# TMJExtensionWidget
#

class TMJExtensionWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """主界面Widget类 - 组合各个模块的UI"""

    def __init__(self, parent=None):
        """初始化主Widget"""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)
        
        # 子模块引用
        self.dataManagerWidget = None
        self.goldStandardWidget = None

    def setup(self):
        """设置主界面"""
        ScriptedLoadableModuleWidget.setup(self)

        # 创建 Data Manager 模块
        self.dataManagerWidget = DataManagerWidget(
            parent=self.layout,
            logCallback=self.addLog
        )

        # 创建 Gold Standard Set 模块
        self.goldStandardWidget = GoldStandardWidget(
            parent=self.layout,
            logCallback=self.addLog,
            getMainFolderNameCallback=self.dataManagerWidget.getMainFolderName
        )

        # 日志区域
        self.setupLogArea()

        # 添加垂直间距
        self.layout.addStretch(1)

    def setupLogArea(self):
        """设置日志区域"""
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

    def cleanup(self):
        """清理资源"""
        self.removeObservers()


#
# TMJExtensionLogic
#

class TMJExtensionLogic(ScriptedLoadableModuleLogic):
    """
    主Logic类 - 现在主要作为模块的容器
    实际的业务逻辑在各个子模块的Logic类中
    """

    def __init__(self):
        """初始化Logic"""
        ScriptedLoadableModuleLogic.__init__(self)
        self.dataManagerLogic = DataManagerLogic()
        self.goldStandardLogic = GoldStandardLogic()


#
# TMJExtensionTest
#

class TMJExtensionTest(ScriptedLoadableModuleTest):
    """测试用例类"""

    def setUp(self):
        """重置状态"""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """运行测试"""
        self.setUp()
        self.test_TMJExtension1()

    def test_TMJExtension1(self):
        """基础测试"""
        self.delayDisplay("Starting the test")
        # TODO: 添加测试代码
        self.delayDisplay('Test passed')
