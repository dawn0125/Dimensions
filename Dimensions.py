# IMPORT STATEMENTS 
import matplotlib.pyplot as plt
import numpy as np
import cv2 as cv
import os
import shapely
import Vihara.Functions as vi
import pandas as pd
from scipy import ndimage

'''
This was done in collaboration with Vihara. The functions and scripting used to 
extract contours was done by Dawn, the functions and scripting used to measure the 
contours was done by Vihara. Any function starting with "vi" was done by vihara. 
For more information about her work, follow this link: https://github.com/ViharaJ/GetDimensions

How to use: 
    1. Change inDir to directory of images to be analyzed 
    2. Change excelPath to the place where you would like your excel file to be saved 
    3. Change scale if it is not already correct 
'''

# Functions
def threshManual(img, lower, upper):
    '''
    thresh according to bins added manually 
    '''
    img = ndimage.gaussian_filter(img, 2, mode='nearest')
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    ret, thresh = cv.threshold(gray, lower, upper, cv.THRESH_BINARY)
    return thresh
    

def threshOtsu(img):
    '''
    img: image array 
    thresh: black and white image array 

    '''
    img = ndimage.gaussian_filter(img, 2, mode='nearest')
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    ret, thresh = cv.threshold(gray, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
    return thresh

def morph(img):
    '''
    perform morphological operations to remove noise
    '''
    kernel = cv.getStructuringElement(cv.MORPH_RECT,(6,6))
    closed = cv.morphologyEx(img, cv.MORPH_CLOSE, kernel)
    
    return closed 

def findContour(img):
    if np.ndim(img) != 2:
        img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    contours, hierarchy = cv.findContours(img, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    
    return contours 

def findAreas(contours):
    '''
    contours: image array with contours found 
    area: array with area of each contour 

    '''
    area = []
    for cnt in contours:
        area.append(cv.contourArea(cnt))
    return np.asarray(area)

def cntsOI(cnts, lower, upper):
    '''
    return indices of contours of interest 
    '''
    areas = findAreas(cnts)
    smalltobig = np.argsort(areas)
    
    i = smalltobig[lower:upper]
    
    return i

def extractROI(contour):
    """
    contours: image array with contours found 
    ROI: image array with region of interest
    """
    x,y,w,h = cv.boundingRect(contour) # draws a straight rectange around the contour 
    ROI = img[y:y+h, x:x+w] # crops image with array indexing 
    return ROI

def findHeights(cnts, cntsOI):
    '''
    cnts: image array of contours 
    cntsOI: indices of contours of interest 
    contour_heights: list of heights of the contours 

    '''
    cnt_heights = []
    for i in cntsOI:
        x,y,w,h = cv.boundingRect(cnts[i]) 
        cnt_heights.append(h) # add heights to cnt heights 
    return cnt_heights

def checkContour(cnts, cntsOI, expected):
    '''
    every actual height must be at least 90% the expected height 

    '''
    cnt_heights = findHeights(cnts, cntsOI)
    for height in cnt_heights: 
        if 0.9 * expected <= height:
            continue
        else: 
            return False
    return True

'''
MAIN
'''
excelPath = "//wp-oft-nas/HiWis/GM_Dawn_Zheng/Vihara's Scripts"
inDir = '//wp-oft-nas/HiWis/GM_Dawn_Zheng/Arvid/Magnesium Walls for Dawn/Post Processed'
acceptedFileTypes = ["jpg", "png", "tif"]
df = pd.DataFrame(columns=['Image_Name', 'Position', 'Average_Height (mm)', 'Max_Height (mm)', 'Average_Width (mm)', 'Max_Width  (mm)', 'Area  (mm^2)'])
scale = 5.88 

# threshing method, (127, 255) is a standard place to start
manual_threshing = False
thresh_upper_bound = 255
thresh_lower_bound = 127 

# indices of contours to be extracted based on size 
cnt_lower_bound = -5
cnt_upper_bound = -2

# DAWN SCRIPT TO EXTRACT CONTOURS
# for every picture in your directory, to extract the contours for analysis 
for i in os.listdir(inDir): 
    if( '.' in i and i.split('.')[-1] in acceptedFileTypes):
        f = inDir + '/' + i
        print('Processing ' + i)
        
        # read img
        img = cv.imread(f) 
        
        # extract img height for morph checker
        img_height = np.shape(img)[0] 
        
        # copy img for summary img
        summary_image = img.copy() 
    
        # different threshing methods 
        if manual_threshing == True:
            thresh = threshManual(img, thresh_lower_bound, thresh_upper_bound)
        elif manual_threshing == False:
            thresh = threshOtsu(img)
        
        # try to morph first (19/30 success rate)
        morph_img = morph(thresh)
        cnts = findContour(morph_img) 
        indices = cntsOI(cnts, cnt_lower_bound, cnt_upper_bound)
       
        # checking contours, excluding morphology if contours are too short
        if checkContour(cnts, indices, img_height) == False:
            cnts = findContour(thresh)
            indices = cntsOI(cnts, cnt_lower_bound, cnt_upper_bound)
        

# VIHARA SCRIPT TO FIND WIDTH AND HEIGHT
        contourCounter = 1
        for j in indices:
            cont = cnts[j]
            
            #Draw rect
            rect = cv.minAreaRect(cont)
            height = rect[1][0]
            width = rect[1][1]
            
            #get coords of box
            box = cv.boxPoints(rect)
            box = np.intp(box)
        
            #get center of mass of contour
            M = cv.moments(cont)
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
    
        
            #create shapely Object for regolith
            rCont = np.squeeze(cont, axis=1)
            polyLine = shapely.geometry.LineString(rCont)
      
            #get slopes of line
            vslope, hslope = vi.getSlopes(box)
            
            #generate line going length wise
            vx, vy = vi.getLinePoints(cx, cy, height, vslope)
        
            #generate line going width wise
            hx, hy = vi.getLinePoints(cx, cy, width, hslope)    
            
        
            # calculate all widths
            reg_widths = vi.calcDistance(vx, vy, width, hslope, polyLine)*scale
    
            # calculate all heights
            reg_heights = vi.calcDistance(hx, hy, height, vslope, polyLine)*scale
          
            
            plt.title(i + ' ' + str(contourCounter))
            plt.rcParams["figure.figsize"] = plt.rcParamsDefault["figure.figsize"]
            plt.gca().invert_yaxis()
            plt.plot(*polyLine.xy)
            x_left, x_right = plt.gca().get_xlim()
            y_low, y_high = plt.gca().get_ylim()
            # plt.gca().set_aspect(abs((x_right-x_left)/(y_low-y_high))/aspect)
            
            plt.show()
            
            if(len(reg_heights) > 0 and len(reg_widths) > 0):
                cv.drawContours(img, [cont], -1, (0,255,0), 3)
                vi.drawLabel(img, cont, contourCounter)
                print("Image: ", i)
                print("Average height: ", np.average(reg_heights))
                print("Max height: ", np.max(reg_heights))
                print("Average width: ", np.average(reg_widths))
                print("Max width: ", np.max(reg_widths))
                print("Area: ", cv.contourArea(cont)*scale**2)
                print("\n")
                
                
                
                df.loc[len(df)] = [i, contourCounter,np.average(reg_heights), np.max(reg_heights),
                                   np.average(reg_widths), np.max(reg_widths), cv.contourArea(cont)*scale**2]
                
                contourCounter = contourCounter + 1
                
                plt.imshow(img)
                plt.show()
    
    # uncomment if you want to save summary img
    #cv.imwrite(destPath  + '/' + i, img)
    #print("Wrote image, ", i) 
    
df.sort_values(["Image_Name", "Position"], inplace=True)
df.to_excel(excelPath+'/'+"Avearge_Dimensions_White.xlsx", index=False)

    