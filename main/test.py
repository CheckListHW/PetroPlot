import tkinter


import lasio
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.transforms as trns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import random

from tkinter import *





class Window():
    root = Tk()

    def __init__(self):
        self.pad_choose = StringVar(self.root)
        self.pad_choose.set(list(['aaa', 'nnnn']))  # default value

        self.head_frame = tkinter.LabelFrame(self.root, text='head_frame')
        self.head_frame.pack(side=BOTTOM)

        self.main_scale_frame = tkinter.LabelFrame(self.root, text='main_scale_frame')
        self.main_scale_frame.pack(side=LEFT)

        self.pads_frame = tkinter.LabelFrame(self.root, text='pads_frame')
        self.pads_frame.pack(side=LEFT)

        add_butt = Button(self.head_frame, text='add', command=self.add)
        del_butt = Button(self.head_frame, text='del', command=self.del_butt)

        add_butt.pack()
        del_butt.pack()

        self.root.mainloop()


    def add(self,):
        self.pads_frame.destroy()


        self.pads_frame = tkinter.LabelFrame(self.root, text='pads_frame')
        self.pads_frame.pack(side=LEFT)
        Button(self.pads_frame, text='add', command=self.add).pack()
        print('add')

    def del_butt(self):
        print('del')


if __name__ == '__main__':
    window = Window()
