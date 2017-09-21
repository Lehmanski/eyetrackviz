import numpy as np 
import sys 
import skvideo.io

from scipy import misc
from os import path, listdir

import pyqtgraph as pg 
import pyqtgraph.opengl as gl 

import matplotlib.pyplot as plt
from matplotlib.pyplot import cm 

import sys, copy




class DataHandler():
    def __init__(self, data_path = None, image_path = None, frame_size = None, image_spacing = 1, sigma = 20, scaling_factor = 1.):
        self.frame_size = frame_size
        self.image_spacing = image_spacing
        self.sigma = sigma 
        self.scaling_factor = scaling_factor
        self.image_path = image_path
        self.data_path = data_path
        self.keyFrames = []
        # get get frame size:
        self.loadFrameByNumber(0)
    '''
    Helper Functions
    '''
    def getColors(self, inp, colormap, vmin=None, vmax=None):
        norm = plt.Normalize(vmin, vmax)
        cm = colormap(norm(inp))*255
        alpha = (inp/inp.max())*100
        if np.isnan(alpha).any():
            alpha = np.ones(alpha.shape)
        alpha[alpha<30] = 0
        alpha[alpha>=30] += 200
        cm[:,:,-1] = alpha
        cm[:,:,-1] = (inp/inp.max())*255
        return cm

    def getKeyFrameIdxs(self, keyFramesPath):
        f = open(keyFramesPath)
        lines = f.readlines()
        f.close()
        self.keyFrameIdxs = []
        for line in lines:
            self.keyFrameIdxs.append(int(line.strip()))
        self.keyFrameIdxs = np.array(self.keyFrameIdxs)

    def getKeyFramesAsGLImageItems(self):
        self.keyFrames = []
        for frame_idx in self.keyFrameIdxs:
            frame = self.loadFrameByNumber(frame_idx, option='translucent')
            self.keyFrames.append(frame)

    def getFrameRate(self):
        # TODO: write function to read framerate from video source
        self.frame_rate = 1./25        


    def str2sec(self, tStr):
        h, m, sms = tStr.split(':')
        s, ms = sms.split('.')
        return int(h)*60*60 + int(m)*60 + int(s) + int(ms)*0.01



    """
    Subtitle data loading and processing (gaze points)
    """
   
    def timeStampsToFrameNr(self, t_start, t_stop):
        f_start = int(self.str2sec(t_start)/self.frame_rate)
        f_stop = int(self.str2sec(t_stop)/self.frame_rate)
        return f_start,f_stop


    def readAss(self):
            self.getFrameRate()
            # list all .ass files in specified folder
            file_paths = listdir(self.data_path)
            file_paths = sorted([path.join(self.data_path, f) for f in file_paths if f.endswith('.ass')])
            # data containers:
            self.gaze_points = []
            self.aois = []
            self.max_time = 0
            for file_path in file_paths:
                file = open(file_path)
                line = file.readline()
                data = []
                while not line.startswith('Dialogue:'):
                    line = file.readline()
                for ix,line in enumerate(file.readlines()):
                    a,b = line.split('{\\p1}')
                    if b.startswith('s'):
                        marker_type = 'gaze_points'
                        t_start = a.split(',')[1]
                        t_stop = a.split(',')[2]
                        # get all frame indices, where soi is visible:
                        f_start,f_stop = self.timeStampsToFrameNr(t_start,t_stop)
                        a1,a2 = a.split('\\pos(')[1].split(',')
                        y = float(a1)
                        x = float(a2[:-2])
                        data.append([x,y,f_start,f_stop])

                    elif b.startswith('m'):
                        marker_type = 'aoi'
                        t_start = a.split(',')[1]
                        t_stop = a.split(',')[2]
                        # get all frame indices, where soi is visible:
                        f_start,f_stop = self.timeStampsToFrameNr(t_start,t_stop)
                        a1,a2 = a.split('\\pos(')[1].split(',')

                        y = float(a1)
                        x = float(a2[:-2])
                        width = float(b.split(' ')[-2])
                        height = float(b.split(' ')[-5])
                        data.append([x,y,width,height,f_start,f_stop])
                data = np.vstack(data)
                if marker_type == 'gaze_points':
                    self.gaze_points.append(data)
                    self.max_time = max([self.max_time,np.max(data[:,2])])
                elif marker_type == 'aoi':
                    self.aois.append(data)
            self.gazePointsToArray()

    def gazePointsToArray(self):
        data = np.zeros((int(np.ceil(self.max_time))+1,3,len(self.gaze_points)))
        for sx in range(len(self.gaze_points)):
            for point_idx in range(self.gaze_points[sx].shape[0]):
                # coordinates of gaze point
                point = self.gaze_points[sx][point_idx,:2]
                # start and stop frame of gaze_point
                # TODO: fix this, so that each gaze point is visible for a certain 
                # duration, not only one frame
                f_start, f_stop = self.gaze_points[sx][point_idx,2:].astype('int')
                data[f_start,:2,sx] = point
                data[f_start,2,sx] = f_start
        self.gaze_points = data
        self.rescaleData()
        self.cleanGazePointsArray()

    def cleanGazePointsArray(self, rep=True):
        for ix in range(self.gaze_points.shape[2]):
            d = self.gaze_points[:,:,ix]
            d[:,-1] = np.arange(0,d.shape[0],1)
            # find first non-zero entry
            fx = np.where(np.any(d>0,1))[0][0]+1
            # change all before that to first none zero
            d[:fx,-1] = d[fx,-1]
            for jx in range(fx,d.shape[0]):
                # if either x or y coordinate are equal to zero
                if any(d[jx,:-1] == 0):
                    # substitute for entry before
                    d[jx,:-1] = d[jx-1,:-1]
                # cant look outside the window
                d[jx,0] = np.max([0,d[jx,0]])
                d[jx,0] = np.min([self.frame_size[0],d[jx,0]])
                d[jx,1] = np.max([0,d[jx,1]])
                d[jx,1] = np.min([self.frame_size[1],d[jx,1]])
                # leaky integration of coordinates (should make path smoother)
                k = 0.3
                d[jx,:-1] = k*d[jx,:-1] + (1-k)*d[jx,:-1]
            self.gaze_points[:,:,ix] = d



    def rescaleData(self):
        # rescale the datapoints to match the size of reshaped frames
        self.gaze_points[:,:2,:] *= self.scaling_factor
        for ax in range(len(self.aois)):
            aoi = self.aois[ax]
            aoi[:,:4] *= self.scaling_factor
            self.aois[ax] = aoi 


    def aoisToGLMeshItems(self, option='additive'):
        self.aoiMeshes = [] 
        alpha = 0.5
        cols = [[1.,0.,0.,alpha],
                  [0.,1.,0.,alpha],
                  [0.,0.,1.,alpha],
                  [1.,1.,0.,alpha],
                  [1.,0.,1.,alpha],
                  [0.,1.,1.,alpha],
                  [1.,0.5,0.,alpha],
                  [0.,1.,0.5,alpha],
                  [0.5,0.,1.,alpha],
                  [1.,1.,0.5,alpha],
                  [1.,0.5,1.,alpha],
                  [0.5,1.,1.,alpha]]
        counter = 0
        for AOIS in self.aois:
            vertices = []
            faces = []
            for coordinates in AOIS:
                x,y,w,h,f_start,f_stop = coordinates
                # for the duration in which aoi is visible (f_start -- f_stop)
                for f in range(int(f_start),int(f_stop)+1,1):
                    f = f*self.image_spacing
                    # span vertices of square:
                    v1 = np.array([x,y,f])
                    v2 = np.array([x+w,y,f])
                    v3 = np.array([x+w,y+h,f])
                    v4 = np.array([x,y+h,f])
                    vertices.extend([v1,v2,v3,v4])

            vertices = np.vstack(vertices)

            # faces
            for idx in range(0,len(vertices)-8,4):
                if (vertices[idx,-1] - vertices[idx+4,-1])>-self.image_spacing:
                    del faces[-4:]
                    continue
                else:
                    for ix in range(idx,idx+5,1):
                        faces.append([ix,ix+1,ix+5])
                        faces.append([ix,ix+4,ix+5])
            faces = np.vstack(faces)

            c = np.tile(cols[counter%len(cols)],[faces.shape[0],1])
            counter+=1


            aoisMesh = gl.GLMeshItem(vertexes=vertices, drawEdges = False, 
                        faces=faces, faceColors = c, edgeColor=[0,0,0,1])
            
            aoisMesh.setGLOptions(option)
            aoisMesh.rotate(90,0,1,0)
            aoisMesh.translate(1,0,0)
            self.aoiMeshes.append(aoisMesh)


    def aoisToGLLinePlotItems(self, option='additive', alpha=1.0, width=5):
        self.aoiLines = [] 
        cols = [[1.,0.,0.,alpha],
                  [0.,1.,0.,alpha],
                  [0.,0.,1.,alpha],
                  [1.,1.,0.,alpha],
                  [1.,0.,1.,alpha],
                  [0.,1.,1.,alpha],
                  [1.,0.5,0.,alpha],
                  [0.,1.,0.5,alpha],
                  [0.5,0.,1.,alpha],
                  [1.,1.,0.5,alpha],
                  [1.,0.5,1.,alpha],
                  [0.5,1.,1.,alpha]]
        counter = 0
        for AOIS in self.aois:
            aoi_lines = []
            for ix in range(4):
                line = gl.GLLinePlotItem()
                if ix == 0:
                    coords = AOIS[:,[0,1,4]]
                elif ix == 1:
                    coords = AOIS[:,[0,1,4]]
                    coords[:,0] += AOIS[:,2]
                elif ix == 2:
                    coords = AOIS[:,[0,1,4]]
                    coords[:,1] += AOIS[:,3]
                elif ix == 3:
                    coords = AOIS[:,[0,1,4]]
                    coords[:,0] += AOIS[:,2]
                    coords[:,1] += AOIS[:,3]
                coords[:,-1] *= self.image_spacing
                line.setData(pos=coords, color = cols[counter%len(cols)], width=width,
                            mode='line_strip',antialias=True)
                line.setGLOptions(option)
                line.rotate(90,0,1,0)
                line.setDepthValue(-1)
                #line.translate(1,0,0)
                aoi_lines.append(line)
            counter+=1
            self.aoiLines.append(aoi_lines)


    '''
    Gaze Points
    '''
    def gaussian(self, max = 100, mu = 50, sigma = 5):
        '''
        Returns a 1d gaussian, normalized to be between (0,1)
        '''
        x = np.linspace(0, max, max)
        y = (1./np.sqrt(2*np.pi*sigma**2))*np.exp(-(x-mu)**2/(2*sigma**2))
        y = y-y.min()
        y = y/y.max()
        return y

    def gaussian2d(self, mu, sigma):
        '''
        Returns a two dimensional gaussian, normalized to be between (0,1)
        '''
        x = self.gaussian(max = self.frame_size[0], mu = mu[0], sigma = sigma)
        y = self.gaussian(max = self.frame_size[1], mu = mu[1], sigma = sigma)
        xx,yy = np.meshgrid(y,x)
        g = yy*xx
        g = g-g.min()
        g = g/g.max()
        return g 

    def gazePointsToGaussians(self, sigma = 20, rotation=[90,0,1,0], 
                   x_shift=0, y_shift=0, option='additive'):
        '''
        Transforms the csv data into a list of GLImageItems. Each item contains the 
        viewpoints (AOIs) of every subject represented as Gaussians
        '''
        self.gaussians = []
        self.XYHeatmap = []
        self.XZHeatmap = []
        for frame_idx in range(self.gaze_points.shape[0]):
            print('computing gaussian overlay #{0}'.format(frame_idx))
            frame_data = self.gaze_points[frame_idx,:2,:]
            gaussians = []
            for subject in range(self.gaze_points.shape[2]):
                # mus are simply pixel indices of eye tracking
                subject_data = frame_data[:,subject]
                # 
                gaussian = self.gaussian2d([subject_data[0], subject_data[1]], self.sigma)
                gaussians.append(gaussian)
            # add all gaussians
            gaussians = np.sum(gaussians,0)
            # divide by number of subjects to renormalize gaussians (0,1)
            gaussians /= (subject+1)
            # transform to RGBA
            gaussians = self.getColors(gaussians, cm.jet)
            # transform into GLImageItem
            gaussians = gl.GLImageItem(gaussians)
            # rotate, translate, scale, set option
            gaussians.rotate(rotation[0],rotation[1],rotation[2],rotation[3])
            gaussians.translate(frame_idx*self.image_spacing+x_shift+1,y_shift,0)

            gaussians.setGLOptions(option)
            self.gaussians.append(gaussians)

    def gazePointsToLines(self, width=1, alpha=1.0, rotation=[90,0,1,0],
                          option='opaque'):
        cols = [[1.,0.,0.,alpha],
                  [0.,1.,0.,alpha],
                  [0.,0.,1.,alpha],
                  [1.,1.,0.,alpha],
                  [1.,0.,1.,alpha],
                  [0.,1.,1.,alpha],
                  [1.,0.5,0.,alpha],
                  [0.,1.,0.5,alpha],
                  [0.5,0.,1.,alpha],
                  [1.,1.,0.5,alpha],
                  [1.,0.5,1.,alpha],
                  [0.5,1.,1.,alpha]]
        self.gazePointsLinePlotItems = []
        for sx in range(self.gaze_points.shape[2]):
            line = gl.GLLinePlotItem()
            coords = self.gaze_points[:,:,sx]
            coords[:,-1] *= self.image_spacing
            line.setData(pos=coords, color = cols[sx%len(cols)], width=width,
                        mode='line_strip',antialias=True)
            line.rotate(*rotation)
            line.setGLOptions(option)
            line.setDepthValue(-1)
            self.gazePointsLinePlotItems.append(line)

    def gazePointsToHeatmaps(self):
        self.XYHeatmap = []
        self.XZHeatmap = []
        for sx in range(self.gaze_points.shape[2]):
            XYG = []
            XZG = []
            for f in range(self.gaze_points.shape[0]):
                d = self.gaze_points[f,:,sx]
                xyg = self.gaussian(mu=d[0],max=self.frame_size[0])
                xzg = self.gaussian(mu=d[1],max=self.frame_size[1])
                XYG.append(xyg)
                XZG.append(xzg)
            self.XYHeatmap.append(np.array(XYG))
            self.XZHeatmap.append(np.array(XZG))

        self.XYHeatmap = np.sum(self.XYHeatmap,0)
        self.XZHeatmap = np.sum(self.XZHeatmap,0)
        self.XYHeatmap = gl.GLImageItem(self.getColors(self.XYHeatmap,cm.jet))
        self.XZHeatmap = gl.GLImageItem(self.getColors(self.XZHeatmap,cm.jet))
        
        self.XYHeatmap.scale(self.image_spacing,1,1)                
        self.XZHeatmap.scale(self.image_spacing,1,1)

        self.XYHeatmap.rotate(90,-1,0,0)
        self.XYHeatmap.translate(0,-50*self.scaling_factor,0)
        self.XZHeatmap.translate(0,0,-self.frame_size[0]-50*self.scaling_factor)
    '''
    Video Data Handling
    '''
    def loadFrameByNumber(self, number, rotation=[90,0,1,0], 
                                 x_shift=0, y_shift=0, option='translucent'):
        # list and sort all frames in folder
        frame_paths = sorted(listdir(self.image_path))
        frame_paths = [path.join(self.image_path,p) for p in frame_paths]
        if number >= len(frame_paths):
            return None
        frame = misc.imread(frame_paths[number])
        if not self.scaling_factor == 1.:
            frame = misc.imresize(frame, self.scaling_factor)
        if self.frame_size is None:
            self.frame_size = frame.shape[:2]
            self.z_shift = 0#self.frame_size[0]
        # convert frame into RGBA image
        frame = pg.makeRGBA(frame, levels = [frame.min(),frame.max()])[0]
        frame = gl.GLImageItem(frame)
        frame.rotate(rotation[0],rotation[1],rotation[2],rotation[3])
        frame.translate(number*self.image_spacing+x_shift,y_shift,self.z_shift)
        frame.setGLOptions(option)

        return frame 

    def loadFramesAsGLImageItems(self, rotation=[90,0,1,0], 
                                 x_shift=0, y_shift=0, option='translucent'):
        self.frames = []
        for idx in self.gaze_points[:,2,0]:
            print('loading video frame #{0}'.format(idx))
            frame = self.loadFrameByNumber(int(idx), rotation=rotation, 
                                           x_shift=x_shift, y_shift= y_shift,
                                           option = option)
            if frame is None:
                self.gaze_points = self.gaze_points[:int(idx),:,:]
                break

            self.frames.append(frame)
        #self.rescaleData()


    def loadKeyFrames(self, key_frame_list, rotation=[90,0,1,0], scale = .5):
        self.keyFrames = []
        for kf in key_frame_list:
            if kf >= len(self.frames) or kf<0:
                print('key frame value not in list: {0}'.format(kf))
                continue
            data = self.frames[kf].data.copy()
            keyFrame = gl.GLImageItem(data)
            keyFrame.rotate(*rotation)
            keyFrame.scale(scale,scale,1)
            keyFrame.translate(self.image_spacing*kf,
                               self.frame_size[1]*1.15,0)
                               #-self.frame_size[0]*1.15)
            self.keyFrames.append(keyFrame)






