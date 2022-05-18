from os import mkdir
from tkinter import Tk, filedialog, Frame, messagebox
from tkinter.ttk import *

import cv2
import matplotlib.pyplot as plt
import numpy as np

class GreenScreen(object):
    def __init__(self):
        self.root = Tk()
        self.root.wm_title('HVGB Green Screen Editor')
        self.lower_green = np.array([0, 100, 0])
        self.upper_green = np.array([120, 255, 100])

    def run(self):
        self.make_gui()
        self.root.mainloop()
    
    def select_input_file(self):
        file_types = (
            ('images', '*.jpg'),
            ('All files', '*.*')
        )
        self.filename = filedialog.askopenfilename(
            title='Open a file',
            initialdir='/',
            filetypes=file_types
        )
    def do_greenscreen(self):
        image = cv2.imread(self.filename)
        height, width, colors = image.shape
        image_copy = np.copy(image)
        image_copy = cv2.cvtColor(image_copy, cv2.COLOR_BGR2RGB)
        mask = cv2.inRange(image_copy, self.lower_green, self.upper_green)
        masked_image = np.copy(image_copy)
        masked_image[mask != 0] = [0,0,0]
        vigo_background = cv2.imread('vigo_background.jpg')
        vigo_background = cv2.cvtColor(vigo_background, cv2.COLOR_BGR2RGB)
        v_height, v_width, v_colors = vigo_background.shape
        if height > v_height and width > v_width:
            # crop the input picture
            cropped_image = cv2.resize(image_copy, (v_width, v_height))
            # get center of width
            #diff_width = width - v_width
            #half_diff_width = int(diff_width/2)
            #r_width = width - half_diff_width
            #bottom = height - v_height
            #cropped_image = cropped_image[half_diff_width:r_width, bottom:v_height]
            mask = cv2.inRange(cropped_image, self.lower_green, self.upper_green)
            masked_image = np.copy(cropped_image)
            masked_image[mask != 0] = [0,0,0]
            vigo_background[mask == 0] = [0,0,0]
            dirname = self.filename.split('.')[0]
            mkdir(dirname)
            cv2.imwrite('{0}/vigo.jpg'.format(dirname), vigo_background + masked_image)
            
    def make_gui(self):
        page = Frame(self.root)
        open_button = Button(self.root, text='Open file', command=self.select_input_file)
        open_button.pack(expand=True)
        edit_button = Button(self.root, text='Do greenscreen magic', command=self.do_greenscreen)
        edit_button.pack(expand=True)

GreenScreen().run()