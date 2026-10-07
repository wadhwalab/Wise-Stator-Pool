# Batch version of Object-Detection.py; processes all .avi files in a directory.
# Prompts for a threshold region per video; outputs per-video frame-properties-df.csv and center-coordinates.csv.
import os
import cv2
import pims
import numpy as np
import matplotlib.pyplot as plt 
import matplotlib.widgets as mwidgets
from skimage.filters import threshold_multiotsu
from skimage.color import rgb2gray
from skimage import measure
import pandas as pd
from circle_fit import taubinSVD
from circle_fit import hyperLSQ
from circle_fit import kmh
import shutil
import argparse

def get_fps(video_path):
    #function to get the FPS of a video file file
    video = cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    video.release()
    print(fps)
    return int(fps)
###

#Taking inputs from user
parser = argparse.ArgumentParser()
parser.add_argument('-avi', help="insert path to the video.", required=True)
parser.add_argument('-r', help="path & name for the results folder", required=True)
args = parser.parse_args()
directory = args.avi
results = args.r

#opening avi files
files = os.listdir(directory)
avi_files = [file for file in files if file.lower().endswith('.avi')]
file_number = "0"

#cycling through every avi file
for avi_file in avi_files:
    avi_name = avi_file[:-4]
    os.mkdir(results + os.path.sep + avi_name)
    path = os.path.join(directory, avi_file)
    print(f'Analyzing file: {path}')
    vidcap = cv2.VideoCapture(path)
    fdir = results + os.path.sep + avi_name + os.path.sep + "imgs"
    os.mkdir(fdir)
    FPS = get_fps(path) 
    count = 0
    while True:
        frames ,image = vidcap.read() # reads frames from the video
        if frames: # check if more video is left to extract images/frames
            fname = fdir + os.path.sep + str(count) + '.tiff'
            #print(fname)
            cv2.imwrite(fname, image) # saves the image/frame to the specified directory
            #print("Extracted " + fname)
            count += 1 # increasing counter by one 
        else:
            break
    vidcap.release() # Release space and windows 
    cv2.destroyAllWindows()
    print('Images extracted')

    #Start thresholding
    fms = pims.open(fdir + os.path.sep + '*.tiff')
    img_properties = pd.DataFrame([])
    f = 0 # initiate counter
    test_img = fms[-1] # Using the last image to set threshold
    test_gray = rgb2gray(test_img[:,:,:3]) #turn image to grayscale
    test_blur = cv2.GaussianBlur(test_gray, (7, 7), 0) # smoothing the image using Guassian Blur with a 7x7 kernel size - reference: https://www.geeksforgeeks.org/python-opencv-smoothing-and-blurring/
    # Using Multi-Otsu to find a threshold value - reference: https://scikit-image.org/docs/stable/auto_examples/segmentation/plot_multiotsu.html
    thresholds = threshold_multiotsu(test_blur, classes = 5) # classes specifies the no. of different threshold regions for dividing the smoothened grayscale image.
    regions = np.digitize(test_blur, bins=thresholds)

    #displaying thresholds:
    fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(10, 3.5))
    ax[0].imshow(test_img)
    ax[0].set_title('Original Image')
    ax[0].axis('off')
    ax[1].imshow(test_blur)
    ax[1].set_title('Smoothened Image')
    ax[1].axis('off')
    ax[2].imshow(regions, cmap='jet')
    ax[2].set_title("Thresholded regions by Otsu's method")
    ax[2].axis('off')
    plt.subplots_adjust()
    plt.show()

    proceed = False
    while proceed == False: #user enters threshold
        rgn = int(input("Enter the threshold value you want to use for image processing based on the region map (e.g. 0, 1, 2,..)= ")) # the plot gives a number when you hover over each region. Enter this number here
        if type(rgn) != int:
            print("Please enter an appropriate integer value")
        else:
            tsh = thresholds[rgn-1] # threshold value index for the corresponding region is region index - 1
            test_binary = test_blur < tsh 
            plt.imshow(test_binary)
            plt.title('Binarized Image')
            plt.show()
            q = input("Threshold OK? Yes/No: ")
            if q == 'Yes' or q == 'yes' or q == 'YES' or q =='y':
                proceed = True
                print("Using a threshold value of ", round(tsh, 3), " for the image processing. Changing this value WILL affect the results of your analysis")
    
    for img in fms:
        gscale = rgb2gray(img[:,:,:3]) # converting image to grayscale, [:,:,:3] - specifies to use only 3 channels
        gauss_blr = cv2.GaussianBlur(gscale, (7, 7), 0) # smoothing the image using Guassian Blur with a 7x7 kernel size - reference: https://www.geeksforgeeks.org/python-opencv-smoothing-and-blurring/ 
        # Using the threshold value from user input to convert all the images to a binary
        binary = gauss_blr > tsh
        label = measure.label(binary) # labels the object in the frame
        properties = measure.regionprops(label)
        if len(properties) < 1: #CASE 1: no image properties = no object
            attr = []
            print('Error: No obj detected') 
        elif len(properties) == 1: #CASE 2: 1 object
            attr = []
            f = f + 1 # update counter
            for obj in properties:
                centroid = [obj.centroid] # centroid of each particle
                cpy = centroid[0][0] # x coordinate of the centroid -> https://scikit-image.org/docs/0.19.x/user_guide/numpy_images.html#coordinate-conventions
                cpx = centroid[0][1] # y coordinate of the centroid 
                alist = [obj.area, cpx,  cpy, obj.major_axis_length, obj.minor_axis_length, f] # list of calculated features of the particle
                attr.append(alist)
        else: #CASE 3: multiple objects
            attr = []
            print(f"Error: Multiple objs detected")
            for obj in properties:
                centroid = [obj.centroid]
                cpy = centroid[0][0] # x coordinate of the centroid -> https://scikit-image.org/docs/0.19.x/user_guide/numpy_images.html#coordinate-conventions
                cpx = centroid[0][1] # y coordinate of the centroid 
                alist = [obj.area, cpx,  cpy, obj.major_axis_length, obj.minor_axis_length, f]
                if alist[0] < 3: #ignore object if it's area is smaller than this threshold
                    print('object too small')
                elif alist[0] > 25: #ignore object if it's area is greater than this threshold
                    print('object too big')
                else: #if object is within the bounds, we keep it
                    attr.append(alist)
        img_props = pd.DataFrame(attr, columns=['area','x','y','Majoraxis','Minoraxis','frame']) # specifying column names    
        img_properties = pd.concat([img_properties, img_props]) # concatenates data of each frame 
    img_properties.to_csv(results + os.path.sep + avi_name + os.path.sep + "frame-properties-df.csv") #exporting frame properties
    #dframe = pd.read_csv(results + os.path.sep + avi_name + os.path.sep + "frame-properties-df.csv")
    centroid_coords = img_properties[["x", "y"]].to_numpy() # coordinates of the centroid of the cell in each frame
    x = img_properties["x"].to_numpy()
    y = img_properties['y'].to_numpy()
    #   Using centroids from OVERLAPPING windows to get the center of rotation
    
    print("Calculating center of rotation...")
    windowsize = FPS * 10 # window size is framerate x 10
    centre_X = [] #x center of rotation
    centre_Y = [] #y center of rotation
    for i in range(0, len(centroid_coords)):
        if i <= len(centroid_coords) - windowsize:
            j = int(i + windowsize)
            ctd_slice = centroid_coords[i:j]
            xc, yc, r, sigma = kmh(ctd_slice) #circle fitting based on centroid coordinates, I use kmh here. I've tried using different fits (such as Taubin) but it doesn't make much of a difference
            centre_X.append(xc)
            centre_Y.append(yc)
        else:
            #dealing with edge cases
            shift_to_left_by = int(i - (len(centroid_coords) - windowsize))
            shifted_i = i - shift_to_left_by
            ctd_slice = centroid_coords[shifted_i:len(centroid_coords)]
            xc, yc, r, sigma = kmh(ctd_slice)
            centre_X.append(xc)
            centre_Y.append(yc)
    cdata = {'x': centre_X, 'y': centre_Y}
    cframe = pd.DataFrame(cdata)
    cframe.to_csv(results + os.path.sep + avi_name + os.path.sep + 'center-coordinates.csv') #exporting center coordinates
    # Plotting trajectory
    centroid_X = centroid_coords[:,0]
    centroid_Y = centroid_coords[:,1]
    plt.scatter(centroid_X, centroid_Y)
    plt.savefig(results + os.path.sep + avi_name + os.path.sep + 'trajectory-scatterplot.png', dpi = 300)

    #clear figure + deleting images
    print('Finishing analysis...')
    plt.clf()
    shutil.rmtree(fdir)

    #Saving inputs to params.csv in results folder
    params = {'FPS': [FPS], 'vp': [directory], 'rp': [results]}
    df = pd.DataFrame(params)
    pdir = results + os.path.sep + 'params.csv'
    df.to_csv(pdir, index=False)