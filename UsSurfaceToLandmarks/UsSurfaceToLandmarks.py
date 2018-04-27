import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np

#
# UsSurfaceToLandmarks
#

class UsSurfaceToLandmarks(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "US Surface To Landmarks"
    self.parent.categories = ["Scoliosis"]
    self.parent.dependencies = []
    self.parent.contributors = ["Ben Church (PerkLab - Queen's University)"]
    self.parent.helpText = "This module takes volumes loaded from the mha output of US image bone enhancement program"
    
    #self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """ """ 

#
# UsSurfaceToLandmarksWidget
#

class UsSurfaceToLandmarksWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    #
    # Node operation tags
    #
    self.ThresholdTag = "_Th"
    self.SmoothTag = "_Sm"
    self.MarkupsTag = "_Mu"
    
    # Instantiate and connect widgets ...

    #
    # Data selection area
    #
    self.DataInterface = ctk.ctkCollapsibleButton()
    self.DataInterface.text = "Data"
    self.layout.addWidget(self.DataInterface)

    # Layout within the dummy collapsible button
    self.DataInterfaceGridLayout = qt.QGridLayout(self.DataInterface)

    self.DataInterfaceGridLayout.setVerticalSpacing(12)
    
    #
    # Embedded config area
    #
    self.DataConfigInterface = ctk.ctkCollapsibleButton()
    self.DataConfigInterface.text = "Config"
    self.DataConfigInterface.collapsed = True
    self.DataConfigInterface.enabled = True
    self.DataInterfaceGridLayout.addWidget(self.DataConfigInterface, 0, 0, 1, 4)
    
    self.DataConfigInterfaceGridLayout = qt.QGridLayout(self.DataConfigInterface)
    self.DataConfigInterfaceGridLayout.setVerticalSpacing(12)
    
    # Input volume voxel threshold slider
    self.VolumeThresholdSlider = ctk.ctkSliderWidget()
    self.VolumeThresholdSlider.singleStep = 0.1
    self.VolumeThresholdSlider.minimum = 0
    self.VolumeThresholdSlider.maximum = 30
    self.VolumeThresholdSlider.value = 3.3
    self.VolumeThresholdSlider.setToolTip("Set threshold value applied to ultrasound scan volume before conversion to label map.")
    self.DataConfigInterfaceGridLayout.addWidget(qt.QLabel("Image threshold"), 0, 0, 1, 1)
    self.DataConfigInterfaceGridLayout.addWidget(self.VolumeThresholdSlider, 0, 1, 1, 3)
    
    # Erosion kernel size spin boxes
    
    self.DataConfigInterfaceGridLayout.addWidget(qt.QLabel('R-L'), 1, 1, 1, 1)
    self.DataConfigInterfaceGridLayout.addWidget(qt.QLabel('A-P'), 1, 2, 1, 1)
    self.DataConfigInterfaceGridLayout.addWidget(qt.QLabel('S-I'), 1, 3, 1, 1)
    
    self.DataConfigInterfaceGridLayout.addWidget(qt.QLabel("Erosion kernel size"), 2, 0, 1, 1)
    self.RlErodeKsSpinBox = qt.QSpinBox()
    self.RlErodeKsSpinBox.enabled = True
    self.RlErodeKsSpinBox.setSingleStep(1)
    self.RlErodeKsSpinBox.setRange(0,10)
    self.RlErodeKsSpinBox.value = 2
    self.RlErodeKsSpinBox.setToolTip("Kernel size in R-L direction")
    self.DataConfigInterfaceGridLayout.addWidget(self.RlErodeKsSpinBox, 2, 1, 1, 1)
    
    self.ApErodeKsSpinBox = qt.QSpinBox()
    self.ApErodeKsSpinBox.enabled = True
    self.ApErodeKsSpinBox.setSingleStep(1)
    self.ApErodeKsSpinBox.setRange(0,10)
    self.ApErodeKsSpinBox.value = 1
    self.ApErodeKsSpinBox.setToolTip("Kernel size in A-P direction")
    self.DataConfigInterfaceGridLayout.addWidget(self.ApErodeKsSpinBox, 2, 2, 1, 1)
    
    self.SiErodeKsSpinBox = qt.QSpinBox()
    self.SiErodeKsSpinBox.enabled = True
    self.SiErodeKsSpinBox.setSingleStep(1)
    self.SiErodeKsSpinBox.setRange(0,10)
    self.SiErodeKsSpinBox.value = 2
    self.SiErodeKsSpinBox.setToolTip("Kernel size in S-I direction")
    self.DataConfigInterfaceGridLayout.addWidget(self.SiErodeKsSpinBox, 2, 3, 1, 1)
    
    # Island removal threshold size slider
    self.IslandSizeThresholdSlider = ctk.ctkSliderWidget()
    ThreshSizeSpinBox = self.IslandSizeThresholdSlider.SpinBox
    ThreshSizeSpinBox.setDecimals(0)
    self.IslandSizeThresholdSlider.singleStep = 1
    self.IslandSizeThresholdSlider.minimum = 0
    self.IslandSizeThresholdSlider.maximum = 1000
    self.IslandSizeThresholdSlider.value = 100
    self.IslandSizeThresholdSlider.setToolTip("Set the threshold of the smallest size of island to be retained in island removal")
    self.DataConfigInterfaceGridLayout.addWidget(qt.QLabel("Island size threshold"), 3, 0, 1, 1)
    self.DataConfigInterfaceGridLayout.addWidget(self.IslandSizeThresholdSlider, 3, 1, 1, 3)
    
    
    # Smoothing convergence slider
    self.SmoothingConvergenceSlider = ctk.ctkSliderWidget()
    SmthConvgSpinBox = self.SmoothingConvergenceSlider.SpinBox
    SmthConvgSpinBox.setDecimals(4)
    self.SmoothingConvergenceSlider.singleStep = 0.0001
    self.SmoothingConvergenceSlider.minimum = 0.0001
    self.SmoothingConvergenceSlider.maximum = 1.0
    self.SmoothingConvergenceSlider.value = 0.1
    self.SmoothingConvergenceSlider.setToolTip("Set the minimum point adjustment size which must be exceeded to continue smoothing")
    self.DataConfigInterfaceGridLayout.addWidget(qt.QLabel("Smoothing convergence threshold"), 4, 0, 1, 1)
    self.DataConfigInterfaceGridLayout.addWidget(self.SmoothingConvergenceSlider, 4, 1, 1, 3)
    
    # Number of smoothing iterations slider
    self.SmoothingIterationsSlider = ctk.ctkSliderWidget()
    SmthIterSpinBox = self.SmoothingIterationsSlider.SpinBox
    SmthIterSpinBox.setDecimals(0)
    self.SmoothingIterationsSlider.singleStep = 1
    self.SmoothingIterationsSlider.minimum = 0
    self.SmoothingIterationsSlider.maximum = 100
    self.SmoothingIterationsSlider.value = 10
    self.SmoothingIterationsSlider.setToolTip("Set the maximum number of iterations vtkSmoothPolyDataFilter will run for")
    self.DataConfigInterfaceGridLayout.addWidget(qt.QLabel("Number of smoothing iterations"), 5, 0, 1, 1)
    self.DataConfigInterfaceGridLayout.addWidget(self.SmoothingIterationsSlider, 5, 1, 1, 3)
    
    # Undersampling fraction slider for landmark generation
    self.UndersampleFractionSlider = ctk.ctkSliderWidget()
    SmplFrcnSpinBox = self.UndersampleFractionSlider.SpinBox
    SmplFrcnSpinBox.setDecimals(3)
    self.UndersampleFractionSlider.singleStep = 0.001
    self.UndersampleFractionSlider.minimum = 0.001
    self.UndersampleFractionSlider.maximum = 1
    self.UndersampleFractionSlider.value = 0.1
    self.UndersampleFractionSlider.setToolTip("Set the fraction of original voxels to be used for kMeans landmark generation")
    self.DataConfigInterfaceGridLayout.addWidget(qt.QLabel("Undersampling fraction"), 6, 0, 1, 1)
    self.DataConfigInterfaceGridLayout.addWidget(self.UndersampleFractionSlider, 6, 1, 1, 3)
    
    #
    # Data Interface
    #
    
    # input volume selector
    self.InputVolumeSelector = slicer.qMRMLNodeComboBox()
    self.InputVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.InputVolumeSelector.selectNodeUponCreation = False
    self.InputVolumeSelector.addEnabled = False
    self.InputVolumeSelector.removeEnabled = True
    self.InputVolumeSelector.noneEnabled = True
    self.InputVolumeSelector.showHidden = False
    self.InputVolumeSelector.showChildNodeTypes = False
    self.InputVolumeSelector.setMRMLScene( slicer.mrmlScene )
    self.InputVolumeSelector.setToolTip( "Pick the input to the algorithm." )
    self.DataInterfaceGridLayout.addWidget(qt.QLabel("Input Volume: "), 1, 0, 1, 1)
    self.DataInterfaceGridLayout.addWidget(self.InputVolumeSelector, 1, 1, 1, 3)
    
    # Storage for intermediate, working label map nde
    self.WorkingLabelMapStorage = slicer.qMRMLNodeComboBox()
    self.WorkingLabelMapStorage.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.WorkingLabelMapStorage.selectNodeUponCreation = False
    self.WorkingLabelMapStorage.addEnabled = False
    self.WorkingLabelMapStorage.removeEnabled = False
    self.WorkingLabelMapStorage.noneEnabled = True
    self.WorkingLabelMapStorage.showHidden = False
    self.WorkingLabelMapStorage.showChildNodeTypes = False
    self.WorkingLabelMapStorage.setMRMLScene( slicer.mrmlScene )
    self.WorkingLabelMapStorage.setToolTip( "Stores label map node generated by module, on which processing is performed, and from which landmarks are retrieved" )
    self.DataInterfaceGridLayout.addWidget(qt.QLabel("Working Labelmap: "), 2, 0, 1, 1)
    self.DataInterfaceGridLayout.addWidget(self.WorkingLabelMapStorage, 2, 1, 1, 3)
    
    # output markups node storage
    self.OutputMarkupsStorage = slicer.qMRMLNodeComboBox()
    self.OutputMarkupsStorage.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
    self.OutputMarkupsStorage.selectNodeUponCreation = False
    self.OutputMarkupsStorage.addEnabled = False
    self.OutputMarkupsStorage.removeEnabled = True
    self.OutputMarkupsStorage.noneEnabled = True
    self.OutputMarkupsStorage.showHidden = False
    self.OutputMarkupsStorage.showChildNodeTypes = False
    self.OutputMarkupsStorage.setMRMLScene( slicer.mrmlScene )
    self.OutputMarkupsStorage.setToolTip( "Stores landmarks deduced from input US scan volume" )
    self.DataInterfaceGridLayout.addWidget(qt.QLabel("Output Landmarks: "), 3, 0, 1, 1)
    self.DataInterfaceGridLayout.addWidget(self.OutputMarkupsStorage, 3, 1, 1, 3)

    # Threshold label map from volume button
    self.ThresholdVolumeButton = qt.QPushButton("Threshold Volume")
    self.ThresholdVolumeButton.toolTip = "Extract label map from input volume node with threshold filter"
    self.ThresholdVolumeButton.enabled = False
    self.DataInterfaceGridLayout.addWidget(self.ThresholdVolumeButton, 4, 0, 1, 2)
    
    # Visualize label map button
    self.VisualizeLabelMapButton = qt.QPushButton("Visualize Labelmap")
    self.VisualizeLabelMapButton.toolTip = "Generate landmarks node from input volume."
    self.VisualizeLabelMapButton.enabled = False
    self.VisualizeLabelMapButton.setCheckable(True)
    self.DataInterfaceGridLayout.addWidget(self.VisualizeLabelMapButton, 4, 2, 1, 2)
    
    # Smooth working label map button
    self.SmoothLabelMapButton = qt.QPushButton("Smooth Labelmap")
    self.SmoothLabelMapButton.toolTip = "Apply vtkSmoothPolyDataFilter to wokring vtkPolyData derived from label map node."
    self.SmoothLabelMapButton.enabled = False
    self.DataInterfaceGridLayout.addWidget(self.SmoothLabelMapButton, 5, 0, 1, 2)
    
    # Decimate working label map button
    self.DecimateLabelMapButton = qt.QPushButton("Decimate Labelmap")
    self.DecimateLabelMapButton.toolTip = "Apply vtkDecimatePro to vtkPolyData derived from wokring label map node."
    self.DecimateLabelMapButton.enabled = False
    self.DataInterfaceGridLayout.addWidget(self.DecimateLabelMapButton, 5, 2, 1, 2)
    
    # Remove islands (coronal slicer-wise) button
    self.RemoveIslandsButton = qt.QPushButton("Remove Islands")
    self.RemoveIslandsButton.toolTip = "Apply vtkImageIslandRemoval2D to ecah coronal slice of working labelmap."
    self.RemoveIslandsButton.enabled = False
    self.DataInterfaceGridLayout.addWidget(self.RemoveIslandsButton, 6, 0, 1, 2)
    
    self.GenerateLandmarksButton = qt.QPushButton("Generate Landmarks")
    self.GenerateLandmarksButton.toolTip = "Generate landmarks node from input volume."
    self.GenerateLandmarksButton.enabled = True
    self.DataInterfaceGridLayout.addWidget(self.GenerateLandmarksButton, 7,1,1,2)
    #self.DataInterfaceGridLayout.addStretch(0)
    
    #self.InputVolumeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    #self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    
    # Data interface connections
    self.InputVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.OnInputVolumeSelectorChanged)
    self.WorkingLabelMapStorage.connect('currentNodeChanged(vtkMRMLNode*)', self.OnWorkingLabelMapStorageChanged)
    
    # US surface operation button connections
    self.ThresholdVolumeButton.connect('clicked(bool)', self.OnThresholdVolumeButtonClicked)
    self.VisualizeLabelMapButton.connect('clicked(bool)', self.OnVisualizeLabelMapButtonClicked)
    self.SmoothLabelMapButton.connect('clicked(bool)', self.OnSmoothLabelMapButtonClicked)
    self.DecimateLabelMapButton.connect('clicked(bool)', self.OnDecimateLabelMapButtonClicked)
    self.RemoveIslandsButton.connect('clicked(bool)', self.OnRemoveIslandsButtonClicked)
    
    self.GenerateLandmarksButton.connect("clicked(bool)", self.OnGenerateLandmarksButtonClicked)
    
    self.ReloadButton = qt.QPushButton("Reload Module")
    self.ReloadButton.enabled = True
    self.layout.addWidget(self.ReloadButton)
    
    self.ReloadButton.connect('clicked(bool)', self.OnReloadButtonClicked)
    
    # Add vertical spacer
    self.layout.addStretch(1)
    
  def cleanup(self):
    pass

  def OnInputVolumeSelectorChanged(self):
    
    # First, (re)initialize segmentation node to contain input and working data
    
    # Check scene for previous segmentation node, remove if present
    SegNodeName = "Seg_" + self.InputVolumeSelector.currentNode().GetName()
    OldSegNode = slicer.util.getNode(SegNodeName)
    if OldSegNode != None:
      OldSegNode.SetSelected(0)
      slicer.mrmlScene.RemoveNode(OldSegNode)
      
    # Instantiate new segmentation node
    self.SegmentationNode = slicer.vtkMRMLSegmentationNode()
    self.SegmentationNode.SetScene(slicer.mrmlScene)
    slicer.mrmlScene.AddNode(self.SegmentationNode)
    self.SegmentationNode.SetSelected(1)
    self.SegmentationNode.SetName(SegNodeName)
    
    NewInputVolumeNode = self.InputVolumeSelector.currentNode()
    
    if NewInputVolumeNode == None:
      self.ThresholdVolumeButton.enabled = False
      return True
      
    if NewInputVolumeNode.GetClassName() != 'vtkMRMLScalarVolumeNode':
      print "ERROR - Invalid node type in Input Volume combo box"
      self.ThresholdVolumeButton.enabled = False
      return False
    
    else:
    
      #self.UpdateSegmentationNode()
      
      self.ThresholdVolumeButton.enabled = True
      
  def OnWorkingLabelMapStorageChanged(self):
    
    NewLabelMapNode = self.WorkingLabelMapStorage.currentNode()
    
    if NewLabelMapNode == None:
      self.VisualizeLabelMapButton.enabled = False
      self.SmoothLabelMapButton.enabled = False
      self.DecimateLabelMapButton.enabled = False
      self.RemoveIslandsButton.enabled = False
      return True
      
    if NewLabelMapNode.GetClassName() != 'vtkMRMLLabelMapVolumeNode':
      print "ERROR - Invalid node type in Working Labelmap combo box - Internal error"
      self.VisualizeLabelMapButton.enabled = False
      self.SmoothLabelMapButton.enabled = False
      self.DecimateLabelMapButton.enabled = False
      self.RemoveIslandsButton.enabled = False
      return False
    
    else:
      self.VisualizeLabelMapButton.enabled = True
      self.SmoothLabelMapButton.enabled = True
      self.DecimateLabelMapButton.enabled = True
      self.RemoveIslandsButton.enabled = True
      return True
    
  def OnThresholdVolumeButtonClicked(self):
    InputVolumeNode = self.InputVolumeSelector.currentNode()
    
    if InputVolumeNode == None:
      print "ERROR - No input volume selected; not generating landmarks"
      return False
    
    else:  
      logic = UsSurfaceToLandmarksLogic()
      
      # Clear mrmlScene of old labelmap node before thresholding new one
      ThresholdLabelmapName = InputVolumeNode.GetName() + self.ThresholdTag
      OldLabelmapNode = slicer.util.getNode(ThresholdLabelmapName)
      if OldLabelmapNode != None:
        slicer.mrmlScene.RemoveNode(OldLabelmapNode)
      
      # Convert the mha-derived volume into a label map for supsequent editing
      LabelMapNode = logic.VolumeThresholdToLabelMap(InputVolumeNode, self.VolumeThresholdSlider.value)
      #LabelMapNode.SetOrigin(InputVolumeNode.GetOrigin())
      LabelMapNode.SetName(ThresholdLabelmapName)
      
      # Import thresholded labelmap into segmentation as "original" scan data i.e. starting point for processing
      #if self.SegmentationNode.GetNumberOfStorageNodes() > 0 and Segmentation.GetNthSegmentID(0) == ThresholdLabelmapName:
      if self.SegmentationNode.GetBinaryLabelmapRepresentation(ThresholdLabelmapName) != None:      
        self.SegmentationNode.RemoveSegment(ThresholdLabelmapName)
      
      """
      OldLabelmapNode = self.WorkingLabelMapStorage.currentNode()
      if OldLabelmapNode != None:
        slicer.mrmlScene.RemoveNode(OldLabelmapNode)
      """
        
      # Update mrmlScene and interface with newest working node
      slicer.mrmlScene.AddNode(LabelMapNode)
      self.WorkingLabelMapStorage.setCurrentNode(LabelMapNode)
      self.UpdateSegmentationNode()
      #SegLogic = slicer.modules.segmentations.logic()
      #SegLogic.ImportLabelmapToSegmentationNode(LabelMapNode, self.SegmentationNode)
      
      return True
  
  def OnVisualizeLabelMapButtonClicked(self):
    self.UpdateSegmentationNode()
    return True
  
  def OnSmoothLabelMapButtonClicked(self):
    # Get working polydata
    WorkingNodeName = self.WorkingLabelMapStorage.currentNode().GetName()
    if self.SegmentationNode.GetClosedSurfaceRepresentation(WorkingNodeName) == None:
      self.SegmentationNode.CreateClosedSurfaceRepresentation()
      
    WorkingPolyData = self.SegmentationNode.GetClosedSurfaceRepresentation(WorkingNodeName)
    
    # Smooth working polydata
    logic = UsSurfaceToLandmarksLogic()
    SmoothedPolyData = logic.SmoothPolyData(WorkingPolyData, self.SmoothingConvergenceSlider.value, self.SmoothingIterationsSlider.value)
    
    # Convert polydata to labelmap via segmentation and vtkmodel
    SmoothedModelNode = slicer.vtkMRMLModelNode()
    SmoothedModelNode.SetName(WorkingNodeName)
    SmoothedModelNode.SetAndObservePolyData(SmoothedPolyData)
    #SmoothedModelNode
    
    ConvSeg = slicer.vtkMRMLSegmentationNode()
    ConvSeg.SetScene(slicer.mrmlScene)
    SegLogic = slicer.modules.segmentations.logic()
    SegLogic.ImportModelToSegmentationNode(SmoothedModelNode, ConvSeg)
    ConvSeg.CreateBinaryLabelmapRepresentation()
    ConvSeg.SetMasterRepresentationToBinaryLabelmap()
    
    # Clear mrmlScene of old labelmap node before exporting the new one
    #OldLabelMapNode = self.WorkingLabelMapStorage.currentNode()
    #OldLabelMapNode = slicer.util.getNode(WorkingNodeName)
    #if OldLabelMapNode != None:
    #  slicer.mrmlScene.RemoveNode(OldLabelMapNode)
    
    # Export segmentation label map representation to mrml node for storage in interface
    SmoothedLabelMapNode = slicer.vtkMRMLLabelMapVolumeNode()
    SmoothedLabelMapNode.SetName(WorkingNodeName + self.SmoothTag)
    
    LabelMapName = vtk.vtkStringArray()
    LabelMapName.InsertNextValue(WorkingNodeName)
    slicer.mrmlScene.AddNode(SmoothedLabelMapNode)    
    SegLogic.ExportSegmentsToLabelmapNode(ConvSeg, LabelMapName, SmoothedLabelMapNode)
    #SmoothedLabelMapNode.SetOrigin(self.InputVolumeSelector.currentNode().GetOrigin())
    # Update working polydata in UI
    # Add new smoothed label map node to mrmlScene
    self.WorkingLabelMapStorage.setCurrentNode(SmoothedLabelMapNode)
    self.UpdateSegmentationNode()
  
    return True
    
  def OnDecimateLabelMapButtonClicked(self):
    # Get working polydata
    WorkingNodeName = self.WorkingLabelMapStorage.currentNode().GetName()
    if self.SegmentationNode.GetClosedSurfaceRepresentation(WorkingNodeName) == None:
      self.SegmentationNode.CreateClosedSurfaceRepresentation()
    WorkingPolyData = self.SegmentationNode.GetClosedSurfaceRepresentation(WorkingNodeName)
    
    # Decimate working polydata
    logic = UsSurfaceToLandmarksLogic()
    DecimatedPolyData = logic.DecimatePolyData(WorkingPolyData)
    
    # Convert polydata to labelmap via segmentation and vtkmodel
    DecimatedModelNode = slicer.vtkMRMLModelNode()
    DecimatedModelNode.SetName(WorkingNodeName)
    DecimatedModelNode.SetAndObservePolyData(DecimatedPolyData)
    
    ConvSeg = slicer.vtkMRMLSegmentationNode()
    ConvSeg.SetScene(slicer.mrmlScene)
    SegLogic = slicer.modules.segmentations.logic()
    SegLogic.ImportModelToSegmentationNode(DecimatedModelNode, ConvSeg)
    ConvSeg.CreateBinaryLabelmapRepresentation()
    ConvSeg.SetMasterRepresentationToBinaryLabelmap()
    
    LabelMapName = vtk.vtkStringArray()
    LabelMapName.InsertNextValue(WorkingNodeName)
    
    DecimatedLabelMapNode = slicer.vtkMRMLLabelMapVolumeNode()
    DecimatedLabelMapNode.SetName(WorkingNodeName)
    slicer.mrmlScene.AddNode(DecimatedLabelMapNode)
    
    SegLogic.ExportSegmentsToLabelmapNode(ConvSeg, LabelMapName, DecimatedLabelMapNode)
    #SmoothedOrientedImageData = ConvSeg.GetBinaryLabelmapRepresentation(WorkingNodeName)
    #DecimatedLabelMapNode.SetAndObserveImageData(SmoothedOrientedImageData)
    # Update working polydata in UI
    self.WorkingLabelMapStorage.setCurrentNode(DecimatedLabelMapNode)
    self.UpdateSegmentationNode()
    
    return True
  
  def OnRemoveIslandsButtonClicked(self):
    logic = UsSurfaceToLandmarksLogic()
    WorkingLabelMap = self.WorkingLabelMapStorage.currentNode()
    WorkingImageData = WorkingLabelMap.GetImageData()
    
    # Clear mrmlScene of old labelmap node before exporting the new one
    OldLabelMapNode = self.WorkingLabelMapStorage.currentNode()
    if OldLabelMapNode != None:
      slicer.mrmlScene.RemoveNode(OldLabelMapNode)
    
    print "DEBUG - About to remove islands"
    
    LabelMapIslandsRemoved = logic.RemoveCoronalIslands(WorkingImageData, self.IslandSizeThresholdSlider.value)
    LabelMapIslandsRemoved.SetName(WorkingLabelMap.GetName())
    print "DEBUG - Islands removed"
  
  
    ConvSeg = slicer.vtkMRMLSegmentationNode()
    ConvSeg.SetScene(slicer.mrmlScene)
    SegLogic = slicer.modules.segmentations.logic()
    SegLogic.ImportLabelmapToSegmentationNode(LabelMapIslandsRemoved, ConvSeg)
    ConvSeg.CreateBinaryLabelmapRepresentation()
    ConvSeg.SetMasterRepresentationToBinaryLabelmap()
    
    LabelMapName = vtk.vtkStringArray()
    LabelMapName.InsertNextValue(WorkingLabelMap.GetName())
    DeislandedLabelMapNode = slicer.vtkMRMLLabelMapVolumeNode()
    DeislandedLabelMapNode.SetName(WorkingLabelMap.GetName())
    slicer.mrmlScene.AddNode(DeislandedLabelMapNode) 
    SegLogic.ExportSegmentsToLabelmapNode(ConvSeg, LabelMapName, DeislandedLabelMapNode)
  
    # Update mrmlScene and UI
    #slicer.mrmlScene.AddNode(LabelMapIslandsRemoved)
    self.WorkingLabelMapStorage.setCurrentNode(DeislandedLabelMapNode)
    self.UpdateSegmentationNode()

    return True
    
  def OnGenerateLandmarksButtonClicked(self):
    logic = UsSurfaceToLandmarksLogic()
    
    LabelMapNode = self.WorkingLabelMapStorage.currentNode()
    if LabelMapNode == None:
      print "ERROR - Cannot generate landmarks without labelmap; at least threshold volume first"
      return False
      
    else:
      MarkupsNode = logic.LabelmapToMarkupsNode(LabelMapNode, self.UndersampleFractionSlider.value)
      MarkupsNodeName = LabelMapNode.GetName() + self.MarkupsTag
      MarkupsNode.SetName(MarkupsNodeName)
      
      OldMarkupsNode = slicer.util.getNode(MarkupsNodeName)
      if OldMarkupsNode != None:
        slicer.mrmlScene.RemoveNode(OldMarkupsNode)
      
      slicer.mrmlScene.AddNode(MarkupsNode)
      self.OutputMarkupsStorage.setCurrentNode(MarkupsNode)
      return True
    
  def OnConsolidateDuplicatesButtonClicked(self):
    MarkupsNode = self.OutputMarkupsStorage.currentNode()
    if MarkupsNode == None:
      print "ERROR - No output landmarks node found"
      return False
      
    else:
      logic = UsSurfaceToLandmarksLogic()
      ConsolidatedMarkupsNode = logic.ConsolidateDuplicateLandmarks(MarkupsNode, self.DuplicateMisdirectionThresholdSlider.value)
      OldNodeName = MarkupsNode.GetName()
      
      #if self.OutputMarkupsStorage.currentNode() != None:
      #  slicer.mrmlScene.RemoveNode(self.OutputMarkupsStorage.currentNode())
      ConsolidatedMarkupsNode.SetName(OldNodeName)
      slicer.mrmlScene.AddNode(ConsolidatedMarkupsNode)
      ConsolidatedMarkupsNode.CreateDefaultDisplayNodes()
      self.OutputMarkupsStorage.setCurrentNode(ConsolidatedMarkupsNode)
    
      # Remove Left and Right side nodes instantiated by preprocesslandmarks module for duplicate detection
      slicer.mrmlScene.RemoveNode(slicer.util.getNode(OldNodeName + '_Left'))
      slicer.mrmlScene.RemoveNode(slicer.util.getNode(OldNodeName + '_Right'))
    
      #slicer.util.reloadScriptedModule('preprocesslandmarks')
    
      return True
    
  def OnReloadButtonClicked(self):
    slicer.util.reloadScriptedModule(slicer.moduleNames.UsSurfaceToLandmarks)
    print str(slicer.moduleNames.UsSurfaceToLandmarks) + " reloaded"
    return True
    
  def UpdateSegmentationNode(self):
    SegLogic = slicer.modules.segmentations.logic()
    OldSegmentationNode = self.SegmentationNode
    NewSegmentationNode = slicer.vtkMRMLSegmentationNode()
    NewSegmentationNode.SetName(OldSegmentationNode.GetName())
    # Import working labelmap from interface
    WorkingLabelMap = self.WorkingLabelMapStorage.currentNode()
    if WorkingLabelMap != None:
      LabelMapNodeName = WorkingLabelMap.GetName()
      
      OldNodeName = LabelMapNodeName[:-3]     # Assuming all tag names are 3 chars long, the last one will be removed
      # Remove old label map - if present
      #if self.SegmentationNode.GetBinaryLabelmapRepresentation(OldNodeName) != None:
      self.SegmentationNode.RemoveSegment(OldNodeName)

      # Create new label map representation
      SegLogic.ImportLabelmapToSegmentationNode(WorkingLabelMap, self.SegmentationNode)
      self.SegmentationNode.CreateBinaryLabelmapRepresentation()
      
      # Update closed surface representation for visualization
      if self.SegmentationNode.GetClosedSurfaceRepresentation(LabelMapNodeName) == None:
        self.SegmentationNode.CreateClosedSurfaceRepresentation()
        self.SegmentationNode.SetDisplayVisibility(0)
      
      # Toggle visualization on, if specified
      if self.VisualizeLabelMapButton.isChecked():
        self.SegmentationNode.SetDisplayVisibility(1)
#
# UsSurfaceToLandmarksLogic
#

class UsSurfaceToLandmarksLogic(ScriptedLoadableModuleLogic):
  
  def VolumeThresholdToLabelMap(self, VolumeNode, Threshold):
    
    LabelMapNode = slicer.vtkMRMLLabelMapVolumeNode()
    LabelMapNode.SetSpacing(VolumeNode.GetSpacing())
    
    # Apply threshold
    Thresholder = vtk.vtkImageThreshold()
    Thresholder.SetInputData(VolumeNode.GetImageData())
    Thresholder.SetInValue(1)
    Thresholder.SetOutValue(0)
    Thresholder.ThresholdBetween(Threshold, 255)
    Thresholder.Update()
    
    LabelMapNode.SetAndObserveImageData(Thresholder.GetOutput())
    LabelMapNode.SetOrigin(VolumeNode.GetOrigin())
    mat = vtk.vtkMatrix4x4()
    VolumeNode.GetIJKToRASDirectionMatrix(mat)
    LabelMapNode.SetIJKToRASDirectionMatrix(mat)
    return LabelMapNode

  def ErodeLabelMap(self, LabelMapNode, ErosionKernelSize):
    
    # Initialize new label map node
    ErodedLabelMapNode = slicer.vtkMRMLLabelMapVolumeNode()
    ErodedLabelMapNode.SetSpacing(LabelMapNode.GetSpacing())
    ErodedLabelMapNode.SetOrigin(LabelMapNode.GetOrigin())
    
    # Intialize vtkImageDilateErode3D
    Eroder = vtk.vtkImageDilateErode3D()
    Eroder.SetErodeValue(1)
    Eroder.SetDilateValue(0)
    Eroder.SetKernelSize(ErosionKernelSize[0], ErosionKernelSize[1], ErosionKernelSize[2])
    
    # Erode label map
    Eroder.SetInputData(LabelMapNode.GetImageData())
    Eroder.Update()
    ErodedLabelMapNode.SetAndObserveImageData(Eroder.GetOutput())
    
    return ErodedLabelMapNode
    
  def SmoothPolyData(self, PolyData, ConvergenceThresh, NumIterations):
    # Instantiate vtk polydata smoother
    vtkSmoother = vtk.vtkSmoothPolyDataFilter()
    
    vtkSmoother.SetFeatureEdgeSmoothing(True)
    
    vtkSmoother.SetConvergence(ConvergenceThresh)
    vtkSmoother.SetNumberOfIterations(int(NumIterations))
    
    vtkSmoother.SetInputData(PolyData)
    vtkSmoother.Update()
    SmoothedPolyData = vtkSmoother.GetOutput()
    return SmoothedPolyData
    
  def DecimatePolyData(self, PolyData):
    # Instantiate vtk polydata decimator
    vtkDecimator = vtk.vtkDecimatePro()

    
    vtkDecimator.SetInputData(PolyData)
    vtkDecimator.Update()
    DecimatedPolyData = vtkSmoother.GetOutput()
    
    return DecimatedPolyData
    
  def RemoveCoronalIslands(self, ImageData, IslandSizeThreshold):
    IslandRemovalFilter = vtk.vtkImageIslandRemoval2D()
    IslandRemovalFilter.SetAreaThreshold(int(IslandSizeThreshold))
    IslandRemovalFilter.SetSquareNeighborhood(8)
    IslandRemovalFilter.SetIslandValue(1)
    IslandRemovalFilter.SetReplaceValue(0)
    
    # Go through each coronal slice of ImageData, storing slices with islands removed
    CoronalSliceImages = []
    Extent = ImageData.GetExtent()
    
    #print "DEBUG - Island remover instantiated"
    
    for A in range(Extent[2], Extent[3]):  # Take projetion alond A-P line, posterior to anterior direction
      CurrentSliceImageData = vtk.vtkImageData()
      CurrentSliceImageData.SetExtent(ImageData.GetExtent()[0:2] + (0,1) + ImageData.GetExtent()[4:])
      CurrentSliceImageData.SetSpacing(ImageData.GetSpacing())
      CurrentSliceImageData.AllocateScalars(ImageData.GetScalarType(), 1)
      
      for S in range(Extent[4], Extent[5]):    # For each row of the labelmap
        for R in range(Extent[0], Extent[1]):      # For each column of the label-map
          CurrentValue = ImageData.GetScalarComponentAsFloat(R,A,S, 0)
          CurrentSliceImageData.SetScalarComponentFromFloat(R,0,S, 0, CurrentValue)
      
      #print "DEBUG - Image data instantiated"
      IslandRemovalFilter.SetInputData(CurrentSliceImageData)
      IslandRemovalFilter.Update()
      #print "DEBUG - Filter ouput updated"
      IslandsRemovedSliceImage = IslandRemovalFilter.GetOutput()
      CoronalSliceImages.append(IslandsRemovedSliceImage)
    
    #print "DEBUG - All slices' islands removed"
    
    # Merge all slices into one FilteredImageData
    ProcessedImageData = vtk.vtkImageData()
    ProcessedImageData.SetExtent(ImageData.GetExtent())
    ProcessedImageData.SetSpacing(ImageData.GetSpacing())
    ProcessedImageData.AllocateScalars(ImageData.GetScalarType(), 1)
    for i, A in enumerate(range(Extent[2], Extent[3])):  
      for S in range(Extent[4], Extent[5]):    # For each row of the labelmap
        for R in range(Extent[0], Extent[1]):      # For each column of the label-map
          CurrentVoxelLabelValue = CoronalSliceImages[i].GetScalarComponentAsFloat(R,0,S, 0)
          ProcessedImageData.SetScalarComponentFromFloat(R,A,S,0, CurrentVoxelLabelValue)
    
    #print "DEBUG - Image data with islands removed created"
    
    LabelMapIslandsRemoved = slicer.vtkMRMLLabelMapVolumeNode()
    LabelMapIslandsRemoved.SetSpacing(ImageData.GetSpacing())
    LabelMapIslandsRemoved.SetOrigin(ImageData.GetOrigin())
    LabelMapIslandsRemoved.SetAndObserveImageData(ProcessedImageData)
    #print "DEBUG - Image data copied to labelmap"
    
    return LabelMapIslandsRemoved
    
  def UndersampleCoordsArrays(self, r, a, s, SampleFraction):
    # Expects 3 vtkDoubleArray of equal length, and one float in range [0,1] as input
    if SampleFraction <= 0 or SampleFraction > 1:
      print "Invalid under-sampling fraction"
      print " Returning input arrays"
      return (r, a, s)
      
    if s.GetNumberOfValues() != r.GetNumberOfValues() or s.GetNumberOfValues() != a.GetNumberOfValues():
      print "Input arrays not of equal length; cannot correspond to spatial coords"
      print " Returning input arrays"
      return (r, a, s)
    
    NumSamples = int(SampleFraction * s.GetNumberOfValues())
    
    sSamples = vtk.vtkDoubleArray()
    sSamples.SetName('s')
    rSamples = vtk.vtkDoubleArray()
    rSamples.SetName('r')
    aSamples = vtk.vtkDoubleArray()
    aSamples.SetName('a')
    
    # Randomly select voxels without replacement    
    for SmplNum in range(NumSamples):
      SampleIndex = int(np.random.uniform() * (s.GetNumberOfValues()))
      sSamples.InsertNextValue(s.GetValue(SampleIndex))
      rSamples.InsertNextValue(r.GetValue(SampleIndex))
      aSamples.InsertNextValue(a.GetValue(SampleIndex))
    
      #print str(rSamples.GetValue(SmplNum)) + ", " + str(aSamples.GetValue(SmplNum)) + ", " + str(sSamples.GetValue(SmplNum)) 
    
      s.RemoveTuple(SampleIndex)
      r.RemoveTuple(SampleIndex)
      a.RemoveTuple(SampleIndex)
    
    #print "DEBUG - Under-sampling success"
    return (rSamples, aSamples, sSamples)
    
  def LabelmapToMarkupsNode(self, LabelmapNode, UndersampleFraction):
    
    id = LabelmapNode.GetImageData()
    orig = LabelmapNode.GetOrigin()
    idExtent = id.GetExtent()
    #idBounds = id.GetBounds()
    rCoords = vtk.vtkDoubleArray()
    rCoords.SetName('r')
    sCoords = vtk.vtkDoubleArray()
    sCoords.SetName('s')
    aCoords = vtk.vtkDoubleArray()
    aCoords.SetName('a')
    
    for R in range(int(idExtent[0]), int(idExtent[1])):      # For each column of the label-map
      for A in range(int(idExtent[3]), int(idExtent[2])-1, -1):  # Take projetion alond A-P line, posterior to anterior direction
        for S in range(int(idExtent[4]), int(idExtent[5])):    # For each row of the labelmap
          CurrentValue = id.GetScalarComponentAsDouble(R,A,S, 0)
          if CurrentValue > 0:
            #print CurrentValue
            rCoords.InsertNextValue(R+orig[0])
            aCoords.InsertNextValue(A+orig[1])
            sCoords.InsertNextValue(S+orig[2])
            break

    # Undersample coords
    (UndSplR, UndSplA, UndSplS) = self.UndersampleCoordsArrays(rCoords, aCoords, sCoords, UndersampleFraction)
    
    dt = vtk.vtkTable()
    dt.AddColumn(UndSplS)
    dt.AddColumn(UndSplR)
    dt.AddColumn(UndSplA)
    
    # Initialize vtk kMeans class
    km = vtk.vtkKMeansStatistics()
    km.SetInputData(vtk.vtkStatisticsAlgorithm.INPUT_DATA, dt)
    km.SetColumnStatus("s", 1)
    km.SetColumnStatus("r", 1)
    km.SetColumnStatus("a", 1)
    km.RequestSelectedColumns()
    
    #df = vtk.vtkKMeansDistanceFunctorCalculator()
    #km.SetDistanceFunctor(df)
    #df.SetDistanceExpression('sqrt( (r0-0)*(x0-y0) + (x1-y1)*(x1-y1) )')
    
    km.SetLearnOption(True)
    km.SetDeriveOption(True)
    km.SetTestOption(True)
    km.SetAssessOption(False)
    
    #print "DEBUG - vtkKMeansStatistics initialized"
    
    # Iteratively try increasing cluster numbers up to 34
    MinErr = 9999999999         # LargeNumber
    BestK = 1
    for k in range(1,35):
      km.SetDefaultNumberOfClusters(k)
      km.Update()
      # Get cluster centers
      
      OutMetaDS = vtk.vtkMultiBlockDataSet.SafeDownCast(km.GetOutputDataObject(vtk.vtkStatisticsAlgorithm.OUTPUT_MODEL))
      OutMetaTable = vtk.vtkTable.SafeDownCast(OutMetaDS.GetBlock(1))
      #  DEBUGGING INFO
      #print OutMetaDS
      #print OutMetaTable
      
      ErCol = OutMetaTable.GetColumn(3)
      
      # Error metric is usual k-means metric multiplied by k to as larger landmark sets will always have smaller average error
      Er = k*abs(ErCol.GetValue(0))     
      print "Landmark generation error with k = " + str(k) + " means: " + str(Er) 
      
      if Er < MinErr:
        MinErr = Er
        BestK = k
    
    print ""
    print "Optimized landmark generation error with k = " + str(BestK) + " means: " + str(MinErr)
    print ""
    km.SetDefaultNumberOfClusters(BestK)
    km.Update()
    OutMetaDS = vtk.vtkMultiBlockDataSet.SafeDownCast(km.GetOutputDataObject(vtk.vtkStatisticsAlgorithm.OUTPUT_MODEL))
    OutMetaTable = vtk.vtkTable.SafeDownCast(OutMetaDS.GetBlock(0))

    Coords0 = vtk.vtkDoubleArray.SafeDownCast(OutMetaTable.GetColumnByName("r"))
    Coords1 = vtk.vtkDoubleArray.SafeDownCast(OutMetaTable.GetColumnByName("a"))
    Coords2 = vtk.vtkDoubleArray.SafeDownCast(OutMetaTable.GetColumnByName("s"))
    
    # Instantiate and populate MarkupsNode
    LandmarksMarkupsNode = slicer.vtkMRMLMarkupsFiducialNode()
    #LandmarksMarkupsNode.SetName(LabelmapNode.GetName() + "_Mu")
    for i in range(np.size(Coords0)):
      CurrentClusterCoords = [Coords0.GetTuple(i)[0], Coords1.GetTuple(i)[0], Coords2.GetTuple(i)[0]]
      LandmarksMarkupsNode.AddFiducialFromArray(CurrentClusterCoords)
      
    return LandmarksMarkupsNode
    
class UsSurfaceToLandmarksTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_UsSurfaceToLandmarks1()

  def test_UsSurfaceToLandmarks1(self):
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
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = UsSurfaceToLandmarksLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
