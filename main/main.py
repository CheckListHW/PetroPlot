import tkinter

import lasio
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.transforms as trns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from tkinter import *


class Chart:
    def __init__(self, dots, **kwargs):
        self.parametrs = {
            'color': 'black',
            'type': 'line',
            'name': None,
        }

        self.dots = dots
        for key, value in kwargs.items():
            if key in self.parametrs:
                self.parametrs[key] = value


class Cell:
    cell_frame = None

    def __init__(self, window, null, name, lineColor, leftValue, measure, rightValue):
        self.cell_frame = Frame(window, background='gray', highlightbackground="black", highlightthickness=1)
        self.cell_frame.pack(side=TOP, fill='both')
        if not null:
            self.cell_frame.grid_columnconfigure(0, weight=1)

            title = Label(self.cell_frame, bg='gray', text=name)
            title.place(height=20)
            title.grid(row=0, column=0, columnspan=3, sticky=E + W + S + N)

            line = Frame(self.cell_frame, width=self.cell_frame.winfo_width(), height=1, bg=lineColor)
            line.grid(row=1, column=0, columnspa=3, sticky=W + E)

            leftV = Label(self.cell_frame, bg='gray', text=leftValue)
            leftV.place(height=20)
            leftV.grid(row=2, column=0, sticky=W)

            measure = Label(self.cell_frame, bg='gray', text=measure)
            measure.place(height=20)
            measure.grid(row=2, column=1, sticky=W + E)

            label_4 = Label(self.cell_frame, bg='gray', text=rightValue)
            label_4.place(height=20)
            label_4.grid(row=2, column=2, sticky=E)

    def destroy(self):
        self.cell_frame.pack_forget()

    def pack(self):
        self.cell_frame.pack(fill="both", side=TOP)


class Pad:
    def __init__(self, frame):
        self.log = BooleanVar(frame)
        self.log.set(0)

        self.line_quantity = StringVar(frame)
        self.line_quantity.set(5)
        self.charts = []

    def add_charts(self, chart):
        self.charts.append(chart)


class PadFrame:
    def __init__(self, pads_frame):
        self.cell = []
        self.fig, self.chart = plt.subplots(nrows=1, ncols=1, figsize=(3, 8))
        self.fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)

        self.pad_frame = tkinter.Frame(pads_frame)  # , text='pad_frame')
        self.pad_frame.pack(side=LEFT)

        self.canvas_frame = tkinter.Frame(self.pad_frame)  # , text='canvas_frame')
        self.canvas_frame.pack(side=BOTTOM)

        self.cell_frame = tkinter.Frame(self.pad_frame)  # , text='cell_frame')
        self.cell_frame.pack(side=TOP, fill='both')

        self.pad_menu_frame = tkinter.Frame(self.pad_frame)  # , text='pad_menu_frame')
        self.pad_menu_frame.pack(side=BOTTOM, fill='both')

        self.canvas = FigureCanvasTkAgg(self.fig, self.canvas_frame)
        self.canvas.get_tk_widget().pack(side=BOTTOM)

    def update_chart(self):
        self.canvas_frame.pack_forget()
        self.canvas_frame.pack(side=BOTTOM)
        self.canvas.draw()

    def add_empty_cell(self, quntity_empty_cell):
        for x in range(quntity_empty_cell):
            new_cell_frame = Cell(self.cell_frame, False, '', 'grey', '', "", '')
            self.cell.append(new_cell_frame)

    def reset(self):
        self.chart.clear()
        for child in self.cell:
            child.destroy()


class App:
    pad_frames = []

    min_y = None
    max_y = None

    start = None
    end = None

    pads = []
    max_pad = 5

    first_show_pad = 0

    def __init__(self, filename, root):
        self.curves = {}
        las = lasio.read(filename)

        DATE = las.sections.get('Well').__getattr__('DATE').__getitem__('value')
        COUNTRY = las.sections.get('Well').__getattr__('COUNTRY').__getitem__('value')
        ORIGINALWELLNAME = las.sections.get('Well').__getattr__('ORIGINALWELLNAME').__getitem__('value')
        FLD = las.sections.get('Well').__getattr__('FLD').__getitem__('value')

        well_name = DATE + '  ' + COUNTRY + '   ' + FLD + '   ' + ORIGINALWELLNAME
        print(well_name)
        self.root = root

        self.pads_frame = tkinter.LabelFrame(self.root, text=well_name)
        self.pads_frame.pack(side=LEFT)

        for item in las.items():
            self.curves[item[0]] = {
                'unit': las.sections.get('Curves').__getitem__(item[0]).__getitem__('unit'),
                'dots': item[1]
            }

        self.depth_dots = self.curves.get('DEPT').get('dots')

        self.start = self.min_y = min(self.curves.get('DEPT').get('dots'))
        self.end = self.max_y = max(self.curves.get('DEPT').get('dots'))

    def get_or_create_pad_frame(self, pad_number):
        if pad_number >= len(self.pad_frames):
            self.pad_frames.append(PadFrame(self.pads_frame))
            return self.pad_frames[-1]
        return self.pad_frames[pad_number]

    def set_first_show_pad(self, new_first_show_pad):
        if len(self.pads) < new_first_show_pad:
            self.first_show_pad = len(self.pads) - 1
            return

        if new_first_show_pad < 0:
            self.first_show_pad = 0
            return

        self.first_show_pad = new_first_show_pad

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

    def add_pad(self, chart_name):
        pad = Pad(self.root)
        self.pads.append(pad)
        self.add_chart(len(self.pads) - 1, chart_name)

    def add_chart(self, pad_number, chart_name):
        self.pads[pad_number].add_charts(Chart(self.curves[chart_name].get('dots'),
                                               name=chart_name,
                                               unit=self.curves.get(chart_name).get('unit')))

    def max_pads_cells(self):
        max_len = 0
        for pad in self.pads:
            max_len = max(len(pad.charts), max_len)
        return max_len

    def delete_pad(self, pad_number):
        self.pads.pop(pad_number)

    def dots_range(self, dots):
        new_y = []
        new_x = []

        for i in range(len(self.depth_dots)):
            if self.start < self.depth_dots[i]:
                if self.depth_dots[i] < self.end:
                    new_y.append(self.depth_dots[i])
                    new_x.append(dots[i])
                else:
                    return new_x, new_y
        return new_x, new_y

    def n_round(self, z):
        n = -2
        while z // (10 ** (-n)) == 0:
            n += 1
            if n > 6:
                return 10
        return n + 2


class Window():
    root = Tk()
    root.geometry('1920x900+-10+0')

    def __init__(self):
        self.head_frame = Frame(self.root)
        self.head_frame.pack(side=BOTTOM)

        self.main_scale_frame = tkinter.LabelFrame(self.root, text='Масштаб')
        self.main_scale_frame.pack(side=LEFT)

        self.app = App('148R.las', self.root)

        self.pad_choose = StringVar(self.root)
        self.pad_choose.set(list(self.app.curves.keys())[1])  # default value

        self.draw_pad_choose_menu()
        self.draw_scale_pad()
        self.draw_pads()
        self.add_pad()
        self.root.mainloop()

    def draw_pad_choose_menu(self):
        move_frame = Frame(self.head_frame)
        move_frame.pack(padx=10, side=RIGHT)
        Button(move_frame, text='->', command=self.pads_move_right).pack(side=RIGHT)
        Button(move_frame, text='<-', command=self.pads_move_left).pack(side=RIGHT)

        add_pad_frame = Frame(self.head_frame)
        add_pad_frame.pack(padx=10, side=RIGHT)
        OptionMenu(add_pad_frame, self.pad_choose, *list(self.app.curves.keys())).pack(side=LEFT)
        Button(add_pad_frame, text='+', command=self.add_pad).pack(side=LEFT)

    def pads_move_right(self):
        self.app.set_first_show_pad(self.app.first_show_pad + 1)
        self.draw_pads()

    def pads_move_left(self):
        self.app.set_first_show_pad(self.app.first_show_pad - 1)
        self.draw_pads()

    def draw_scale_pad(self):
        self.scale_cell_frame = tkinter.Frame(self.main_scale_frame)  # , text='pad_menu_frame')
        self.scale_cell_frame.pack(side=TOP, fill='both')

        scale_menu_frame = tkinter.Frame(self.main_scale_frame)  # , text='pad_menu_frame')
        scale_menu_frame.pack(side=BOTTOM, fill='both')

        button_reset_border = Button(scale_menu_frame, text='Сброс', command=self.reset_border)
        button_reset_border.pack(side=TOP, fill='both')

        scale_fig, self.scale_charts = plt.subplots(nrows=1, ncols=1, figsize=(1, 8))
        scale_fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
        self.scale_charts.spines['left'].set_position('center')
        self.scale_charts.xaxis.set_visible(False)
        self.scale_charts.set_ylim(self.app.end, self.app.start)

        self.canvas_scale = FigureCanvasTkAgg(scale_fig, self.main_scale_frame)
        self.canvas_scale.callbacks.connect('button_press_event', self.change_scale)

        self.canvas_scale.get_tk_widget().pack(side=BOTTOM)
        self.canvas_scale.draw()

    def change_scale_pad(self):
        for child in self.scale_cell_frame.winfo_children():
            child.destroy()

        for i in range(self.app.max_pads_cells()):
            Cell(self.scale_cell_frame, False, '', 'grey', '', "", '')

        self.canvas_scale.get_tk_widget().pack_forget()
        self.canvas_scale.get_tk_widget().pack(side=BOTTOM)
        self.scale_charts.set_ylim(self.app.end, self.app.start)
        self.canvas_scale.draw()

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
        self.app.add_pad(self.pad_choose.get())
        self.draw_pads()

    def delete_pad(self, pad_number):
        self.app.delete_pad(pad_number)
        self.draw_pads()

    def draw_pads(self):
        for frame in self.app.pad_frames:
            frame.pad_frame.pack_forget()

        for i in range(self.app.first_show_pad, len(self.app.pads)):
            pad_frame = self.app.get_or_create_pad_frame(i)

            if len(pad_frame.pad_menu_frame.winfo_children()) == 0:
                self.create_pad_menu(pad_frame.pad_menu_frame, i)

            pad_frame.reset()

            pad_frame.chart.set_ylim(self.app.end, self.app.start)

            if self.app.pads[i].log.get():
                pad_frame.chart.set_xscale('log')

            for chart in self.app.pads[i].charts:
                x, y = self.app.dots_range(chart.dots)

                chart_line = pad_frame.chart.plot(x, y)

                X_Lim = [min(x), max(x)]

                medium = abs(X_Lim[0] - X_Lim[1])
                n_round = self.app.n_round(medium)
                new_cell_frame = Cell(pad_frame.cell_frame, False,
                                      chart.parametrs.get('name'),
                                      chart_line[0].get_color(),
                                      str(round(X_Lim[0], n_round)),
                                      chart.parametrs.get('unit'),
                                      str(round(X_Lim[1], n_round)))

                chart.parametrs['color'] = chart_line[0].get_color()
                pad_frame.cell.append(new_cell_frame)
                pad_frame.pad_frame.pack(side=LEFT)

            pad_frame.chart.set_xlim(pad_frame.chart.get_xlim()[0],
                                     pad_frame.chart.get_xlim()[1])

            line_quantity = int(self.app.pads[i].line_quantity.get())
            medium = abs(pad_frame.chart.get_xlim()[0]-pad_frame.chart.get_xlim()[1])
            step = medium / (line_quantity + 1)

            for x in range(line_quantity + 1):
                x1 = pad_frame.chart.get_xlim()[0] + step * x
                pad_frame.chart.plot(
                    [x1, x1],
                    [self.app.end, self.app.start],
                    color='black',
                    linewidth=0.5)

            pad_frame.add_empty_cell(self.app.max_pads_cells() - len(self.app.pads[i].charts))

            # перерисовка плота(графика) при добавлении новых линий
            self.app.pad_frames[i].update_chart()

        self.change_scale_pad()

    def create_pad_menu(self, frame, pad_number):
        pad_edit_button = Button(frame, text='Изменить',
                                 command=lambda j=pad_number: self.show_pad_edit_window(j))
        pad_edit_button.pack(side=LEFT)

        button_delete_pad = Button(frame, text='X',
                                   command=lambda j=pad_number: self.delete_pad(j))
        button_delete_pad.pack(side=RIGHT)

    def delete_pad(self, pad_number):
        self.app.delete_pad(pad_number)
        self.draw_pads()

    def pre_destroy(self, widget):
        widget.destroy()
        self.draw_pads()

    def add_chart_to_pad(self, pad_number):
        self.app.add_chart(pad_number, self.pad_choose.get())
        self.update_pad_edit_window(pad_number)

    def pop_chart_from_pad(self, pad_number, chart):
        self.app.pads[pad_number].charts.remove(chart)
        self.update_pad_edit_window(pad_number)

    def show_pad_edit_window(self, pad_number):
        if hasattr(self, 'pad_edit_window'):
            self.pad_edit_window.destroy()

        self.pad_edit_window = Toplevel(self.root)
        self.pad_edit_window.title('Настройки планшета: ' + str(pad_number+1))
        self.pad_edit_window.wm_geometry("400x400")
        self.pad_edit_window.protocol("WM_DELETE_WINDOW", lambda j=self.pad_edit_window: self.pre_destroy(j))

        self.update_pad_edit_window(pad_number)


    def update_pad_edit_window(self, pad_number):
        for widget in self.pad_edit_window.winfo_children():
            widget.destroy()

        chart_edit = Frame(self.pad_edit_window)
        chart_edit.pack(side=TOP)

        chart_add = Frame(chart_edit)
        chart_add.pack(side=TOP)

        OptionMenu(chart_add, self.pad_choose, *list(self.app.curves.keys())).pack(side=LEFT)
        Button(chart_add, text='+', command=lambda j=pad_number: self.add_chart_to_pad(j)).pack(side=RIGHT)

        for chart in self.app.pads[pad_number].charts:
            chart_delete = Frame(chart_edit)
            chart_delete.pack(side=TOP, fill='both')

            Label(chart_delete, text=chart.parametrs.get('name')).pack(side=LEFT)
            Button(chart_delete, text='X', command=lambda j=chart: self.pop_chart_from_pad(pad_number, j)).pack(side=RIGHT)
            Frame(chart_delete, width=30, height=2, bg=chart.parametrs.get('color')).pack(side=RIGHT)

        chart_styles = Frame(self.pad_edit_window)
        chart_styles.pack(side=TOP)

        chart_log = Frame(chart_styles)
        chart_log.pack(side=TOP)

        Label(chart_log, text='Логарифмическая шкала').pack(side=LEFT)
        Checkbutton(chart_log, variable=self.app.pads[pad_number].log).pack(side=LEFT)

        chart_grid = Frame(chart_styles)
        chart_grid.pack(side=TOP)

        Label(chart_grid, text='Количество линий').pack(side=LEFT)
        OptionMenu(chart_grid, self.app.pads[pad_number].line_quantity, *list(range(11))).pack(side=LEFT)

if __name__ == '__main__':
    window = Window()
