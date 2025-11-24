"""
ROI Mask Set Logic - 业务逻辑处理
基于高分辨率浮动图像的物理范围自动生成固定图像的ROI掩膜
"""
import vtk
import slicer
import os
import numpy as np


class ROIMaskSetLogic:
    """
    ROI Mask Set 的业务逻辑类
    负责根据浮动图像的物理范围生成固定图像的ROI掩膜
    """

    def __init__(self, logCallback=None):
        """
        初始化 ROI Mask Set Logic
        
        :param logCallback: 日志回调函数
        """
        self.logCallback = logCallback if logCallback else print

    def generateROIMask(self, fixedVolume, roiMovingVolume, expansionMm=10.0):
        """
        基于ROI Moving Volume的物理范围自动生成Fixed Volume的ROI掩膜
        
        :param fixedVolume: 固定图像 (CBCT)
        :param roiMovingVolume: 高分辨率ROI浮动图像 (局部MRI)
        :param expansionMm: 掩膜膨胀量(毫米)，默认10mm
        :return: 生成的掩膜节点
        """
        try:
            if not fixedVolume or not roiMovingVolume:
                raise ValueError("Fixed Volume 和 ROI Moving Volume 都不能为空")

            self.logCallback(f"开始生成 ROI 掩膜...")
            self.logCallback(f"  Fixed Volume: {fixedVolume.GetName()}")
            self.logCallback(f"  ROI Moving Volume: {roiMovingVolume.GetName()}")
            self.logCallback(f"  膨胀量: {expansionMm} mm")

            # 获取ROI Moving Volume的物理边界框
            bounds = [0] * 6
            roiMovingVolume.GetBounds(bounds)
            self.logCallback(f"  ROI Moving Volume 物理范围:")
            self.logCallback(f"    X: [{bounds[0]:.2f}, {bounds[1]:.2f}] mm")
            self.logCallback(f"    Y: [{bounds[2]:.2f}, {bounds[3]:.2f}] mm")
            self.logCallback(f"    Z: [{bounds[4]:.2f}, {bounds[5]:.2f}] mm")

            # 应用膨胀
            expandedBounds = [
                bounds[0] - expansionMm,
                bounds[1] + expansionMm,
                bounds[2] - expansionMm,
                bounds[3] + expansionMm,
                bounds[4] - expansionMm,
                bounds[5] + expansionMm
            ]
            self.logCallback(f"  膨胀后的范围:")
            self.logCallback(f"    X: [{expandedBounds[0]:.2f}, {expandedBounds[1]:.2f}] mm")
            self.logCallback(f"    Y: [{expandedBounds[2]:.2f}, {expandedBounds[3]:.2f}] mm")
            self.logCallback(f"    Z: [{expandedBounds[4]:.2f}, {expandedBounds[5]:.2f}] mm")

            # 创建掩膜体积（基于固定图像的几何信息）
            maskVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", "ROI_Mask")
            
            # 获取固定图像的几何信息
            fixedImageData = fixedVolume.GetImageData()
            fixedSpacing = fixedVolume.GetSpacing()
            fixedOrigin = fixedVolume.GetOrigin()
            fixedDimensions = fixedImageData.GetDimensions()
            
            self.logCallback(f"  Fixed Volume 信息:")
            self.logCallback(f"    尺寸: {fixedDimensions}")
            self.logCallback(f"    间距: {fixedSpacing}")
            self.logCallback(f"    原点: {fixedOrigin}")

            # 创建与固定图像相同几何的掩膜图像
            maskImageData = vtk.vtkImageData()
            maskImageData.SetDimensions(fixedDimensions)
            maskImageData.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 1)
            maskImageData.GetPointData().GetScalars().Fill(0)  # 初始化为0

            # 获取RAS到IJK的转换矩阵
            rasToIjkMatrix = vtk.vtkMatrix4x4()
            fixedVolume.GetRASToIJKMatrix(rasToIjkMatrix)

            # 遍历固定图像的所有体素，判断是否在ROI范围内
            self.logCallback(f"  正在计算掩膜...")
            voxelCount = 0
            totalVoxels = fixedDimensions[0] * fixedDimensions[1] * fixedDimensions[2]
            
            # 使用numpy加速计算
            maskArray = slicer.util.arrayFromVolume(maskVolume)
            if maskArray is None:
                # 如果无法获取numpy数组，手动创建
                maskArray = np.zeros(fixedDimensions[::-1], dtype=np.uint8)  # 注意维度顺序
            
            # 遍历所有体素
            for k in range(fixedDimensions[2]):
                for j in range(fixedDimensions[1]):
                    for i in range(fixedDimensions[0]):
                        # IJK坐标转换为RAS坐标
                        ijkPoint = [i, j, k, 1]
                        rasPoint = [0, 0, 0, 1]
                        fixedVolume.GetIJKToRASMatrix().MultiplyPoint(ijkPoint, rasPoint)
                        
                        # 判断RAS坐标是否在膨胀后的边界框内
                        if (expandedBounds[0] <= rasPoint[0] <= expandedBounds[1] and
                            expandedBounds[2] <= rasPoint[1] <= expandedBounds[3] and
                            expandedBounds[4] <= rasPoint[2] <= expandedBounds[5]):
                            maskArray[k, j, i] = 255  # 在ROI内，设为255
                            voxelCount += 1

            # 将numpy数组写回体积
            slicer.util.updateVolumeFromArray(maskVolume, maskArray)
            
            # 复制固定图像的几何信息到掩膜
            maskVolume.CopyOrientation(fixedVolume)
            
            # 设置掩膜的显示属性
            displayNode = maskVolume.GetDisplayNode()
            if not displayNode:
                displayNode = slicer.vtkMRMLScalarVolumeDisplayNode()
                slicer.mrmlScene.AddNode(displayNode)
                maskVolume.SetAndObserveDisplayNodeID(displayNode.GetID())
            
            # 设置为红色半透明显示
            displayNode.SetAndObserveColorNodeID("vtkMRMLColorTableNodeRed")
            displayNode.SetOpacity(0.3)

            maskPercentage = (voxelCount / totalVoxels) * 100
            self.logCallback(f"✓ ROI掩膜生成成功")
            self.logCallback(f"  掩膜体素数: {voxelCount} / {totalVoxels} ({maskPercentage:.2f}%)")

            return maskVolume

        except Exception as e:
            self.logCallback(f"✗ 生成ROI掩膜失败: {str(e)}")
            import traceback
            self.logCallback(traceback.format_exc())
            return None

    def saveROIMaskToScene(self, fixedVolume, roiMovingVolume, maskVolume, 
                           mainFolderName, moduleFolderName):
        """
        保存ROI掩膜结果到场景文件夹
        
        :param fixedVolume: 固定图像
        :param roiMovingVolume: ROI浮动图像
        :param maskVolume: 生成的掩膜
        :param mainFolderName: 主文件夹名称
        :param moduleFolderName: 模块子文件夹名称
        :return: 是否保存成功
        """
        try:
            # 获取或创建场景保存目录
            sceneSaveDirectory = slicer.app.defaultScenePath
            if not sceneSaveDirectory:
                import tempfile
                sceneSaveDirectory = tempfile.gettempdir()

            # 创建完整路径
            fullPath = os.path.join(sceneSaveDirectory, mainFolderName, moduleFolderName)
            if not os.path.exists(fullPath):
                os.makedirs(fullPath)

            self.logCallback(f"保存路径: {fullPath}")

            # 保存Fixed Volume（参考）
            fixedPath = os.path.join(fullPath, "ROIMask_Fixed_Volume.nrrd")
            slicer.util.saveNode(fixedVolume, fixedPath)
            self.logCallback(f"✓ Fixed Volume 已保存: {fixedPath}")

            # 保存ROI Moving Volume（参考）
            roiMovingPath = os.path.join(fullPath, "ROIMask_ROI_Moving_Volume.nrrd")
            slicer.util.saveNode(roiMovingVolume, roiMovingPath)
            self.logCallback(f"✓ ROI Moving Volume 已保存: {roiMovingPath}")

            # 保存掩膜
            maskPath = os.path.join(fullPath, "ROI_Mask.nrrd")
            slicer.util.saveNode(maskVolume, maskPath)
            self.logCallback(f"✓ ROI掩膜已保存: {maskPath}")

            self.logCallback(f"✓ ROI Mask Set 结果已全部保存到场景文件夹")
            return True

        except Exception as e:
            self.logCallback(f"✗ 保存ROI掩膜失败: {str(e)}")
            import traceback
            self.logCallback(traceback.format_exc())
            return False
