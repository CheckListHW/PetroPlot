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
    def __init__(self, dots, **kwargs):
        self.parametrs = {
            'color': 'black',
            'unit': None,
            'type': 'line',
            'name': None,
        }

        self.dots = dots
        for key, value in kwargs.items():
            if key in self.parametrs:
                self.parametrs[key] = value


class Cell:
    def __init__(self, window, null, name, lineColor, leftValue, measure, rightValue):
        self = Frame(window, background='gray', highlightbackground="black", highlightthickness=1)
        if not null:
            self.grid_columnconfigure(0, weight=1)
            self.pack(fill="both", expand=True)

            title = Label(self, bg='gray', text=name)
            title.place(height=20)
            title.grid(row=0, column=0, columnspan=3, sticky=E + W + S + N)

            line = Frame(self, width=window.winfo_width(), height=1, bg=lineColor)
            line.grid(row=1, column=0, columnspa=3, sticky=W + E)

            leftV = Label(self, bg='gray', text=leftValue)
            leftV.place(height=20)
            leftV.grid(row=2, column=0, sticky=W)

            measure = Label(self, bg='gray', text=measure)
            measure.place(height=20)
            measure.grid(row=2, column=1, sticky=W + E)

            label_4 = Label(self, bg='gray', text=rightValue)
            label_4.place(height=20)
            label_4.grid(row=2, column=2, sticky=E)


class Pad:
    charts = []

    def __init__(self):
        self.charts = []

    def add_charts(self, chart):
        self.charts.append(chart)


class App:
    min_y = None
    max_y = None

    start = None
    end = None

    pads = []
    max_pad = 5

    first_show_pad = 0

    def __init__(self, filename):
        las = lasio.read(filename)
        self.curves = {}

        for item in las.items():
            self.curves[item[0]] = {
                'unit': las.sections.get('Curves').__getitem__(item[0]).__getitem__('unit'),
                'dots': item[1]
            }

        self.depth_dots = self.curves.get('DEPT').get('dots')

        self.start = self.min_y = min(self.curves.get('DEPT').get('dots'))
        self.end = self.max_y = max(self.curves.get('DEPT').get('dots'))

    def pads_show_number(self):
        for p in self.pads:
            for c in p.charts:
                print(c.parametrs.get('name'))

        self.set_first_show_pad(self.first_show_pad)
        if self.max_pad < len(self.pads):
            print(range(self.first_show_pad, self.first_show_pad + self.max_pad))
            return range(self.first_show_pad, self.first_show_pad + self.max_pad)
        else:
            print(range(self.first_show_pad, len(self.pads)))
            return range(self.first_show_pad, len(self.pads))

    def set_first_show_pad(self, new_first_show_pad):
        if len(self.pads) <= 5 or new_first_show_pad < 0:
            self.first_show_pad = 0
            return

        if new_first_show_pad + self.max_pad < len(self.pads):
            self.first_show_pad = new_first_show_pad
            return

        self.first_show_pad = len(self.pads) - 5

    def dots_range(self, dots):
        new_x = []
        new_y = []

        for i in range(len(self.depth_dots)):
            if self.start < self.depth_dots[i]:
                if self.depth_dots[i] < self.end:
                    new_x.append(self.depth_dots[i])
                    new_y.append(dots[i])
                else:
                    return new_y, new_x
        return new_y, new_x

    def zoom_scale(self, middle_y):
        scale = (self.end - self.start) / 4
        self.set_new_border(middle_y - scale, middle_y + scale)

    def reduce_scale(self):
        scale = (self.end - self.start)
        middle_y = self.start + scale / 2
        self.set_new_border(middle_y - scale, middle_y + scale)

    def set_new_border(self, new_start, new_end):
        if abs(new_end - new_start) < 10:
            return

        if new_end < self.max_y:
            self.end = new_end
        else:
            self.end = self.max_y

        if new_start > self.min_y:
            self.start = new_start
        else:
            self.start = self.min_y

    def add_pad(self, pad):
        self.pads.append(pad)

    def max_chart_in_pad(self):
        max_len = 0
        for pad in self.pads:
            max_len = max(len(pad.charts), max_len)
        return max_len


class Window():
    root = Tk()
    app = App('148R.las')

    def __init__(self):
        self.pad_choose = StringVar(self.root)
        self.pad_choose.set(list(self.app.curves.keys())[1])  # default value

        self.head_frame = tkinter.LabelFrame(self.root, text='head_frame')
        self.head_frame.pack(side=BOTTOM)

        self.main_scale_frame = tkinter.LabelFrame(self.root, text='main_scale_frame')
        self.main_scale_frame.pack(side=LEFT)

        self.pads_frame = tkinter.LabelFrame(self.root, text='pads_frame')
        self.pads_frame.pack(side=LEFT)

        self.draw_pad_choose_menu()
        self.draw_pads()
        self.root.mainloop()

    def draw_pad_choose_menu(self):
        Button(self.head_frame, text='>', command=self.pads_move_right).pack(side=RIGHT)
        Button(self.head_frame, text='+', command=self.add_pad).pack(side=RIGHT)
        Button(self.head_frame, text='<', command=self.pads_move_left).pack(side=LEFT)
        OptionMenu(self.head_frame, self.pad_choose, *list(self.app.curves.keys())).pack(side=LEFT)

    def pads_move_right(self):
        self.app.set_first_show_pad(self.app.first_show_pad + 1)
        self.draw_pads()

    def pads_move_left(self):
        self.app.set_first_show_pad(self.app.first_show_pad - 1)
        self.draw_pads()

    def draw_scale_pad(self):
        for widget in self.main_scale_frame.winfo_children():
            widget.destroy()

        scale_frame = tkinter.LabelFrame(self.main_scale_frame, text='scale_frame')
        scale_frame.pack()

        for i in range(self.app.max_chart_in_pad()):
            Cell(scale_frame, False, '', 'grey', '', "", '')

        scale_menu_frame = tkinter.LabelFrame(scale_frame, text='pad_menu_frame')
        button_useless = Button(scale_menu_frame, text='Сброс', command=self.reset_border)
        button_useless.pack(side=TOP, fill='both')
        scale_menu_frame.pack(side=BOTTOM, fill='both')

        scale_fig, scale_charts = plt.subplots(nrows=1, ncols=1, figsize=(1, 8))
        scale_fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
        scale_charts.spines['left'].set_position('center')
        scale_charts.xaxis.set_visible(False)
        scale_charts.set_ylim(self.app.end, self.app.start)

        canvas_scale = FigureCanvasTkAgg(scale_fig, scale_frame)
        canvas_scale.callbacks.connect('button_press_event', self.change_scale)

        canvas_scale.get_tk_widget().pack(side=LEFT)
        canvas_scale.draw()

    def reset_border(self):
        self.app.set_new_border(0, 99999)
        self.draw_pads()

    def change_scale(self, event):
        if event.button == 1:
            self.app.zoom_scale(event.ydata)
        if event.button == 3:
            self.app.reduce_scale()
        self.draw_pads()

    def add_pad(self):
        pad = Pad()
        self.add_chart(pad)
        self.app.add_pad(pad)
        self.draw_pads()

    def add_chart(self, pad):
        pad.add_chart(Chart(self.app.curves[self.pad_choose.get()].get('dots'),
                            name=self.pad_choose.get(),
                            unit=self.app.curves.get(self.pad_choose.get()).get('unit')))

    def draw_pads(self):

        plt.close('all')
        for widget in self.pads_frame.winfo_children():
            widget.destroy()

        for i in self.app.pads_show_number().__reversed__():
            fig, Chart = plt.subplots(nrows=1, ncols=1, figsize=(3, 8))
            fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)

            pad_frame = tkinter.LabelFrame(self.pads_frame, text='pad_frame')
            pad_frame.pack(side=RIGHT)

            pad_menu_frame = tkinter.LabelFrame(pad_frame, text='pad_menu_frame')
            pad_menu_frame.pack(side=BOTTOM, fill='both')

            pad_edit_button = Button(pad_menu_frame, text='Изменить',
                                     command=lambda j=self.app.pads[i]: self.show_pad_edit_window(j))
            pad_edit_button.pack(side=LEFT)

            button_delete_pad = Button(pad_menu_frame, text='X',
                                       command=lambda j=i: self.delete_pad(j))
            button_delete_pad.pack(side=RIGHT)

            for chart in self.app.pads[i].charts:
                x, y = self.app.dots_range(chart.dots)
                Chart.set_ylim(self.app.end, self.app.start)
                chart_line = Chart.plot(x, y)

                Cell(pad_frame, False, chart.parametrs.get('name'),
                     str(chart_line[0].get_color()),
                     str(round(min(x), 2)), chart.parametrs.get('unit'), str(round(max(x), 2)))

            for i in range(self.app.max_chart_in_pad() - len(self.app.pads[i].charts)):
                Cell(pad_frame, False, '', 'grey', '', "", '')

            canvas_main_charts = FigureCanvasTkAgg(fig, pad_frame)
            canvas_main_charts.get_tk_widget().pack(side=LEFT)
            canvas_main_charts.draw()
        self.draw_scale_pad()

    def delete_pad(self, pad_number):
        self.app.pads.pop(pad_number)
        self.draw_pads()

    def pre_destroy(self, widget):
        self.draw_pads()
        widget.destroy()

    def show_pad_edit_window(self, pad_number):
        pad_edit_window = Toplevel(self.root)
        pad_edit_window.protocol("WM_DELETE_WINDOW", lambda j=pad_edit_window: self.pre_destroy(j))
        pad_choose_menu = OptionMenu(pad_edit_window, self.pad_choose, *list(self.app.curves.keys()))
        pad_choose_menu.pack(side=LEFT)
        add_pad_btn = Button(pad_edit_window, text='+',
                             command=lambda j=pad_number: self.add_chart(j))
        add_pad_btn.pack()


if __name__ == '__main__':
    window = Window()
