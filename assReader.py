import numpy as np
from os import path, listdir
import sys
from pprint import pprint as print

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QSizePolicy, QSlider, QSpacerItem, \
    QVBoxLayout, QWidget, QCheckBox
from PyQt5.QtGui import QPolygon


import pyqtgraph.opengl as gl
from pyqtgraph import GraphicsWindow, mkQApp
import pyqtgraph as pg
from pyqtgraph.opengl import GLViewWidget


class Slider(QWidget):
    def __init__(self, minimum, maximum, parent=None):
        super(Slider, self).__init__(parent=None)
        self.verticalLayout = QVBoxLayout(self)
        self.label = QLabel(self)
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout = QHBoxLayout()
        spacerItem = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.slider = QSlider(self)
        self.slider.setOrientation(Qt.Vertical)
        self.horizontalLayout.addWidget(self.slider)
        spacerItem1 = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
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


class DataHandler():


    def str2sec(self, tStr):
        h, m, sms = tStr.split(':')
        s, ms = sms.split('.')
        return int(h)*60*60 + int(m)*60 + int(s) + int(ms)*0.01



    def readAss(self, f_path):

        files = listdir(f_path)
        files = [f for f in files if f.endswith('ass')]
        self.subtitle_data = {'aoi': [], 
                         'gaze_points':[]}
        # gaze points must be (m,3,n_subj)
        for file in files:
            data = []
            f = open(file)
            line = f.readline()
            while not line.startswith('Dialogue:'):
                line = f.readline()
            for ix,line in enumerate(f.readlines()):
                a,b = line.split('{\\p1}')
                if b.startswith('s'):
                    marker_type = 'gaze_points'
                    f_start = a.split(',')[1]
                    f_stop = a.split(',')[2]
                    z = ix * 20# str2sec(f_stop) #- str2sec(f_start)

                    a1,a2 = a.split('\\pos(')[1].split(',')
                    x = float(a1)
                    y = float(a2[:-2])
                    data.append([z, (x,y)])
                elif b.startswith('m'):
                    marker_type = 'aoi'
                    f_start = a.split(',')[1]
                    f_stop = a.split(',')[2]
                    z = ix * 20# str2sec(f_stop) #- str2sec(f_start)

                    a1,a2 = a.split('\\pos(')[1].split(',')
                    x = float(a1)
                    y = float(a2[:-2])
                    width = float(b.split(' ')[-2])
                    height = float(b.split(' ')[-5])
                    data.append([z, (x,y), (width, height)])
            self.subtitle_data[marker_type].append(data)
            f.close()

    def aoisToGLMeshItem(self):
        aois = self.subtitle_data['aoi'][0]
        self.vertices = []
        for aoi in aois:
            z = aoi[0]
            y,x = aoi[1]
            w,h = aoi[2]
            w += x
            h += y
            a = np.array([x,y,z])
            b = np.array([x+w,y,z])
            c = np.array([x+w,y+h,z])
            d = np.array([x,y+h,z])
            self.vertices.append(a)
            self.vertices.append(b)
            self.vertices.append(c)
            self.vertices.append(d)

        self.vertices = np.vstack(self.vertices)

        self.faces = []
        for idx in range(0,self.vertices.shape[0]-4,4):
            # top
            self.faces.append(np.array([idx,idx+1,idx+4]))
            self.faces.append(np.array([idx+1,idx+4,idx+5]))
            # left
            self.faces.append(np.array([idx+2,idx+3,idx+6]))
            self.faces.append(np.array([idx+3,idx+6,idx+7]))
            # bottom
            self.faces.append(np.array([idx,idx+3,idx+7]))
            self.faces.append(np.array([idx,idx+4,idx+7]))
            # right
            self.faces.append(np.array([idx+1,idx+2,idx+5]))
            self.faces.append(np.array([idx+2,idx+5,idx+6]))
        # front
        self.faces.append(np.array([0,1,2]))
        self.faces.append(np.array([0,2,3]))
        # back
        self.faces.append(np.array([idx+4,idx+5,idx+6]))
        self.faces.append(np.array([idx+4,idx+6,idx+7]))
        #
        self.faces = np.vstack((self.faces))

        c = np.tile([0.5,0.5,0.5,.5],[self.faces.shape[0],1])

        self.mesh = gl.GLMeshItem(vertexes=self.vertices, drawEdges = False, faces=self.faces, faceColors = c, edgeColor=[0,0,0,1])
        self.mesh.setGLOptions('translucent')
        self.mesh.rotate(90,0,1,0)





if __name__ == '__main__':

    dh = DataHandler()

    dh.readAss('/home/me/Dropbox/Alles_fuer_die_Uni/Job/matroska_stuff/')
    dh.aoisToGLMeshItem()


    app = QApplication(sys.argv)

    w = GLViewWidget()

    w.addItem(dh.mesh)



    w.show()
