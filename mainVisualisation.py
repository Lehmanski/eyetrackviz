import numpy as np 

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QSizePolicy, QSlider, QSpacerItem, \
    QVBoxLayout, QWidget, QCheckBox, QPushButton
from PyQt5.QtGui import QPolygon

import pyqtgraph.opengl as gl
from pyqtgraph import GraphicsWindow, mkQApp
import pyqtgraph as pg
from pyqtgraph.opengl import GLViewWidget

from dataHandler import DataHandler

import sys

import matplotlib.pyplot as plt 

from controlWindow import *




class PlotWindow(GLViewWidget):
    def __init__(self, parent=None):
        super(PlotWindow, self).__init__(parent=None)





class MainWindow(QWidget):
    def __init__(self, data_path, image_path, until_frame=None):
        super(MainWindow, self).__init__()
        # create a data reader object
        self.handler = DataHandler(data_path = data_path,
                                   image_path = image_path,
                                   image_spacing = -5,
                                   sigma = 5)


        """
        Data loading and management
        """
        # read in the .ass subtitle data (gaze points and aois)
        self.handler.readAss()
        # throw away bunch of data (for faster testing)


        if until_frame is not None:
            self.handler.gaze_points = self.handler.gaze_points[:until_frame,:,:]

        # rescale images to smaller size 
        self.handler.scaling_factor = .2
        # load the video frames (single .jpg images in folder) [frame size is obtained her]
        self.handler.loadFramesAsGLImageItems()
        # transform gaze points data into gaussians (ImageItems)
        self.handler.gazePointsToGaussians()
        # transform aois into GLMeshItems
        self.handler.aoisToGLMeshItems(option='translucent')
        # create 3d lines from gaze points:
        self.handler.gazePointsToLines(option='translucent')
        # create heatmaps:
        self.handler.gazePointsToHeatmaps()

        self.handler.aoisToGLLinePlotItems(option='opaque')





        """
        Visualization and Plotting
        """
        # instantiate window for the data visualization
        self.plotWindow = PlotWindow(parent=None)

        #add surface under and behind the scene
        surf_color = [0.945, 0.9098, 0.6823, 1.0]
        self.surf1 = np.zeros([2,2])
        self.surf1 = gl.GLSurfacePlotItem(z=self.surf1,
                                          color = surf_color)
        self.surf1.scale(self.handler.gaze_points.shape[0]*self.handler.image_spacing*1.1,
                        self.handler.frame_size[1]*1.1,
                        1)
        self.surf1.translate(-self.handler.gaze_points.shape[0]*self.handler.image_spacing*0.05,
                             -self.handler.frame_size[1]*0.05,
                             -self.handler.frame_size[0]-100*self.handler.scaling_factor)
        self.plotWindow.addItem(self.surf1)

        self.surf2 = np.zeros([2,2])
        self.surf2 = gl.GLSurfacePlotItem(z=self.surf2,
                                          color = surf_color)
        self.surf2.scale(self.handler.gaze_points.shape[0]*self.handler.image_spacing*1.1,
                        self.handler.frame_size[0]*1.1,
                        1)
        self.surf2.rotate(90,1,0,0)
        self.surf2.translate(-0.05*self.handler.gaze_points.shape[0]*self.handler.image_spacing,
                             -100 * self.handler.scaling_factor,
                             -self.handler.frame_size[0]*1.05)
        self.plotWindow.addItem(self.surf2)


        '''
        adding heatmaps
        '''
        self.plotWindow.addItem(self.handler.XYHeatmap)
        self.plotWindow.addItem(self.handler.XZHeatmap)



        # put video frames inside of visualization
        for frame in self.handler.frames:
            self.plotWindow.addItem(frame)
            frame.setVisible(False)

        # put gaussians on top of video frames:
        for gaussian in self.handler.gaussians:
            self.plotWindow.addItem(gaussian)
            gaussian.setVisible(False)

        # add aoi meshes into visualization
        for mesh in self.handler.aoiMeshes:
            self.plotWindow.addItem(mesh)
            #mesh.setVisible(False)
        self.handler.frames[0].setVisible(True)

        # add line plots
        for line in self.handler.gazePointsLinePlotItems:
            self.plotWindow.addItem(line)

        # add aoi frame lines
        for lines in self.handler.aoiLines:
            for line in lines:
                self.plotWindow.addItem(line)


        #self.horizontalLayout.addWidget(self.plotWindow)
        self.plotWindow.show()





if __name__ == '__main__':

    app = QApplication(sys.argv)


    if len(sys.argv)<=4:
        mainWindow = MainWindow(data_path = sys.argv[1],
                                image_path = sys.argv[2],
                                until_frame = int(sys.argv[3]))
    else:
        mainWindow = MainWindow(data_path = sys.argv[1],
                                image_path = sys.argv[2])

    cw = ControlWindow(mainWindow=mainWindow, handler=mainWindow.handler,parent=None)
    cw.showFrameNum(0)
    cw.showGaussianNum(0)


    
    cw.setGeometry(100,100,100,700)
    x,y,w,h = cw.frameGeometry().getCoords()

    mainWindow.plotWindow.setGeometry(w,100,1500,h-x)

    sys.exit(app.exec_())
    
   