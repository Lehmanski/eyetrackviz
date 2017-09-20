import skvideo.io 
from scipy import misc
from os import makedirs
from os.path import isdir
from os import path 


in_path = 'video_data/ball_game_ass.mkv'
out_path = 'video_frames/ball_game'

if not isdir(out_path):
	makedirs(out_path)



vc = skvideo.io.VideoCapture(in_path)

a,b = vc.read()

id = 0

while a:
	misc.imsave(path.join(out_path,str(id).zfill(4))+'.jpg', b)
	a,b = vc.read()
	id += 1
