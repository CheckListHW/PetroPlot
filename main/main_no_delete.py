import tkinter

import lasio
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.transforms as trns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import random

from tkinter import *


class Chart:
    dots = []
    parametrs = {
        'color': 'black',
        'unit': None,
        'max_value': None,
        'min_value': None,
        'type': 'line',
        'start': 0,
    }



    def __init__(self, dots, **kwargs):
        self.dots = dots
        for key, value in kwargs.items():
            if key in self.parametrs:
                self.parametrs[key] = value


class Cell:
    def __init__(self, window, null, i, j, name, lineColor, leftValue, measure, rightValue):
        self = Frame(window, background='gray', highlightbackground="black", highlightthickness=1)
        self.place(x=i * 152, y=j * 45, width=152, height=45)

        if not null:
            title = Label(self, bg='gray', text=name)
            title.place(height=20)
            title.grid(row=0, column=0, columnspan=3, sticky=E + W + S + N)

            line = Frame(self, width=150, height=1, bg=lineColor)
            line.grid(row=1, column=0, columnspa=3)

            leftV = Label(self, bg='gray', text=leftValue)
            leftV.place(height=20)
            leftV.grid(row=2, column=0, sticky=W)

            measure = Label(self, bg='gray', text=measure)
            measure.place(height=20)
            measure.grid(row=2, column=1, sticky=W + E)

            label_4 = Label(self, bg='gray', text=rightValue)
            label_4.place(height=20)
            label_4.grid(row=2, column=2, sticky=E)
            self.pack()

class Pad:
    def __init__(self):
        self.charts = []

    def add_charts(self, chart):
        self.charts.append(chart)


class App:
    start = None
    max_y = None
    depth_dots = None

    end = None
    min_y = None

    pads = []
    max_pad = 5
    log_names = []

    def __init__(self, filename):
        las = lasio.read(filename)

        self.values = {}
        self.len_values = len(las.items()[0][1])

        for item in las.items():
            self.values[item[0]] = item[1]
            self.log_names.append(item[0])

        self.depth_dots = self.values.get('DEPT')
        self.min_y = self.start = min(self.values.get('DEPT'))
        self.max_y = self.end = max(self.values.get('DEPT'))

    def dots_range(self, dots):
        new_x = []
        new_y = []

        for i in range(len(self.depth_dots)):
            if self.start < self.depth_dots[i]:
                if self.depth_dots[i] < self.end:
                    new_x.append(self.depth_dots[i])
                    new_y.append(dots[i])
                else:
                    print(new_x)
                    return new_y, new_x
        print(new_x)
        return new_y, new_x

    def zoom_scale(self, middle_y):
        scale = (self.end - self.start)/4
        self.set_new_border(middle_y - scale, middle_y + scale)

    def reduce_scale(self):
        scale = (self.end - self.start)
        middle_y = self.start + scale/2
        self.set_new_border(middle_y - scale, middle_y + scale)

    def set_new_border(self, min_y, max_y):
        if max_y - min_y < 1:
            return

        if max_y <= self.max_y:
            self.end = max_y
        else:
            self.end = self.max_y

        if min_y >= self.min_y:
            self.start = min_y
        else:
            self.start = self.min_y

    def add_pad(self, pad):
        self.pads.append(pad)


class Window():
    root = Tk()
    app = App('148R.las')

    def __init__(self):
        self.head_frame = tkinter.LabelFrame(self.root, text='head_frame')
        self.pads_frame = tkinter.LabelFrame(self.root, text='pads_frame')
        self.scale_frame = tkinter.LabelFrame(self.root, text='scale_frame')

        add_pad_btn = Button(self.head_frame, text='+', command=self.add_pad)

        self.pad_choose = StringVar(self.root)
        self.pad_choose.set('1')  # default value
        self.pad_choose_menu = OptionMenu(self.head_frame, self.pad_choose, *range(1, 2))
        self.pad_choose_menu.pack(side=LEFT)


        chart_delete_btn = Button(self.head_frame, text='Удалить', command=self.delete_pad)

        self.fig, self.Charts = plt.subplots(nrows=1, ncols=1, figsize=(16, 9))
        self.fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)

        self.scale_fig, self.scale_charts = plt.subplots(nrows=1, ncols=1, figsize=(1, 9))
        self.scale_fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
        self.scale_charts.spines['left'].set_position('center')
        self.scale_charts.xaxis.set_visible(False)

        self.head_frame.pack(side=BOTTOM)
        self.scale_frame.pack(side=LEFT)
        self.pads_frame.pack(side=LEFT)
        a = Cell(self.pads_frame, False, 0, 0, "Title", "yellow", "0.00", "", "200.0")
        add_pad_btn.pack(side=RIGHT)

        chart_delete_btn.pack(side=LEFT)

        self.canvas_scale = FigureCanvasTkAgg(self.scale_fig, self.scale_frame)
        self.canvas_scale.callbacks.connect('button_press_event', self.change_scale)
        self.canvas_main_charts = FigureCanvasTkAgg(self.fig, self.pads_frame)

        self.canvas_scale.get_tk_widget().pack(side=LEFT)
        self.canvas_main_charts.get_tk_widget().pack(side=LEFT)

        self.update_scale()
        self.canvas_main_charts.draw()
        self.root.mainloop()


    def update_scale(self):
        self.canvas_scale.get_tk_widget().destroy()

        self.scale_charts.set_ylim(self.app.end, self.app.start)
        self.canvas_scale = FigureCanvasTkAgg(self.scale_fig, self.scale_frame)
        self.canvas_scale.get_tk_widget().pack(side=LEFT)
        self.canvas_scale.draw()

    def change_scale(self, event):
        if event.button == 1:
            self.app.zoom_scale(event.ydata)
        if event.button == 3:
            self.app.reduce_scale()
        self.update_scale()
        self.update_pads()

    def edit_pad(self, name):
        self.Charts[int(self.pad_choose.get()) - 1].clear()
        self.Charts[int(self.pad_choose.get()) - 1].plot(self.values[name], range(self.len_values))
        #self.Charts[int(self.pad_choose.get()) - 1].axis('off')
        self.canvas_main_charts.draw()

    def add_pad(self):
        chart = Chart(self.app.values[self.app.log_names[len(self.app.pads)+1]])
        pad = Pad()
        pad.add_charts(chart)
        self.app.add_pad(pad)
        self.update_pads()

    def update_pads(self):
        self.canvas_main_charts.get_tk_widget().destroy()
        pad_len = len(self.app.pads)
        if pad_len == 0:
            return
        self.fig, self.Charts = plt.subplots(nrows=1, ncols=pad_len, figsize=(16, 9))
        self.fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)

        if len(self.app.pads) == 1:
            for chart in self.app.pads[0].charts:
                x, y = self.app.dots_range(chart.dots)
                self.Charts.set_ylim(self.app.end, self.app.start)
                self.Charts.plot(x, y)
                #self.Charts.axis('off')
        else:
            for i in range(len(self.app.pads)):
                 for chart in self.app.pads[i].charts:
                    x, y = self.app.dots_range(chart.dots)
                    self.Charts[i].set_ylim(self.app.end, self.app.start)
                    self.Charts[i].plot(x, y)
                    #self.Charts[i].axis('off')


        self.canvas_main_charts = FigureCanvasTkAgg(self.fig, self.pads_frame)
        self.canvas_main_charts.get_tk_widget().pack(side=LEFT)
        self.canvas_main_charts.draw()

        self.pad_choose_menu.destroy()
        self.pad_choose_menu = OptionMenu(self.head_frame, self.pad_choose, *range(1, len(self.app.pads)+1))
        self.pad_choose_menu.pack(side=LEFT)



    def delete_pad(self):
        self.app.pads.pop(int(self.pad_choose.get())-1)
        self.update_pads()



if __name__ == '__main__':
    window = Window()


