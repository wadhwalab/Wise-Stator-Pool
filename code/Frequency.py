# Computes rotation frequency from Object-Detection output for a single video.
# Outputs freq.csv and freq-plot.png to the results folder.
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
import scipy 
import cv2

#Rotation speed
def get_fps(video_path):
    video = cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    video.release()
    return int(fps)

def get_rotfreq(x, y, xcen, ycen, frate):
    xcomp = x - xcen #x component of the vector from center of rotation to centroid
    ycomp = y - ycen #y component of the vector from center of rotation to centroid
    theta = np.unwrap(np.arctan2(ycomp, xcomp)) # UNWRAP function
    f = frate*np.diff(theta)/(2*np.pi)
    return f

#Displacement between two points:
def disp(x1,y1,x0,y0):
    return np.sqrt((x1-x0)*(x1-x0) + (y1-y0)*(y1-y0))
###

#Taking inputs from user
avi_file = input("Input path to video")
results = input("Input path to results folder")

#Get video FPS
FPS = get_fps(avi_file)
print(f'FPS: {FPS}')

#Taking information from files
properties = pd.read_csv(results + os.path.sep + "frame-properties-df.csv")
center = pd.read_csv(results + os.path.sep + "center-coordinates.csv")
x = properties["x"].to_numpy() #x,y centroid
y = properties["y"].to_numpy()
mjr_ax = properties["Majoraxis"].to_numpy() #major axis of obj
xc = center["x"].to_numpy() #x,y center of rotation
yc = center["y"].to_numpy()

#correcting center coordinates - if distance traveled over 10 frames is less than the diameter of the cell (major axis) then correct center coordinates
#center correction is only really useful if your object stops rotating
i_list = np.arange(1,len(x) ,dtype='int')
dia = np.mean(mjr_ax) #determining diameter of object by averaging major axis length
thresh = 0.5 #for tethered cell assays set this to 1, for bead assays set this to 0.5?
displacements = np.zeros(len(x))
#finding displacements between consecutive centroid coordinates
for i in i_list:
    d = disp(x[i], y[i], x[i-1], y[i-1])
    displacements[i] = d
sums = []
#sum the displacement over 10 frames
for i in i_list:
    sum = np.sum(displacements[i:i+10])
    sums.append(sum)
#dividing the sum by the diameter to get a unitless number
corrected_sum = sums / dia
j_list = np.arange(1,len(x)-1,dtype='int')
for j in j_list:
    #if the unitless number is less than the threshold we correct the center coordinates
    if corrected_sum[j] <= thresh:
        xc[j] = xc[j-1]
        yc[j] = yc[j-1]
    else:
        continue

#calculate frequency
freq = get_rotfreq(x,y,xc,yc,FPS) #multiply by -1 for CW rotation
    
#filtering frequency with a median filter
freq_filt = scipy.signal.medfilt(freq, kernel_size=51)
    
#plotting filtered frequency for easy visualization
seconds = np.arange(0,len(x) - 1) / FPS
figure = plt.figure(figsize=(10,5))
ax1 = figure.add_subplot(111)
ax1.plot(seconds, freq_filt, c='grey',label='Frequency (Filtered)')
ax1.set_xlabel("Time (seconds)")
ax1.set_ylabel("Frequency (Hz)")
#plt.xlim((0,20))
figure.tight_layout()
plt.yticks(np.arange(-15, 15, 5.0))
#plt.legend(loc = 'lower right')
plt.savefig(results + os.path.sep + 'freq-plot.png', dpi = 300)

#saving the FILTERED frequency 
ff = pd.DataFrame(freq_filt)
ff.to_csv(results + os.path.sep + 'freq.csv')

#saving the UPDATED center coordinates
cdata = {'x': xc, 'y': yc}
cframe = pd.DataFrame(cdata)
cframe.to_csv(results + os.path.sep + 'new-center-coordinates.csv') #exporting center coordinates