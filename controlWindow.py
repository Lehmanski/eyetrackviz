from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QCheckBox, QSizePolicy, QSlider, QSpacerItem, \
    QVBoxLayout, QWidget, QPushButton, QToolButton, QMenu, QLineEdit
import re

class ControlWindow(QWidget):
    def __init__(self, mainWindow = None, handler = None, parent=None):
        super(ControlWindow,self).__init__(parent=parent)
        self.handler = handler
        self.mainWindow = mainWindow
        self.activeFrames = []
        self.activeGaussians = []
        self.frame_toggle = True
        self.gaussian_toggle = True 
        self.heatmap_toggle = True
        self.AOIs_toggle = True
        self.AOILines_toggle = True
        self.gaze_paths_toggle = True

        self.horizontalLayout = QHBoxLayout(self)

        self.sliderX = Slider(0, self.handler.aois[0][:,-1].max())
        self.sliderX.slider.setValue(0)
        self.horizontalLayout.addWidget(self.sliderX)
        self.sliderX.slider.valueChanged.connect(lambda: self.translateX(self.sliderX.slider.value()))
        #

        self.sliderY = Slider(0, self.handler.frame_size[1])
        v = .5*self.handler.frame_size[1]
        self.sliderY.slider.setValue(v)
        self.translateY(v)
        self.horizontalLayout.addWidget(self.sliderY)
        self.sliderY.slider.valueChanged.connect(lambda: self.translateY(self.sliderY.slider.value()))
        #

        self.sliderZ = Slider(0, self.handler.frame_size[0])
        v = .5*self.handler.frame_size[0]
        self.sliderZ.slider.setValue(v)
        self.translateZ(v)
        self.horizontalLayout.addWidget(self.sliderZ)
        self.sliderZ.slider.valueChanged.connect(lambda: self.translateZ(self.sliderZ.slider.value()))
        #

        # vertical button layout
        self.buttonLayout = QVBoxLayout()
        spacer = QSpacerItem(10,30)
        self.buttonLayout.addItem(spacer)

        # button to de/activate aois:
        self.buttonAOIs = QCheckBox('aois (volume)')
        self.buttonAOIs.setChecked(True)
        self.buttonAOIs.clicked.connect(self.toggleAOIs)
        self.buttonLayout.addWidget(self.buttonAOIs)

        # button to de/activate aois:
        self.buttonAOIs = QCheckBox('aois (line)')
        self.buttonAOIs.setChecked(True)
        self.buttonAOIs.clicked.connect(self.toggleAOILines)
        self.buttonLayout.addWidget(self.buttonAOIs)

        # button to de/activate gaze paths:
        self.buttonGaze = QCheckBox('gaze paths')
        self.buttonGaze.setChecked(True)
        self.buttonGaze.clicked.connect(self.toggleGaze)
        self.buttonLayout.addWidget(self.buttonGaze)

        # button to de/activate heatmaps:
        self.buttonHeatmap = QCheckBox('heatmaps')
        self.buttonHeatmap.setChecked(True)
        self.buttonHeatmap.clicked.connect(self.toggleHeatmaps)
        self.buttonLayout.addWidget(self.buttonHeatmap)

        # button to de/activate gaussians:
        self.buttonGaussian = QCheckBox('gaze points')
        self.buttonGaussian.setChecked(True)
        self.buttonGaussian.clicked.connect(self.toggleGaussians)
        self.buttonLayout.addWidget(self.buttonGaussian)

        # button to de/activate gaussians:
        self.buttonFrame = QCheckBox('video frames')
        self.buttonFrame.setChecked(True)
        self.buttonFrame.clicked.connect(self.toggleFrames)
        self.buttonLayout.addWidget(self.buttonFrame)

        self.buttonLayout.addStretch()
        self.horizontalLayout.addLayout(self.buttonLayout)


        # vertical selection box layout
        self.selectionLayout = QVBoxLayout()
        spacer = QSpacerItem(10,30)
        self.selectionLayout.addItem(spacer)

        self.aoiSelection = QToolButton()
        self.aoiSelection.setText('select AOI (volume)')
        self.aoiSelectionMenu = QMenu()
        for t in self.handler.aoi_titles:
            a = self.aoiSelectionMenu.addAction(t)
            a.setCheckable(True)
            a.setChecked(True)
            a.changed.connect(self.toggleSingleAOIs)
        self.aoiSelection.setMenu(self.aoiSelectionMenu)
        self.aoiSelection.setPopupMode(QToolButton.InstantPopup)
        self.selectionLayout.addWidget(self.aoiSelection)

        self.aoiLineSelection = QToolButton()
        self.aoiLineSelection.setText('select AOI (lines)')
        self.aoiLineSelectionMenu = QMenu()
        for t in self.handler.aoi_titles:
            a = self.aoiLineSelectionMenu.addAction(t)
            a.setCheckable(True)
            a.setChecked(True)
            a.changed.connect(self.toggleSingleAOILines)
        self.aoiLineSelection.setMenu(self.aoiLineSelectionMenu)
        self.aoiLineSelection.setPopupMode(QToolButton.InstantPopup)
        self.selectionLayout.addWidget(self.aoiLineSelection)

        self.gazePathsSelection = QToolButton()
        self.gazePathsSelection.setText('select gaze paths')
        self.gazePathsSelectionMenu = QMenu()
        for t in self.handler.gp_titles:
            a = self.gazePathsSelectionMenu.addAction(t)
            a.setCheckable(True)
            a.setChecked(True)
            a.changed.connect(self.toggleSingleGazePath)
        self.gazePathsSelection.setMenu(self.gazePathsSelectionMenu)
        self.gazePathsSelection.setPopupMode(QToolButton.InstantPopup)
        self.selectionLayout.addWidget(self.gazePathsSelection)


        self.label = QLabel('specify key frames')
        self.lineEdit = QLineEdit()
        self.lineEditButton = QPushButton('ok')
        self.lineEditButton.clicked.connect(self.updateKeyFrames)
        self.selectionLayout.addWidget(self.label)
        self.selectionLayout.addWidget(self.lineEdit)
        self.selectionLayout.addWidget(self.lineEditButton)

        self.selectionLayout.addStretch()
        self.horizontalLayout.addLayout(self.selectionLayout)

        spacer = QSpacerItem(0,0,QSizePolicy.Expanding,QSizePolicy.Expanding)
        #self.horizontalLayout.addItem(spacer)
        self.show()

    def updateKeyFrames(self):
        if not self.handler.keyFrames == []:
            for kf in self.handler.keyFrames:
                self.mainWindow.plotWindow.removeItem(kf)
                del kf 
        text = re.split(' | , ; ',self.lineEdit.text())
        key_frames = [int(t) for t in text if t.isnumeric()]
        self.handler.loadKeyFrames(key_frames)
        for kf in self.handler.keyFrames:
            self.mainWindow.plotWindow.addItem(kf)

    def toggleFrames(self):
        self.frame_toggle = not self.frame_toggle
        for fx in self.activeFrames:
            frame = self.handler.frames[fx]
            frame.setVisible(self.frame_toggle)

    def toggleGaussians(self):
        self.gaussian_toggle = not self.gaussian_toggle
        for gx in self.activeGaussians:
            gaussian = self.handler.gaussians[gx]
            gaussian.setVisible(self.gaussian_toggle)

    def toggleAllGaussians(self):
        self.gaussian_toggle = not self.gaussian_toggle
        for gx in self.handler.gaussians:
            gx.setVisible(self.gaussian_toggle)

    # gaze paths
    def toggleGaze(self):
        self.gaze_paths_toggle = not self.gaze_paths_toggle
        self.toggleSingleGazePath()

    def toggleSingleGazePath(self):
        for a in self.gazePathsSelectionMenu.actions():
            idx = self.handler.gp_titles.index(a.text())
            self.handler.gazePointsLinePlotItems[idx].setVisible(a.isChecked()*self.gaze_paths_toggle)


    # AOI meshes
    def toggleAOIs(self):
        self.AOIs_toggle = not self.AOIs_toggle
        self.toggleSingleAOIs()

    def toggleSingleAOIs(self):
        for a in self.aoiSelectionMenu.actions():
            idx = self.handler.aoi_titles.index(a.text())
            self.handler.aoiMeshes[idx].setVisible(a.isChecked()*self.AOIs_toggle)
    # AOI lines
    def toggleAOILines(self):
        self.AOILines_toggle = not self.AOILines_toggle
        self.toggleSingleAOILines()


    def toggleSingleAOILines(self):
        for a in self.aoiLineSelectionMenu.actions():
            idx = self.handler.aoi_titles.index(a.text())
            for line in self.handler.aoiLines[idx]:
                line.setVisible(a.isChecked()*self.AOILines_toggle)


    def toggleHeatmaps(self):
        self.heatmap_toggle = not self.heatmap_toggle
        self.handler.XYHeatmap.setVisible(self.heatmap_toggle)
        self.handler.XZHeatmap.setVisible(self.heatmap_toggle)

    def translateX(self, value):
        self.mainWindow.plotWindow.opts['center'].setX(value * self.handler.image_spacing)
        if value < len(self.handler.frames):
            self.showFrameNum(value)
            self.showGaussianNum(value)
        self.mainWindow.plotWindow.update()

    def translateY(self, value):
        self.mainWindow.plotWindow.opts['center'].setY(value)
        self.mainWindow.plotWindow.update()

    def translateZ(self, value):
        self.mainWindow.plotWindow.opts['center'].setZ(-value)
        self.mainWindow.plotWindow.update()

    def showFrameNum(self, value):
        for frame in self.handler.frames:
            frame.setVisible(False)
        if self.frame_toggle:
            self.handler.frames[value].setVisible(True)
        self.activeFrames = [value]

    def showGaussianNum(self, value):
        for gaussian in self.handler.gaussians:
            gaussian.setVisible(False)
        if self.gaussian_toggle:
            self.handler.gaussians[value].setVisible(True)
        self.activeGaussians = [value]

    def showGazePointLines(self, line_idxs):
        for line in self.handler.gazePointsLinePlotItems:
            line.setVisible(False)
        for idx in line_idxs:
            self.handler.gazePointsLinePlotItems[idx].setVisible(True)


class Slider(QWidget):
    def __init__(self, minimum, maximum, parent=None):
        super(Slider, self).__init__(parent=None)
        self.verticalLayout = QVBoxLayout(self)
        self.label = QLabel(self)
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout = QHBoxLayout()
        #spacerItem = QSpacerItem(0, 20, QSizePolicy.Expanding)
        #self.horizontalLayout.addItem(spacerItem)
        self.slider = QSlider(self)
        self.slider.setOrientation(Qt.Vertical)
        self.horizontalLayout.addWidget(self.slider)
        #spacerItem1 = QSpacerItem(0, 20, QSizePolicy.Expanding)
        #self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.resize(self.sizeHint())

        self.minimum = minimum
        self.maximum = maximum
        self.slider.setRange(minimum, maximum)
        self.slider.valueChanged.connect(self.setLabelValue)
        self.x = None
        self.setLabelValue(self.slider.value())

    def setLabelValue(self, value):
        self.label.setText("{0:.4g}".format(value))
