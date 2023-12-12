# -*- coding: utf-8 -*-
"""
These are functions that were created by Vihara for Tim to analyze height + width 
"""
import numpy as np
import cv2 as cv
import shapely

def drawLabel(image, contour, num):
    '''
    draws label num directly on image at the center of mass of the contour
    '''
    M = cv.moments(contour)
    cx= int(M['m10']/M['m00'])
    cy= int(M['m01']/M['m00'])
    cv.putText(image, text= str(num), org=(cx-5,cy),
        fontFace= cv.FONT_HERSHEY_SIMPLEX, fontScale=2, color=(0,0,0),
        thickness=3, lineType=cv.LINE_AA)
    
    
def leftToRight(contours):
    '''
    return the array of contours sorted from left to right according to their center of mass
    '''
    com_x = []
    
    for c in contours:
        M = cv.moments(c)
        com_x.append(M['m10']/M['m00'])
        
    return np.argsort(com_x)


def getSlopes(points):
    '''
    points: [x,y,width, height] of rectangle 
    returns: vertical slope, horizontal slope
    '''
    vertical = False
    
    #check if we have vertical line
    if points[1][0]-points[0][0] == 0:
        s1 = None
        vertical = True
    else:
        s1 = (points[1][1] - points[0][1])/(points[1][0]-points[0][0])
        
     #check if we have vertical line    
    if points[2][0] - points[1][0] == 0:
        s2 = None
        vertical = True
    else:      
        s2 = ( points[2][1] - points[1][1])/(points[2][0] - points[1][0])
    
    #always return vertical line first
    if vertical:
        if(s1 is None):
            return s1, s2 
        else:
            return s2, s1 
    else: 
        if abs(s1) >= abs(s2):
            return s1, s2
        else:
            return s2, s1
    

def getLinePoints(x1, y1, lenP, slope):
    '''
    x1,y1: center coordinate of desired line 
    lenP: full length of line 
    slope: slope of line
    
    returns x,y arrays 
    '''
    
    if slope is None:
        x = np.full(shape=(int(lenP*2)), fill_value=x1)
        y = np.linspace(-(lenP/2),lenP/2, int(lenP*2)) + y1
        return x, y 
    else:        
        x = np.linspace(-(lenP/2),lenP/2, int(lenP*2)) + x1
        b = -slope*x1 +  y1
        
        return x, x*slope + b
    
def euclidDist(x1, y1, x2, y2):
    '''
    x1: first set of x coordinate(s), 
    y1: first set of y coordinate(s), 
    x2: second set of x coordinate(s), 
    y2: first set of y coordinate(s)
    returns: euclidan distance between points as int or array
    '''
    return np.sqrt((x2-x1)**2 + (y2-y1)**2)

def getPointsofObject(interPoints):
    '''
    interPoints: intersection geometry returned by shapely
    returns: x,y coordinate of point
    '''
    pointType = shapely.get_type_id(interPoints)
    x,y = [], []
    
    if(pointType == 4):
        interPoints = interPoints.geoms
         
        for p in interPoints:
            x.append(p.x)
            y.append(p.y)
        
    return x,y

def getMaxDist(x,y):
    '''
    x,y : coordinate arrays
    returns: maximum distance between points
    '''
    maxDist = -1
    
    for i in range(len(x)):
        temp = euclidDist(x, y, x[i], y[i])
        
        if(np.max(temp) > maxDist):
            maxDist = np.max(temp)
            
    
    return maxDist


def calcDistance(x_points, y_points, w, s, realContour):
    allWidths = []
    
    for p in range(len(x_points)):
        #create horizontal line
        nx, ny = getLinePoints(x_points[p], y_points[p], w, s)
        stack = np.stack((nx, ny), axis=-1)
        lineString = shapely.geometry.LineString(stack)
        
        if(lineString.intersects(realContour)):
            interPoints = lineString.intersection(realContour)
            a,b = getPointsofObject(interPoints)
           
            allWidths.append(getMaxDist(a, b))
      
    return np.array(allWidths)