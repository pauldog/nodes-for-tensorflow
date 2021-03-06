"""A visual programming tool for use with Tensorflow
by Paul Bird
You will need to install: wxpython, pil, tensorflow, numpy, opencv
"""


import random
import os
import math
import sys
import threading
import numpy as np
import wx
import tensorflow as tf
import PIL.Image
import PIL.ImageDraw
import PIL.ImageTk
#import PIL.ImageFont
#import aggdraw
import json
import inspect
import about
import time
import json
import cv2
import about
#import skvideo.io as sk

#font = PIL.ImageFont.truetype("Arialbd.ttf",30)

customNodes = []

camera = None

#Create list of tensorflow functions
tfFunctions = ["functions","add","subtract","multiply","divide","assign","reshape",""]
for name in dir(tf):
    obj = getattr(tf, name)
    if inspect.isfunction(obj) and not name[0].istitle():
        tfFunctions.append(name)

tfNNFunctions = ["tf.nn"]
for name in dir(tf.nn):
    obj = getattr(tf.nn, name)
    if inspect.isfunction(obj) and not name[0].istitle():
        tfNNFunctions.append(name)

tfLayerFunctions = ["tf.layers"]
for name in dir(tf.layers):
    obj = getattr(tf.layers, name)
    if inspect.isfunction(obj) and not name[0].istitle():
        tfLayerFunctions.append(name)

#tf.nn

updateSpeed = 1

class MainWindow(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, "Nodes for Tensorflow")
        #self.SetDoubleBuffered(True)
        self.SetInitialSize((WIDTH,HEIGHT))
        self.SetPosition((0,0))
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.timer = wx.Timer(self, 101)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer.Start(updateSpeed)    # 1 second interval
        #self.Maximize(True)
        

    def OnClose(self, event):
        print("On Close")
        self.timer.Stop()
        if camera!=None:
            camera.release()
        self.Destroy()

    def OnTimer(self, event):
        update()

WIDTH = 1280#int(window.winfo_screenwidth()/1)
HEIGHT = 720#int(window.winfo_screenheight()/2)

WIDTH = int(1920/1.25)
HEIGHT = int(1080/1.25)


sess = tf.Session()

app = wx.App(False)
window = MainWindow()
window.SetTitle("Visual Programming with Tensorflow")

fullscreen = not True
#window.wm_attributes("-topmost", 1)
if fullscreen:
    WIDTH = window.winfo_screenwidth()
    HEIGHT = window.winfo_screenheight()
    
    ##PUT FULLSCREEN CODE HERE##

img = PIL.Image.new("RGB", (WIDTH, HEIGHT), "black")
#dc2 = aggdraw.Draw(img)
dc = PIL.ImageDraw.Draw(img)


#pen = aggdraw.Pen("white", 1)
#brush= aggdraw.Brush("red")

def updateImage():
    bitmap = bitmapFromPIL(img)
    label.SetBitmap(bitmap)


class Input:
    node = 0
    def __init__(self, node, output):
        self.node = node
        self.output = output
    value = 0

def drawBezier(dc, points):
    (x1, y1, x2, y2, x3, y3, x4, y4) = points
    steps = 50
    X = x1
    Y = y2
    for t in range(1, steps+1):
        a = t*1.0/steps
        b = (1-a)
        x = b*b*b*x1 + 3*b*b*a*x2 + 3*b*a*a*x3 + a*a*a*x4
        y = b*b*b*y1 + 3*b*b*a*y2 + 3*b*a*a*y3 + a*a*a*y4
        dc.line((X, Y, x, y), fill=(255, 255, 255))
        X = x
        Y = y


class Node:
    x = 50
    y = 50
    height = 60
    width = 80
    titleHeight = 13
    drag = False
    name = "Image"
    inputs = [0, 0]
    color = (0, 0, 255)
    inputNames = ["a", "b", "c", "d", "e", "f", "g", "h"]
    outputs = []
    value = 0
    type = ""
    showvalue = True
    issetup = True

    def __init__(self):
        global currentNode
        self.inputs = [0, 0]
        self.outputs = [Input(self, 0)]
        if currentNode:
            self.x = currentNode.x+currentNode.width + 40
            self.y = currentNode.y
        currentNode = self

    def setup(self):
        self.issetup = True
        for n in self.inputs:
            if n != 0:
                if n.node != 0 and not n.node.issetup:
                    n.node.setup()

    def draw(self, dc):
        self.drawBackground(dc)
        if self.showvalue:
            self.showValue(dc)
        self.drawForeground(dc)

    def calc(self):
        z = 0

    def drawBackground(self, dc):
        (r, g, b) = self.color
        normalColor = self.color
        darkColor = (int(r/2), int(g/2), int(b/2))
        lightColor = (int((255+r)/2), int((255+g)/2), int((255+b)/2))
        if self==currentNode:
             dc.rectangle((self.x-2, self.y-1, self.x+self.width+1, self.y+self.height+1), outline=lightColor, fill=normalColor)
        
        dc.rectangle((self.x-1, self.y, self.x+self.width, self.y+self.titleHeight), outline=lightColor, fill=normalColor)


        title = self.name
        if self.value != 0 and self.type != "value" and self.type != "optimizer":
            title += " "+str(self.value.get_shape())
        dc.text((self.x+5, self.y+1), title+"\0")
        dc.rectangle((self.x-1, self.y+self.titleHeight, self.x+self.width, self.y+self.height),
                     outline=lightColor, fill=darkColor)
        y = self.y+len(self.inputs)*self.spacing + self.titleHeight
        dc.line((self.x-1, y, self.x+self.width, y), fill=lightColor)


    circCenter = []
    circInputCenter = []
    spacing = 16

    def drawForeground(self, dc):
        circleSize = 6
        self.circInputCenter = []
        for n in range(0, len(self.inputs)):
            y = self.y+self.titleHeight + self.spacing * n + 5
            x = self.x+5
            self.circInputCenter.append((x+circleSize/2, y+circleSize/2))
            dc.ellipse((x, y, x+circleSize, y+circleSize), fill=(255, 255, 0))
            if n < len(self.inputNames):
                dc.text((x+10, y-3), self.inputNames[n]+"\0", fill=(255, 255, 255))

            #dc2.ellipse((x,y ,x+circleSize,y+circleSize),pen,brush)
            if self.inputs[n] != 0:
                node2 = self.inputs[n].node
                X = node2.x + node2.width - 5 - circleSize
                Y = node2.y + node2.titleHeight + 5 + self.spacing * self.inputs[n].output
                #dc.line((x+circleSize/2, y+circleSize/2 , X +circleSize/2,Y + circleSize/2 ) ,fill=(255,255,0) )
                away = 50
                drawBezier(dc,
                           (x+circleSize/2, y+circleSize/2,
                            x+circleSize/2-away, y+circleSize/2,
                            X+circleSize/2+away, Y+circleSize/2,
                            X+circleSize/2, Y+circleSize/2)
                          )
        #dc2.flush()

        self.circCenter = []
        for n in range(0, len(self.outputs)):
            y = self.y+self.titleHeight + self.spacing * n + 5
            x = self.x+self.width-5-circleSize
            self.circCenter.append((x+circleSize/2, y+circleSize/2))
            dc.ellipse((x, y, x+circleSize, y+circleSize), fill=(255, 255, 0))

    def inside(self, pos):
        (px, py) = pos
        return px > self.x and py > self.y and px < self.x+self.width and py < self.y+self.height

    def insideShowButton(self, pos):
        (px, py) = pos
        buttonSize =  self.titleHeight
        return px > self.x+self.width-buttonSize and py > self.y and px < self.x+self.width and py < self.y+buttonSize

    def insideOutput(self, pos):
        global dragStartPos
        (px, py) = pos
        for n in range(0, len(self.circCenter)):
            (cx, cy) = self.circCenter[n]
            if (px-cx)*(px-cx)+(py-cy)*(py-cy) < 8*8:
                dragStartPos = (cx, cy)
                return n
        return -1

    def insideInput(self, pos):
        (px, py) = pos
        for n in range(0, len(self.circInputCenter)):
            (cx, cy) = self.circInputCenter[n]
            if (px-cx)*(px-cx)+(py-cy)*(py-cy) < 8*8:
                dragStartPos = (cx, cy)
                return n
        return -1

    def showValue(self, dc):
        yOffset = len(self.inputs)*self.spacing + 5
        xOffset = 5
        xPadding = 15

        if self.value == 0:
            return
        if self.type == "value":
            t = str(self.value)
            dc.text((self.x+xOffset, self.y+yOffset+self.titleHeight), t+"\0")
            charWidth = 6
            self.width = max(len(t)*charWidth+xOffset+xPadding, self.width)
            return
        try:    
            array = sess.run(self.value, feed_dict={i: d for i, d in zip(placeholders, callbackvalues)})
        except Exception as e:
            SetText(infoLabel, "Error")
            return
        if self.type == "optimizer":
            return
        shape = self.value.get_shape()
        if shape._dims is None:
            return
        #self.name = str(shape)
        if len(shape) >= 2:
            if(shape[0]+self.titleHeight>self.height):
                 self.height = int(shape[0])+self.titleHeight
            if(shape[1] > self.width):
                 self.width = int(shape[1])

        if len(shape) == 2:
            if shape[0]<=4 and shape[1]<=4:
                maxt = 0
                for y in range(0, shape[0]):
                    t = str(array[y])
                    maxt = max(len(t),maxt)
                    dc.text((self.x+xOffset, self.y+yOffset+self.titleHeight+y*self.spacing), t+"\0")
                self.height = int(shape[0])*self.spacing+self.titleHeight+yOffset
                charWidth = 6
                self.width = max(maxt*charWidth+xOffset+xPadding, self.width)
            else:
                if array.dtype == np.complex128 or array.dtype==np.complex64:
                    data = np.reshape(array,(shape[0], shape[1],1))
                    data = np.concatenate( (
                        (np.angle(data)*255/np.pi/2).astype(np.uint8),
                        #np.full((shape[0],shape[1],1),255).astype(np.uint8),
                        (np.clip(np.abs(data),0,1) *255).astype(np.uint8),
                        (np.clip(1.0/np.abs(data),0,1) *255*1).astype(np.uint8)
                        ) ,axis=2 )
                    image = PIL.Image.fromarray(data, mode="HSV")
                    img.paste(image,(self.x, self.y+self.titleHeight))
                else:
                    data = np.reshape(array*255, (shape[0], shape[1])).astype(np.uint8)
                    image = PIL.Image.fromarray(data, mode="L")
                    #scale image
                    m = max(image.width, image.height) 
                    if m < 128:
                        image = image.resize( [int(128.0/m*image.width), int(128.0/m*image.height)] , PIL.Image.BICUBIC )
                    if(image.width > self.width):
                        self.width = image.width
                    if(image.height > self.height):
                        self.height = image.height + self.titleHeight

                    img.paste(image,(self.x,self.y+self.titleHeight))
        elif len(shape) == 3:
            if shape[2] == 3: #RGB
                data = np.reshape(array*255,(shape[0], shape[1], shape[2])).astype(np.uint8)
                image = PIL.Image.fromarray(data, mode="RGB")
                img.paste(image, (self.x, self.y+self.titleHeight))
            elif shape[2] == 2: #?
                iscomplex = 1 #(doesnt do anything)
        elif len(shape) <= 1:
            if self.value.dtype == tf.string:
                if len(shape)==0:
                    t = array.decode("latin-1")
                else:
                    return
                if len(t)>1000:
                    t = t[:1000]+"..."
            else:
                t = str(array)

            t1 = t.split("\n")
            maxW = 0
            for n in range(0,len(t1)):
                dc.text((self.x+xOffset, self.y+yOffset+self.titleHeight+n*self.spacing), t1[n]+"\0")
                maxW = max(len(t1[n]), maxW)
            charWidth = 6
            self.width = max(maxW * charWidth+xOffset+xPadding, self.width)
            self.height = max(len(t1)*self.spacing+yOffset+self.titleHeight, self.height)

dragStartPos = (0,0)


class ConstantNode(Node):
    value = 0
    height = 30
    type="constant"
    name="Constant"
    inputs = []
    color = (0,128,0)
    val = 0
    def __init__(self):
        Node.__init__(self)
        self.inputs=[]
    def setup(self):
        Node.setup(self)
        self.value = tf.constant(self.val)
        self.outputs[0].value=self.value

class PlaceholderNode(Node):
    value = 0
    height = 30
    name="Placeholder"
    inputs = []
    color = (255,0,128)
    val = 0
    type="placeholder"
    def __init__(self):
        Node.__init__(self)
        self.inputs=[]
    def setup(self):
        Node.setup(self)
        shape= np.array(self.val()).shape     
        self.value = tf.placeholder(tf.float32,shape=shape)
        placeholders.append(self.value)
        def callback():
            return self.val()
        callbacks.append(callback)
        self.outputs[0].value=self.value

class ListNode(Node):
    value = 0
    height = 30
    width = 100
    type="value"
    name="Value"
    inputs = []
    color = (200,0,0)
    val = 0
    def __init__(self):
        Node.__init__(self)
        self.inputs=[]
    def setup(self):
        Node.setup(self)
        self.value = self.val
        self.outputs[0].value=self.value

class VariableNode(Node):
    value = 0
    height = 30
    width = 100
    val = 0
    color = (128,0,128)
    name="Variable"
    def __init__(self):
        Node.__init__(self)
        self.inputs=[]
    def setup(self):
        Node.setup(self)
        self.value = tf.Variable(self.val)
        sess.run(tf.initialize_variables([self.value]))
        self.outputs[0].value=self.value


class RandomNode(VariableNode):
    value = 0
    height = 30
    width = 100
    name="Random Float32"
    op = 0
    def __init__(self):
        Node.__init__(self)
        self.inputs=[]
    def setup(self):
        Node.setup(self)
        self.value = tf.cast(tf.random_uniform([],-0.5,0.5),tf.float32)
        self.outputs[0].value = self.value 

class Random3x3(VariableNode):
    value = 0
    height = 50
    width = 100
    name="Random 3x3 Matrix"
    op=0
    def __init__(self):
        Node.__init__(self)
        self.inputs=[]
    def setup(self):
        Node.setup(self)
        self.value = tf.cast(tf.random_uniform([3,3],-0.5,0.5),tf.float32)
        self.outputs[0].value = self.value

class Random3(VariableNode):
    value = 0
    height = 30
    width = 100
    name="Random 3Vector"
    op = 0
    def __init__(self):
        Node.__init__(self)
        self.inputs=[]
    def setup(self):
        Node.setup(self)
        self.value = tf.cast(tf.random_uniform([3],-0.5,0.5),tf.float32)
        self.outputs[0].value = self.value 


class DotNode(Node):
    name="A.B"
    height = 50
    width = 100
    inputs = [0,0]
    showvalue = not False
    def setup(self):
        Node.setup(self)
        if self.inputs[0]!=0 and self.inputs[1]!=0:
            A = self.inputs[0].value
            B = self.inputs[1].value
            shape1 = A.get_shape()
            shape2 = B.get_shape()
            #contract last indices
            if len(shape1)>0 and len(shape2)>0:
                a = len(shape1)-1
                b = len(shape2)-1
                self.value = tf.reduce_sum( A * B, a )
                self.outputs[0].value = self.value

customNodes.append(DotNode.__name__)

#Node takes an image and draws a filled circle
class DrawCircle(Node):
    name="Draw Circle"
    height = 100
    width = 100
    inputs = [0,0,0,0]
    inputNames = ["image ref","position","radius","RGB"]
    color = (255,0,0)
    showvalue = not False
    def __init__(self):
        Node.__init__(self)
        self.inputs = [0,0,0,0]
    def setup(self):
        Node.setup(self)
        if self.inputs[0]!=0:# and self.inputs[1]!=0 and self.inputs[2]!=0 and self.inputs[3]!=0:
            image = self.inputs[0].value
            #position = self.inputs[1].value
            #radius = self.inputs[2].value
            #color = self.inputs[3].value
            #imageSize = tf.shape(image)  #width x height x channels
            #circle = (tf.random_uniform(imageSize) + image)/2
            size = self.inputs[0].value.get_shape()
            w = size[0]
            h = size[1]
            print(str(w)+"................"+str(h))
            uv = np.array([[[u,v] for u in range(0,w) ] for v in range(0,h)])
            uvConst = tf.constant(uv)
            pos = [50,50]
            radius=25
            if self.inputs[1]!=0:
                pos = self.inputs[1].value
            if self.inputs[2]!=0:
                radius = self.inputs[2].value
            d = uv-pos
            circle = tf.cast(tf.reduce_sum(d*d,2) < radius, tf.float32)
            self.value = tf.assign(image , circle  )
            self.outputs[0].value = self.value

customNodes.append(DrawCircle.__name__)

class DrawingNode(Node):
    name="Drawing"
    height = 100
    width = 100
    inputs = [0,0,0,0]
    inputNames = ["image ref"]
    color = (255,0,0)
    showvalue = not False
    coords = []
    def __init__(self):
        Node.__init__(self)
        self.inputs = [0]
    def setup(self):
        Node.setup(self)
        self.coords = CursorPosition() #cursor position node
        self.coords.setup()
        #nodes.append(self.coords)
        if self.inputs[0]!=0:
            image = self.inputs[0].value
            size = self.inputs[0].value.get_shape()
            #type = self.inputs[0].value.type()
            w = size[0]
            h = size[1]
            print(str(w)+"................"+str(h))
            uv = np.array([[[u,v] for u in range(0,w) ] for v in range(0,h)])
            uvConst = tf.constant(uv)
            radius=10
            pos = self.coords.outputs[0].value # - placeholder for topleft
            d = uv-pos
            circle = image + tf.cast(tf.reduce_sum(d*d,2) < radius, tf.float32)
            self.value = tf.assign(image , circle  )
            self.outputs[0].value = self.value

customNodes.append(DrawingNode.__name__)

placeholders = []
callbacks = []
callbackvalues = []

currentNode = 0

minstData = None

def loadMinstData():
    global minstData
    file = open("minst.bytes")
    file.seek(16)
    data = np.fromfile(file, dtype=np.uint8).astype(np.float32)/255.0
    minstData = np.reshape(data,[-1,28,28])
    #print(str(minstData[0]))

minstLabels = None

def loadMinstLabels():
    global minstLabels
    file = open("mnist_labels.bytes")
    file.seek(8)
    minstLabels = np.fromfile(file, dtype=np.byte).astype(np.int32)

class MINSTdata(Node):
    name="MNIST data"
    height = 100
    width = 100
    inputs = []
    inputNames = []
    color = (255,0,0)
    showvalue = not False
    def setup(self):
        loadMinstData()
        Node.setup(self)
        self.value = tf.placeholder(tf.float32,shape=[28,28])
        placeholders.append(self.value)
        callbacks.append(getRandomMINST)
        self.outputs[0].value = self.value

customNodes.append(MINSTdata.__name__)

class MINSTnumber(Node):
    name="MNIST number"
    height = 100
    width = 100
    inputs = []
    inputNames = []
    color = (255,0,0)
    showvalue = not False
    def setup(self):
        loadMinstLabels()
        Node.setup(self)
        self.value = tf.placeholder(tf.float32,shape=[1,10])
        placeholders.append(self.value)
        callbacks.append(getRandomMINSTNumber)
        self.outputs[0].value = self.value

customNodes.append(MINSTnumber.__name__)

def getRandomMINSTNumber():
    #print("labels="+str(len(minstLabels)))
    i = randomNumber % len(minstLabels)
    num = minstLabels[i]
    val = np.zeros([1,10])
    val[0][num] = 1
    return val

def getRandomMINST():
    #print("data="+str(len(minstData)))
    #print("shape="+str(np.shape(minstData)))
    i = randomNumber % len(minstData)  #random.randint(0, len(minstData)-1)
    return minstData[i]

#Node takes an image and draws a filled circle
class CursorPosition(Node):
    name="Cursor Position"
    height = 30
    width = 100
    inputs = []
    inputNames = []
    color = (255,0,0)
    showvalue = not False
    def __init__(self):
        Node.__init__(self)
        self.inputs=[]
    def setup(self):
        Node.setup(self)
        self.value = tf.placeholder(tf.int32,shape=[2])
        placeholders.append(self.value)
        callbacks.append(getMousePos)
        self.outputs[0].value = self.value

customNodes.append(CursorPosition.__name__)

WEBCAM_WIDTH=320
WEBCAM_HEIGHT=240


class WebcamNode(Node):
    name="Webcam Node"
    height = 100
    width = 100
    inputs = []
    inputNames = []
    color = (255,0,0)
    showvalue = not False
    def setup(self):
        global camera
        Node.setup(self)
        if camera==None:
            camera = cv2.VideoCapture(0)
        self.value = tf.placeholder(tf.float32,shape=[WEBCAM_HEIGHT, WEBCAM_WIDTH, 3])
        placeholders.append(self.value)
        callbacks.append(getWebcamImage)
        self.outputs[0].value = self.value

customNodes.append(WebcamNode.__name__)

def getTime():
    return time.clock()

class TimeNode(Node):
    name="Time"
    height = 100
    width = 100
    inputs = []
    inputNames = []
    color = (255,0,0)
    showvalue = not False
    def setup(self):
        Node.setup(self)
        self.value = tf.placeholder(tf.float32,shape=[])
        placeholders.append(self.value)
        callbacks.append(getTime)
        self.outputs[0].value = self.value

customNodes.append(TimeNode.__name__)

#train your neural network or find solutions
class OptimizerNode(Node):
    name="Optimizer"
    height = 50
    width = 100
    inputs = [0,0]
    color = (255,0,0)
    inputNames = ["input","expected"]
    type = "optimizer"
    showvalue = not False
    def setup(self):
        Node.setup(self)
        if self.inputs[0]!=0 and self.inputs[1]!=0:
            A = self.inputs[0].value
            B = self.inputs[1].value
            loss_op = tf.reduce_sum(tf.square(tf.subtract(A,B) ) ) 
            optimizer = tf.train.AdamOptimizer(learning_rate=0.03)
            self.value = optimizer.minimize(loss_op)
            self.outputs[0].value = self.value

class RNNNode(Node):
    inputs = [0, 0]
    outputs = [0, 0]
    inputNames = ["input","state"]
    name = "RNN"
    def __init__(self):
        Node.__init__(self)
        self.outputs = [Input(self, 0),Input(self,1)]
    def setup(self):
        Node.setup(self)

        if self.inputs[0]!=0 and self.inputs[1]!=0:
            INPUT = self.inputs[0].value
            INPUT_STATE = self.inputs[1].value
            SIZE = INPUT.get_shape()[0]
            RNN = tf.contrib.rnn.BasicRNNCell( SIZE ) 
            try:
                OUTPUT, NEW_STATE = tf.nn.dynamic_rnn( RNN , INPUT , initial_state=INPUT_STATE, dtype=tf.float32)
                self.outputs[0].value = OUTPUT
                self.outputs[1].value = NEW_STATE
            except Exception as e:
                SetText(infoLabel, e)

customNodes.append(RNNNode.__name__)

class FullyConnectedSigmoid(Node):
    inputs = [0]
    outputs = [0]
    inputNames = ["input","num nodes"]
    name = "Fully Connected Sigmoid"
    def __init__(self):
        Node.__init__(self)
    def setup(self):
        Node.setup(self)
        if self.inputs[0]!=0 and self.inputs[1]!=0:
            INPUT = self.inputs[0].value
            OUTPUT_SIZE = self.inputs[1].value
            try:
                OUTPUT = tf.contrib.layers.fully_connected( INPUT , OUTPUT_SIZE ,activation_fn=tf.nn.sigmoid)
                self.value = OUTPUT
                self.outputs[0].value = OUTPUT
                sess.run(tf.global_variables_initializer())
            except Exception as e:
                SetText(infoLabel, e)

customNodes.append(FullyConnectedSigmoid.__name__)

class FullyConnectedSoftmax(Node):
    inputs = [0]
    outputs = [0]
    inputNames = ["input","num nodes"]
    name = "Fully Connected Softmax"
    def __init__(self):
        Node.__init__(self)
    def setup(self):
        Node.setup(self)
        if self.inputs[0]!=0 and self.inputs[1]!=0:
            INPUT = self.inputs[0].value
            OUTPUT_SIZE = self.inputs[1].value
            try:
                OUTPUT = tf.contrib.layers.fully_connected( INPUT , OUTPUT_SIZE ,activation_fn=tf.nn.softmax)
                self.value = OUTPUT
                self.outputs[0].value = OUTPUT
                sess.run(tf.global_variables_initializer())
            except Exception as e:
               SetText(infoLabel, e)

customNodes.append(FullyConnectedSoftmax.__name__)

class ConvolutionalLayer(Node):
    inputs = [0]
    outputs = [0]
    inputNames = ["input"]
    name = "Convolutional"
    def __init__(self):
        Node.__init__(self)
    def setup(self):
        Node.setup(self)
        if self.inputs[0]!=0:
            INPUT = self.inputs[0].value
            shape = INPUT.get_shape()
            try:
                if len(shape)==3:
                    INPUT = tf.reshape(INPUT, [1, shape[0], shape[1], shape[2]])
                if len(shape)==2:
                    INPUT = tf.reshape(INPUT, [1,shape[0], shape[1], 1])
                numfilters=3
                if self.inputs[1]!=0:
                    numfilters = self.inputs[1].value
                OUTPUT = tf.layers.conv2d(inputs=INPUT, filters=numfilters, kernel_size=[3, 3], padding="same")
                #if len(shape)==3:
                #    OUTPUT = tf.reshape(OUTPUT,(shape[0],shape[1],shape[2]))
                #if len(shape)==2:
                #    OUTPUT = tf.reshape(OUTPUT,(shape[0],shape[1]))
                self.value = OUTPUT
                self.outputs[0].value = OUTPUT
                sess.run(tf.global_variables_initializer())
            except Exception as e:
                SetText(infoLabel, e)

customNodes.append(ConvolutionalLayer.__name__)

class MaxPoolingLayer(Node):
    inputs = [0]
    outputs = [0]
    inputNames = ["input"]
    name = "Max Pooling"
    def __init__(self):
        Node.__init__(self)
    def setup(self):
        Node.setup(self)
        if self.inputs[0]!=0:
            INPUT = self.inputs[0].value
            shape = INPUT.get_shape()
            try:
                OUTPUT = tf.layers.max_pooling2d(inputs=INPUT, pool_size=[2, 2], strides=2)
                self.value = OUTPUT
                self.outputs[0].value = OUTPUT
                sess.run(tf.global_variables_initializer())
            except Exception as e:
                SetText(infoLabel, e)

customNodes.append(MaxPoolingLayer.__name__)


#General node for any tensorflow function
class FunctionNode(Node):
    name="x"
    inputs = [0,0]
    showvalue = not False
    args = []
    func = 0
    funcCompiled = 0
    def __init__(self,func,args):
        Node.__init__(self)
        self.func=func
        print("func="+func)
        self.funcCompiled = eval(func)
        self.args=args
        self.inputs = [0] * len(args)
        self.height = 16 * len(args) + self.titleHeight
        self.name = self.funcCompiled.__name__
        for a in range(0,len(self.args)):
            if self.args[a]!=0:
                self.inputs[a] = self.args[a].outputs[0]

    def setup(self):
        Node.setup(self)
        fargs=[]
        for a in range(0,len(self.inputs)):
            if self.inputs[a]==0:
                break
            fargs.append(self.inputs[a].value)
        try:
            self.value = self.funcCompiled(*fargs)
            self.outputs[0].value = self.value
        except Exception as e:
            SetText(infoLabel, e)

#Matrix multiplication for each element in a grid
class MatMultNode(Node):
    name="AB"
    height = 50
    width = 100
    inputs = [0,0]
    showvalue = not False
    def setup(self):
        Node.setup(self)
        if(self.inputs[0]!=0 and self.inputs[1]!=0):
            a = len(self.inputs[0].value.get_shape())-1
            b = len(self.inputs[1].value.get_shape())-2
            self.value =tf.tensordot( self.inputs[0].value , self.inputs[1].value , [[a],[b]])
            self.outputs[0].value = self.value

customNodes.append(MatMultNode.__name__)

class WatchNode(Node):
    name="watch"
    inputs = [0]
    def setup(self):
        Node.setup(self)
        if(self.inputs[0]!=0):
            self.value = self.inputs[0].value
            self.outputs[0] = self.value

customNodes.append(WatchNode.__name__)

ar = np.zeros([256,256])
for x in range(0,256):
    for y in range(0,256):
        ar[y][x] = ((x+y)%256)/255.0

W=128
H=128
ar3 = np.zeros([H,W,3]).astype(np.float32)
for x in range(0,W):
    for y in range(0,H):
        ar3[y][x][0] = x*2.0/W-1
        ar3[y][x][1] = y*2.0/H-1


nodes=[]

def defaultNodes():
    global nodes

    X = ConstantNode()
    X.val = ar3

    M = Random3x3()

    MX = MatMultNode()
    MX.inputs[0]=X.outputs[0]
    MX.inputs[1]=M.outputs[0]
    MX.x=500

    XMX = DotNode()
    XMX.inputs[0]=MX.outputs[0]
    XMX.inputs[1]=X.outputs[0]
    XMX.x=800
    XMX.y=300

    B = Random3()

    BX = DotNode()
    BX.inputs[0]=X.outputs[0]
    BX.inputs[1]=B.outputs[0]
    BX.x=800


    XMX_BX = FunctionNode("tf.add",[BX,XMX])
    XMX_BX.x = 1000

    W = WatchNode()
    W.inputs[0]=XMX_BX.outputs[0]

    RNN = RNNNode()

    nodes = [X,M,MX,XMX,B,BX,XMX_BX,RNN]

def defaultNodes2():
    global nodes
    img1 = PIL.Image.open("abc.png").convert("RGB") 
    ar2 = np.array(img1) /256.0

    c1 = ConstantNode()
    c1.value = tf.constant(ar3)
    c2 = ConstantNode()
    c2.value = tf.constant(ar3)

    m = Random3x3()

    u = Random3()

    t=MatMultNode()
    t.inputs[0] = c1.outputs[0]
    t.inputs[1] = m.outputs[0]

    a = DotNode()
    a.inputs[0] = t.outputs[0]
    a.inputs[1] = u.outputs[0]

    w=WatchNode()
    w.inputs[0]=a.outputs[0]

    nodes = [c1,m,t,u,a,w]

def setupNodes():
    for n in nodes:
        n.issetup = False
    for n in nodes:
        if not n.issetup:
            n.setup()

    sess.run(tf.global_variables_initializer())

#defaultNodes()
setupNodes()

draggingObject = 0
draggingOutput = -1
lastPos = (0,0)


############# make menu bar ##############
panel = window# wx.Panel(window, wx.ID_ANY)
vbox = wx.BoxSizer(wx.VERTICAL)
panel.SetSizer(vbox)

menubar = wx.BoxSizer(wx.HORIZONTAL) #wx.Panel(window, wx.ID_ANY)
menubar2 = wx.BoxSizer(wx.HORIZONTAL) # wx.Panel(window, wx.ID_ANY)

vbox.Add(menubar)
vbox.Add(menubar2)

nodeButtons= []#"tf.add","tf.multiply","tf.assign","tf.reshape"]  #tf.reduce_sum,

DERIVE="[astype]"
typeButtons = [DERIVE,  "int32", "int64", "float16", "float32","float64" , "complex64", "complex128" ,"string"]

showDefaultArguments = not True

def buttonPressed(nbName):
    nb=eval(nbName)
    args = inspect.getargspec(nb)
    if args.defaults != None and not showDefaultArguments:
        numArgs = len(args[0])- len(args.defaults)
    else:
        numArgs = len(args[0])
    print(str(inspect.getargspec(nb)[0]))
    n = FunctionNode(nbName,np.zeros(numArgs-0))
    n.inputNames = inspect.getargspec(nb)[0]
    n.setup()
    nodes.append(n)

for nb in nodeButtons:
    button1 = ttk.Button(menubar, text=nb, command = lambda x=nb:buttonPressed(x) )
    button1.pack(side="left")

def listbuttonPressed(event=None):
    b= ListNode()
    setValueOfListNode(b)
    nodes.append(b)

def getValue(v):
    return v.GetValue()

def setValueOfListNode(b):
    v = getValue(inputVar)
    tv = getValue(typeVar)
    if tv == "string":
        val=v
    else:
        val = eval(v)
        if tv!=DERIVE:
            t = getattr(np,tv)
            val = np.array(val).astype(t).tolist()
    b.val=val
    b.setup()

def cusomNodePressed(event=None):
    b=OptimizerNode()
    b.setup()
    nodes.append(b)



def optimizebuttonPressed(event=None):
    #b=CursorPosition()
    #b=DrawCircle()
    b=OptimizerNode()
    b.setup()
    nodes.append(b)

def pbuttonPressed(event=None):
    b=PlaceholderNode()
    b.val = eval("lambda:"+getValue(inputVar))
    b.setup()
    nodes.append(b)

def cbuttonPressed(event=None):
    b = ConstantNode()
    v = getValue(inputVar)
    tv = getValue(typeVar)
    if tv == "string":
        val=v
    else:
        val = eval(v)
        if tv!=DERIVE:
            t = getattr(np,tv)
            val = np.array(val).astype(t)
    b.val=val
    b.setup()
    nodes.append(b)

def vbuttonPressed(event=None):
    b = VariableNode()
    v = getValue(inputVar)
    tv =getValue( typeVar)
    print("v="+str(v))
    if tv == "string":
        val=v
    else:
        val = eval(v)
        if tv!=DERIVE:
            t = getattr(np,tv)
            val = np.array(val).astype(t)
    b.val=val
    b.setup()
    nodes.append(b)

def abuttonPressed(event=None):
    W=256
    H=256
    ar3 = np.zeros([H,W]).astype(np.complex64)
    for x in range(0,W):
        for y in range(0,H):
            ar3[y][x] =  x*2.0/W-1 + (y*2.0/H-1)*1j
    b = ConstantNode()
    b.val = ar3
    b.setup()
    nodes.append(b)


#ttk.Style().configure("TButton",relief="flat", padding=4, background="#000")

def createButton(holder, text="", command=None):
    button = wx.Button(panel, id=wx.ID_ANY, label=text)
    button.Bind(wx.EVT_BUTTON, command)
    holder.Add(button)

def createComboBox(holder, choices=None, command=None):
    combobox = wx.ComboBox(panel, id=wx.ID_ANY, choices=choices, style=wx.CB_READONLY , size = (150,-1))
    combobox.SetSelection(0)
    combobox.Bind(wx.EVT_COMBOBOX, command)
    holder.Add(combobox)
    return combobox

createButton(menubar, text="value", command = listbuttonPressed )
createButton(menubar, text="variable", command = vbuttonPressed )
createButton(menubar, text="constant tensor", command = cbuttonPressed )
createButton(menubar, text="placeholder", command = pbuttonPressed )  
createButton(menubar, text="optimize", command = optimizebuttonPressed )
createButton(menubar, text="argand", command = abuttonPressed )  

inputVar = wx.TextCtrl(panel, value = "[[1.0, 2.0], [3.0, 4.0]]")
menubar.Add(inputVar)
typeVar = createComboBox(menubar, typeButtons, None)

def optionChosen(event):
    buttonPressed("tf."+getValue(optionVar) )

optionVar = createComboBox(menubar, tfFunctions, optionChosen)

def customChosen(event):
    c = eval(getValue(customVar)+"()")
    nodes.append(c)
    resetbuttonPressed(event=None)

customVar = createComboBox(menubar2, customNodes, customChosen)

def optionChosen2(event):
    buttonPressed("tf.nn."+getValue(optionVar2))

def optionChosen3(event):
    buttonPressed("tf.layers."+getValue(optionVar2))

optionVar2 = createComboBox(menubar, tfNNFunctions, optionChosen2)

optionVar3 = createComboBox(menubar2, tfLayerFunctions, optionChosen3)

def deleteNode(event=None):
    global currentNode
    print(str(currentNode))
    if currentNode != 0:
        nodes.remove(currentNode)
    currentNode = 0
    resetbuttonPressed(event=None)


createButton(menubar2 ,text="delete",command=deleteNode)

def loadFile(event=None): 
    clearbuttonPressed(event=None)

    with wx.FileDialog(window, "Select file", wildcard="graphs|*.json",
                    style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
        if fileDialog.ShowModal() == wx.ID_CANCEL:
            return     # the user changed their mind
        filename = fileDialog.GetPath()


    with open('graph_data.json') as data_file:    
        data = json.load(data_file)
    for node in data:
        func = node.get("func", "")
        inputs = node["inputs"]
        type = node["type"]
        if func!="":
            n = eval(type+"('"+func+"',np.zeros(len(inputs)))")
        else:
            n = eval(type+"()")
        n.x = node["x"]
        n.y = node["y"]
        if hasattr(n, "val"):
            n.val = node["val"]
        nodes.append(n)
    index = 0
    for node in data:
        inputs = node["inputs"]
        for i in range(0,len(inputs)):
            if inputs[i]!=-1:
                nodes[index].inputs[i] = nodes[inputs[i]].outputs[0]
        index = index+1

    resetbuttonPressed(event=None)


def saveFile(event=None):
    data=[]
    for node in nodes:
        nodeData={}
        inputs = []
        nodeData["type"] = node.__class__.__name__
        nodeData["x"] = node.x
        nodeData["y"] = node.y   
        if hasattr(node,"val"):
            nodeData["val"] = node.val
        func = getattr(node, "func", 0)
        if func!=0:
            nodeData["func"] = func
        for i in node.inputs:
            if i!=0 and i.node!=0:
                index = nodes.index(i.node)
                inputs.append(index)
            else:
                inputs.append(-1)
        nodeData["inputs"] = inputs
        data.append(nodeData)
    with open('graph_data.json', 'w') as outfile:  
        json.dump(data, outfile , indent=4)

fullScreen=False

def ToggleFullScreen(event=None):
    global fullScreen
    fullScreen = not fullScreen
    window.ShowFullScreen(fullScreen)


createButton(menubar2 ,text="Load Network",command=loadFile)
createButton(menubar2 ,text="Save Network",command=saveFile)





def clearbuttonPressed(event=None):
    global nodes, currentNode
    nodes = []
    resetbuttonPressed(event=None)
    currentNode = None

createButton(menubar, text="clear", command = clearbuttonPressed )


def resetbuttonPressed(event=None):
    global nodes, sess, callbacks, placeholders
    sess.close()
    tf.reset_default_graph()
    callbacks=[]
    placeholders=[]
    for n in nodes:
        n.value = 0
        n.outputs[0].value=0
    sess = tf.Session()
    setupNodes()


"""
resetbutton = ttk.Button(menubar, text="reset", command = resetbuttonPressed )
resetbutton.pack(side="left") 
"""



def getWebcamImage():
    _, image = camera.read()
    image = cv2.resize(image, (WEBCAM_WIDTH, WEBCAM_HEIGHT), 0, 0, cv2.INTER_CUBIC)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)/255.0
    return image

def newWebcamNode(event=None):
    global camera
    camera = cv2.VideoCapture(0)
    c1 = PlaceholderNode()
    c1.val = lambda: getWebcamImage()
    c1.setup()
    nodes.append(c1)
    resetbuttonPressed(event=None)

def loadData(event=None):
    with wx.FileDialog(window, "Select file", wildcard="image files|*.jpg;*.png;*.gif;*.txt|movies files|*.mp4;*.mpg;*.flv|all files|*.*",
                    style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
        if fileDialog.ShowModal() == wx.ID_CANCEL:
            return     # the user changed their mind
        filename = fileDialog.GetPath()

    _, ext = os.path.splitext(filename)
    data=""
    print("Extension = "+ext)
    if ext==".txt":
        with open(filename, 'r',encoding="latin-1" ) as myfile:
            lines= myfile.readlines()
            data =""
            for l in lines:
                if len(l)>1:
                    data+=l
                else:
                    data+=" \n"
    elif ext==".mp4" or ext==".flv" or ext==".mpg":
        cap = cv2.VideoCapture(filename)
        c1 = PlaceholderNode()
        c1.val = lambda: getVideoFrame(cap)
        c1.setup()
        nodes.append(c1)
        resetbuttonPressed(event=None)
        return
    else:
        img1 = PIL.Image.open(filename).convert("RGB") 
        ar2 = np.array(img1) /256.0
        data = np.reshape(ar2,(img1.height, img1.width, 3)).astype(np.float)
    c1 = ConstantNode()
    c1.val = data
    nodes.append(c1)
    resetbuttonPressed(event=None)

createButton(menubar2, text="load data",command = loadData)
createButton(menubar2, text="webcam",command = newWebcamNode)

def getVideoFrame(cap):
    ret, image = cap.read()
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)/255.0
    if not ret:
        cap.set(cv2.CAP_PROP_POS_AVI_RATIO , 0)
        ret, image = cap.read()
    image = cv2.resize(image, (320, 180), 0, 0, cv2.INTER_CUBIC)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)/255.0
    return image


def infoPressed(event=None):
    graph_def = tf.get_default_graph().as_graph_def()
    SetText(infoLabel, "nodes="+str(len(graph_def.node)))
    for node in graph_def.node:
        print(node.name+" : "+node.op)

createButton(menubar, text="graph info", command = infoPressed )

def aboutbuttonPressed(event=None):
    aboutDialog = about.AboutDialog(window)
    aboutDialog.Show()

createButton(menubar, text="about", command = aboutbuttonPressed )

def toggleSpeed(event=None):
    global updateSpeed
    if updateSpeed == 1:
        updateSpeed = 1000
    else:
        updateSpeed = 1
    window.timer.Start(updateSpeed)
    

def changeValue(event=None):
    b=currentNode
    setValueOfListNode(b)

updateChange = True

def updateOnChange():
    print(str(getValue(upc)))
    if getValue(upc) == 1:
        updateChange = True
    else:
        updateChange = False

createButton(menubar2, text="slow", command = toggleSpeed)
createButton(menubar2, text="change value", command = changeValue)
createButton(menubar2 ,text="Full screen",command=ToggleFullScreen)

def bitmapFromPIL( pilImg):
    #print(pilImg.mode)
    data = pilImg.convert('RGB').tobytes()
    wxImg = wx.Image(*pilImg.size, data)
    wxBmap = wxImg.ConvertToBitmap()     # Equivalent result:   wxBmap = wx.BitmapFromImage( wxImg )
    return wxBmap



class DynamicBitmap(wx.Panel):
    def __init__(self, parent=None, id=-1, bitmap=None):
        wx.Panel.__init__(self, parent, id=-1)
        self.SetInitialSize((bitmap.Width, bitmap.Height))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.parent = parent
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.bitmap = bitmap
    
    def SetBitmap(self, b):
        self.bitmap = b
        #self.Refresh()

    def OnPaint(self, evt):
        dc = wx.BufferedPaintDC(self)
        dc.DrawBitmap(self.bitmap, 0,0)

infoLabel = wx.StaticText(panel, label="info")
vbox.Add(infoLabel)
bitmap = wx.Image(WIDTH, HEIGHT).ConvertToBitmap()
label = DynamicBitmap(panel, -1, bitmap)
vbox.Add(label)

#    updateOnChangeCheckbox = ttk.Checkbutton(menubar2, text="update graph on change", command = updateOnChange, variable = upc)
#    updateOnChangeCheckbox.pack(side="left")






def getMousePos():
    pt = wx.GetMousePosition()
    return ( 
        pt.x - label.GetScreenPosition().x, 
        pt.y - label.GetScreenPosition().y 
    )


def leftMouseUp(event):
    global draggingObject, draggingOutput, currentNode
    pos = getMousePos()
    if draggingOutput !=-1:
        for b in nodes:
            o =  b.insideInput(pos)
            if o!=-1:
                #print ("inputs " +str(o)+ " of "+str(b)+"to output "+str(draggingOutput)+" of "+str(draggingObject))
                b.inputs[o] = draggingObject.outputs[draggingOutput]
                currentNode = b
                if updateChange:
                    resetbuttonPressed(event=None)
                #b.setup()

    draggingObject = 0
    draggingOutput = -1
    pos = getMousePos()

def SetText(label, t):
    label.SetLabel(str(t))

def leftMouseDown(event):
    global draggingObject, draggingOutput, currentNode
    draggingObject = 0
    draggingOutput = -1
    pos = getMousePos()
    for b in nodes:
        if b.insideShowButton(pos):
            print(str(b.showvalue))
            b.height = max(len(b.inputs),len(b.outputs)) * b.spacing + b.titleHeight
            b.showvalue = not b.showvalue
        if b.inside(pos):
            #dc.rectangle((0,0,650,650),fill=(0,255,0))
            draggingObject = b
            currentNode = draggingObject
            #if draggingObject.type=="constant":
            SetText(infoLabel, draggingObject.value)
            #    inputVar.set(draggingObject.val)
        o = b.insideOutput(pos)
        if o!=-1:
            draggingOutput = o
        
    updateImage()

def doStuff():
    global lastPos, callbackvalues
    dc.rectangle((0,0,WIDTH,HEIGHT),fill=(0,0,0))
    (x0,y0) = lastPos
    (x,y) = getMousePos()

    if draggingObject !=0 and draggingOutput ==-1:
        #dc.rectangle((0,0,650,650),fill=(0,255,0))
        draggingObject.x += (x-x0)
        draggingObject.y += (y-y0)

    if draggingOutput!=-1:
        (x0,y0) = dragStartPos
        drawBezier(dc,
        (x0,y0,
        x0+50,y0,
        x-50,y,
        x,y)  
        )

    callbackvalues=[0]*len(callbacks)
    for n in range(0,len(callbacks)):
        callbackvalues[n] = callbacks[n]()

    for b in nodes:
        b.calc()
        b.draw(dc)

    lastPos = (x,y)


label.Bind(wx.EVT_LEFT_DOWN,leftMouseDown)
label.Bind(wx.EVT_LEFT_UP,leftMouseUp)


randomNumber = 0



def update():
    global randomNumber
    randomNumber =randomNumber+1# random.randint(0,99999999)
    doStuff()
    updateImage()
    label.Refresh()


def outputGraph():
    graph_def = tf.get_default_graph().as_graph_def()
    for node in graph_def.node:
        print(node.name+" : "+node.op)
        for input in node.input:
            print("\t"+input)

update()


        


window.Show()
app.MainLoop()
