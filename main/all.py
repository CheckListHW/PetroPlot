import json
import math
import os
from tkinter import *
from tkinter import filedialog, ttk

import lasio
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import re

BASE_DIR = os.path.dirname(__file__)


class StolbGraph:
    def __init__(self, maxX, x, y, colorLine,  borders, fig=None, ax=None, w=None, h=None,):
        self.fig = fig
        self.ax = ax
        self.y = []
        self.color = []
        new_border = None
        empty = False

        self.y.append(y[0])
        self.color.append(colorLine[0])

        for step in range(len(x)):
            for i in range(1, len(borders)):
                if not -math.inf <= x[step] <= math.inf and empty is False:
                    self.y.append(y[step])
                    self.color.append('white')
                    empty = True
                if borders[i - 1] <= x[step] < borders[i]:
                    if new_border != borders[i - 1]:
                        empty = False
                        next_color = i - 1
                        new_border = borders[i - 1]
                        self.y.append(y[step])
                        self.color.append(colorLine[next_color])

        self.y.append(y[-1])
        self.x = np.linspace(0, maxX, maxX)
        self.w = w
        self.h = h

    def draw(self):
        if self.fig is None or self.ax is None:
            self.fig, self.ax = plt.subplots(nrows=1, ncols=1, figsize=(3, 8))

        for i in range(0, len(self.y) - 1):
            self.ax.fill_between(self.x, self.y[i], self.y[i + 1], color=self.color[i])

        if self.w is not None and self.h is not None:
            self.fig.set_figwidth(self.w)
            self.fig.set_figheight(self.h)

        #plt.show()


class Chart:
    def __init__(self, dots, **kwargs):
        self.type_line = None
        self.dots = dots

        self.parametrs = {
            'color': 'black',
            'type': 'line',
            'name': None,
            'borders': [np.nanmin(self.dots), np.nanmax(self.dots)],
            'borders_color': ['b'],
            'side_left': False,
        }

        for key, value in kwargs.items():
            if key in self.parametrs:
                self.parametrs[key] = value

    def get_type_line(self):
        if self.type_line is None:
            return self.parametrs.get('type')
        return self.type_line.get()


class Cell:
    cell_frame = None

    def __init__(self, window, null, name, lineColor, leftValue, measure, rightValue):
        self.cell_frame = Frame(window, background='gray', highlightbackground='black', highlightthickness=1)
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
        self.cell_frame.pack(fill='both', side=TOP)


class Pad:
    def __init__(self, frame):
        self.log = BooleanVar(frame)
        self.log.set(0)

        self.type = StringVar(frame)
        self.type.set('line')

        self.line_quantity = StringVar(frame)
        self.line_quantity.set(5)
        self.charts = []

    def add_chart(self, chart):
        self.charts.append(chart)


class PadFrame:
    def __init__(self, pads_frame):
        self.cell = []
        self.fig, self.chart = plt.subplots(nrows=1, ncols=1, figsize=(3, 8))
        self.fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)

        self.pad_frame = Frame(pads_frame)  # , text='pad_frame')
        self.pad_frame.pack(side=LEFT)

        self.canvas_frame = Frame(self.pad_frame)  # , text='canvas_frame')
        self.canvas_frame.pack(side=BOTTOM)

        self.cell_frame = Frame(self.pad_frame)  # , text='cell_frame')
        self.cell_frame.pack(side=TOP, fill='both')

        self.pad_menu_frame = Frame(self.pad_frame)  # , text='pad_menu_frame')
        self.pad_menu_frame.pack(side=BOTTOM, fill='both')

        self.canvas = FigureCanvasTkAgg(self.fig, self.canvas_frame)
        self.canvas.get_tk_widget().pack(side=BOTTOM)

    def update_chart(self):
        self.canvas_frame.pack_forget()
        self.canvas_frame.pack(side=BOTTOM)
        self.canvas.draw()

    def add_empty_cell(self, quntity_empty_cell):
        for x in range(quntity_empty_cell):
            new_cell_frame = Cell(self.cell_frame, False, '', 'grey', '', '', '')
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

    def __init__(self, root):
        self.filenames = []
        self.filenames_url = []
        self.curves = {}
        self.depth_dots = []

        self.root = root

        well_name = 'Планшеты'
        self.pads_frame = LabelFrame(self.root, text=well_name)
        self.pads_frame.pack(side=LEFT)

        # try:
        #    DATE = las.sections.get('Well').__getattr__('DATE').__getitem__('value')
        #    COUNTRY = las.sections.get('Well').__getattr__('COUNTRY').__getitem__('value')
        #    ORIGINALWELLNAME = las.sections.get('Well').__getattr__('ORIGINALWELLNAME').__getitem__('value')
        #    FLD = las.sections.get('Well').__getattr__('FLD').__getitem__('value')
        #    well_name = DATE + '  ' + COUNTRY + '   ' + FLD + '   ' + ORIGINALWELLNAME
        # except:
        #    well_name = 'Планшеты'

    def add_curves_from_file(self, filename):
        las = lasio.read(filename, encoding='utf-8')
        match = re.findall(r'\w*.las', filename)
        short_filename = match[0].replace('.las', '')

        if short_filename in self.filenames:
            self.open_error_window('Файл:' + match[0] + ' уже добавлен')
            return

        self.filenames.append(short_filename)
        self.filenames_url.append(filename)

        self.depth_dots.append(las.items()[0][1])

        self.start = self.min_y = min(las.items()[0][1])
        self.end = self.max_y = max(las.items()[0][1])

        for item in las.items():
            self.curves[str(item[0]) + ' ' + short_filename] = {
                'unit': las.sections.get('Curves').__getitem__(item[0]).__getitem__('unit'),
                'dots': item[1],
            }

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

    def open_error_window(self, message):
        error_window = Toplevel(self.root)
        label_error = Label(text=message, master=error_window, fg='red', font='Arial 32')
        label_error.pack()

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
            self.start = self.min_y

    def add_pad(self):
        pad = Pad(self.root)
        self.pads.append(pad)
        return pad

    def add_chart(self, pad_number, chart_name):
        self.pads[pad_number].add_chart(Chart(self.curves[chart_name].get('dots'),
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
        depth_dots_number = 0

        for i in range(len(self.depth_dots)):
            if len(self.depth_dots[i]) == len(dots):
                depth_dots_number = i

        for i in range(len(self.depth_dots[depth_dots_number])):
            if self.start < self.depth_dots[depth_dots_number][i]:
                if self.depth_dots[depth_dots_number][i] < self.end:
                    new_y.append(self.depth_dots[depth_dots_number][i])
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
    def __init__(self, root_widget):
        self.i = 0
        self.root = root_widget
        self.root = root_widget
        self.head_frame = Frame(self.root)
        self.head_frame.pack(side=BOTTOM)

        self.main_scale_frame = LabelFrame(self.root, text='Масштаб')
        self.main_scale_frame.pack(side=LEFT)

        self.app = App(self.root)

        self.pad_choose = StringVar(self.root)

        self.draw_pad_choose_menu()
        self.draw_scale_pad()
        self.draw_pads()

    def add_las_file(self):
        self.progress_bar_start()

        filenames = filedialog.askopenfilename(title='Открыть файл', initialdir=os.getcwd(),
                                               filetypes=[('las files', '.las')], multiple=True)

        for filename in filenames:
            self.app.add_curves_from_file(filename)
            self.draw_pad_choose_menu()

        self.progress_bar_stop()

    def load_template(self):
        self.progress_bar_start()
        filename = filedialog.askopenfilename(title='Открыть файл', initialdir=os.getcwd(),
                                              filetypes=[('JSON files', '.json')])


        with open(filename) as f:
            template = json.load(f)
            for file in template['files']:
                self.app.add_curves_from_file(file)

            for pad in template['pads']:
                new_pad = self.app.add_pad()
                new_pad.log.set(pad['log'])
                new_pad.type.set(pad['type'])
                new_pad.line_quantity.set(pad['line_quantity'])
                for chart in pad['charts']:
                    new_chart = Chart(self.app.curves[chart['name']].get('dots'),
                                      name=chart['name'],
                                      color=chart['color'],
                                      type=chart['type'],
                                      borders=chart['borders'],
                                      borders_color=chart['borders_color'],
                                      unit=self.app.curves.get(chart['name']).get('unit'))

                    new_pad.add_chart(new_chart)

        self.progress_bar_stop()

        self.draw_pad_choose_menu()
        self.draw_pads()

    def save_template(self):
        filename = filedialog.asksaveasfilename(initialdir='os.getcwd()', title='Select file',
                                                filetypes=(('json files', '*.json'), ("All files", "*.")))
        if filename is None or filename == '':  # asksaveasfile return `None` if dialog closed with 'cancel'.
            return

        main_json = {'files': self.app.filenames_url, 'pads': []}

        for pad in self.app.pads:
            pad_info = {'log': pad.log.get(), 'type': pad.type.get(),
                        'line_quantity': pad.line_quantity.get(), 'charts': []}

            for chart in pad.charts:
                parametrs = {'name': chart.parameters.get('name'), 'color': chart.parameters.get('color'),
                             'type': chart.get_type_line(), 'borders': chart.parameters.get('borders'),
                             'borders_color': chart.parameters.get('borders_color')}

                pad_info['charts'].append(parametrs)

            main_json['pads'].append(pad_info)

        if os.path.isfile(filename):
            os.remove(filename)

        jsonFile = open(filename, mode='x')
        json.dump(main_json, jsonFile)
        jsonFile.close()



    def progress_bar_start(self):
        self.progress_bar.pack()

    def progress_bar_stop(self):
        self.progress_bar.pack_forget()

    def draw_pad_choose_menu(self):
        for children in self.head_frame.winfo_children():
            children.destroy()

        progress_bar_frame = Frame(self.head_frame)
        progress_bar_frame.pack(padx=10, side=LEFT)

        self.progress_bar = ttk.Progressbar(progress_bar_frame, orient='horizontal', mode='determinate')
        self.progress_bar.start()

        move_frame = Frame(self.head_frame)
        move_frame.pack(padx=10, side=LEFT)
        Button(move_frame, text='Сохранить шаблон', command=self.save_template).pack(side=RIGHT)
        Button(move_frame, text='Загрузить шаблон', command=self.load_template).pack(side=RIGHT)
        Button(move_frame, text='Добавить las файл', command=self.add_las_file).pack(side=RIGHT)

        if self.app.curves != {}:
            move_frame = Frame(self.head_frame)
            move_frame.pack(padx=10, side=RIGHT)
            Button(move_frame, text='->', command=self.pads_move_right).pack(side=RIGHT)
            Button(move_frame, text='<-', command=self.pads_move_left).pack(side=RIGHT)

            add_pad_frame = Frame(self.head_frame)
            add_pad_frame.pack(padx=10, side=RIGHT)
            self.pad_choose.set(list(self.app.curves.keys())[1])  # default value
            OptionMenu(add_pad_frame, self.pad_choose, *list(self.app.curves.keys())).pack(side=LEFT)
            Button(add_pad_frame, text='+', command=self.add_pad).pack(side=LEFT)

    def pads_move_right(self):
        self.app.set_first_show_pad(self.app.first_show_pad + 1)
        self.draw_pads()

    def pads_move_left(self):
        self.app.set_first_show_pad(self.app.first_show_pad - 1)
        self.draw_pads()

    def draw_scale_pad(self):
        self.scale_cell_frame = Frame(self.main_scale_frame)  # , text='pad_menu_frame')
        self.scale_cell_frame.pack(side=TOP, fill='both')

        scale_menu_frame = Frame(self.main_scale_frame)  # , text='pad_menu_frame')
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
            Cell(self.scale_cell_frame, False, '', 'grey', '', '', '')

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
        self.app.add_pad()
        self.app.add_chart(len(self.app.pads) - 1, self.pad_choose.get())

        self.draw_pads()

    def delete_pad(self, pad_number):
        self.app.delete_pad(pad_number)
        self.draw_pads()

    def draw_pads(self):
        for frame in self.app.pad_frames:
            frame.pad_frame.pack_forget()

        for pad_number in range(self.app.first_show_pad, len(self.app.pads)):
            pad_frame = self.app.get_or_create_pad_frame(pad_number)

            if len(pad_frame.pad_menu_frame.winfo_children()) == 0:
                self.create_pad_menu(pad_frame.pad_menu_frame, pad_number)

            pad_frame.reset()

            if self.app.pads[pad_number].type.get() == 'line':
                self.draw_chart_in_pad(pad_number, pad_frame)

            if self.app.pads[pad_number].type.get() == 'row':
                self.draw_row_in_pad(pad_number, pad_frame)

            # перерисовка плота(графика) при добавлении новых линий
            self.app.pad_frames[pad_number].update_chart()

        self.change_scale_pad()

    def draw_chart_in_pad(self, pad_number, pad_frame):
        if self.app.pads[pad_number].log.get():
            pad_frame.chart.set_xscale('log')

        main_min = math.inf
        main_max = -math.inf

        for chart in self.app.pads[pad_number].charts:
            x, y = self.app.dots_range(chart.dots)
            main_min = min(np.nanmin(x), main_min)
            main_max = max(np.nanmax(x), main_max)
            X_Lim = [np.nanmin(x), np.nanmax(x)]

            chart_line = pad_frame.chart.plot(x, y)

            if chart.get_type_line() == 'fill':
                xx, yy = self.split_mass_nan(x, y)
                for i in range(len(xx)):
                    xx[i].append(main_max)
                    yy[i].append(yy[i][-1])
                    pad_frame.chart.fill_between(xx[i], yy[i], y2=min(yy[i]), color=chart_line[0].get_color(),
                                                 alpha=0.5)

            medium = abs(X_Lim[0] - X_Lim[1])
            n_round = self.app.n_round(medium)

            new_cell_frame = Cell(pad_frame.cell_frame, False,
                                  chart.parameters.get('name'),
                                  chart_line[0].get_color(),
                                  str(round(X_Lim[0], n_round)),
                                  chart.parameters.get('unit'),
                                  str(round(X_Lim[1], n_round)))

            chart.parameters['color'] = chart_line[0].get_color()

            pad_frame.cell.append(new_cell_frame)
            pad_frame.pad_frame.pack(side=LEFT)

        pad_frame.chart.set_ylim(self.app.end, self.app.start)

        pad_frame.chart.set_xlim(main_min * 1.01, main_max * 1.01)

        line_quantity = int(self.app.pads[pad_number].line_quantity.get())
        medium = abs(pad_frame.chart.get_xlim()[0] - pad_frame.chart.get_xlim()[1])
        step = medium / (line_quantity + 1)

        for x in range(line_quantity + 1):
            x1 = pad_frame.chart.get_xlim()[0] + step * x
            pad_frame.chart.plot(
                [x1, x1],
                [self.app.end, self.app.start],
                color='black',
                linewidth=0.5)

        pad_frame.add_empty_cell(self.app.max_pads_cells() - len(self.app.pads[pad_number].charts))

    def draw_row_in_pad(self, pad_number, pad_frame):
        if len(self.app.pads[pad_number].charts) == 0:
            return

        chart = self.app.pads[pad_number].charts[0]
        x, y = self.app.dots_range(chart.dots)

        fig_color, ax_color = plt.subplots()
        if len(chart.parameters['borders_color']) + 1 < len(chart.parameters['borders']):
            borders_color = []
            for i in chart.parameters['borders']:
                chart_line = ax_color.plot(1, 1)
                borders_color.append(chart_line[0].get_color())
            chart.parameters['borders_color'] = borders_color

        fig = pad_frame.fig
        ax = pad_frame.chart

        a = StolbGraph(2, x, y, chart.parameters['borders_color'],
                       chart.parameters['borders'], fig=fig, ax=ax)
        a.draw()

        X_Lim = [np.nanmin(x), np.nanmax(x)]

        medium = abs(X_Lim[0] - X_Lim[1])
        n_round = self.app.n_round(medium)
        new_cell_frame = Cell(pad_frame.cell_frame, False,
                              chart.parameters.get('name'),
                              'blue',
                              str(round(X_Lim[0], n_round)),
                              chart.parameters.get('unit'),
                              str(round(X_Lim[1], n_round)))

        chart.parameters['color'] = 'blue'
        pad_frame.cell.append(new_cell_frame)
        pad_frame.pad_frame.pack(side=LEFT)

        pad_frame.chart.set_ylim(self.app.end, self.app.start)

        pad_frame.chart.set_xlim(0, 1)

        pad_frame.add_empty_cell(self.app.max_pads_cells() - 1)

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

    def pop_border_from_pad(self, pad_number, value):
        self.app.pads[pad_number].charts[0].parameters['borders'].remove(value)
        self.update_pad_edit_window(pad_number)

    def add_pad_border(self, pad_number, value):
        try:
            border_value = float(value.get().replace(',', '.'))
        except ValueError:
            self.app.open_error_window(value.get() + ' - не является числом!')
            return

        if len(self.app.pads[pad_number].charts) == 0:
            self.app.open_error_window('Не указана линия!')
            return

        self.app.pads[pad_number].charts[0].parameters['borders'].append(border_value)
        self.app.pads[pad_number].charts[0].parameters['borders'] = \
            sorted(self.app.pads[pad_number].charts[0].parameters['borders'])

        self.update_pad_edit_window(pad_number)

    def show_pad_edit_window(self, pad_number):
        if hasattr(self, 'pad_edit_window'):
            self.pad_edit_window.destroy()

        self.pad_edit_window = Toplevel(self.root)
        self.pad_edit_window.title('Настройки планшета: ' + str(pad_number + 1))
        self.pad_edit_window.wm_geometry('400x400')
        self.pad_edit_window.protocol('WM_DELETE_WINDOW', lambda j=self.pad_edit_window: self.pre_destroy(j))

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

            Label(chart_delete, text=chart.parameters.get('name')).pack(side=LEFT)
            Button(chart_delete, text='X', command=lambda j=chart: self.pop_chart_from_pad(pad_number, j)).pack(
                side=RIGHT)

            if chart.type_line is None:
                chart.type_line = StringVar(self.root)
                chart.type_line.set(chart.parameters.get('type'))

            OptionMenu(chart_delete, chart.type_line, *list(['line', 'fill'])).pack(side=RIGHT)
            Frame(chart_delete, width=30, height=2, bg=chart.parameters.get('color')).pack(side=RIGHT)

        chart_styles = Frame(self.pad_edit_window)
        chart_styles.pack(side=TOP)

        pad_log = Frame(chart_styles)
        pad_log.pack(side=TOP)

        Label(pad_log, text='Логарифмическая шкала').pack(side=LEFT)
        Checkbutton(pad_log, variable=self.app.pads[pad_number].log).pack(side=LEFT)

        pad_grid = Frame(chart_styles)
        pad_grid.pack(side=TOP)

        Label(pad_grid, text='Количество линий').pack(side=LEFT)
        OptionMenu(pad_grid, self.app.pads[pad_number].line_quantity, *list(range(11))).pack(side=LEFT)

        pad_type = Frame(chart_styles)
        pad_type.pack(side=TOP)

        if self.app.pads[pad_number].type._tclCommands is None:
            self.app.pads[pad_number].type.trace('w', lambda *args: self.edit_window_on_change(pad_number, *args))

        Label(pad_type, text='Тип кривой').pack(side=LEFT)
        OptionMenu(pad_type, self.app.pads[pad_number].type, *list(['line', 'row'])).pack(side=LEFT)

        if len(self.app.pads[pad_number].charts) == 0:
            return

        if self.app.pads[pad_number].type.get() == 'row':
            pad_border = LabelFrame(chart_styles, text='Добавление границ')
            pad_border.pack(side=TOP)
            border_value = StringVar(value=0)

            add_pad_border = Frame(pad_border)
            add_pad_border.pack(side=TOP)

            Entry(add_pad_border, textvariable=border_value).pack(side=LEFT)
            Button(add_pad_border, text='+', command=lambda j=border_value: self.add_pad_border(pad_number, j)).pack(
                side=RIGHT)

            for border in self.app.pads[pad_number].charts[0].parameters['borders']:
                pad_border_delete = Frame(pad_border)
                pad_border_delete.pack(side=BOTTOM, fill='both')

                Label(pad_border_delete, text=border).pack(side=LEFT)
                Button(pad_border_delete, text='X',
                       command=lambda j=border: self.pop_border_from_pad(pad_number, j)).pack(side=RIGHT)
                # Frame(pad_border_delete, width=30, height=2, bg=chart.parametrs.get('color')).pack(side=RIGHT)

    def edit_window_on_change(self, p_n, *args):
        self.i += 1
        self.update_pad_edit_window(p_n)

    def split_mass_nan(self, x, y):
        z = True
        xx = []
        yy = []

        for s in range(min(len(x), len(y))):
            if np.isnan(x[s]):
                z = True
            else:
                if z is True:
                    z = False
                    xx.append([])
                    yy.append([])
                xx[-1].append(x[s])
                yy[-1].append(y[s])

        return xx, yy


import lasio
import pandas as pd
import numpy as np
from datetime import datetime


class Model():
    def __init__(self, las_path, Biot=0.85):
        self.las = lasio.read(las_path)
        self.Geomech_Model = pd.DataFrame({'Sv': self.las['SV'], 'SHmax': self.las['SH_MAX_V'],
                                           'Shmin': self.las['SH_MIN_V'], 'Ppore': self.las['PP'], 'Pw': self.las['PW'],
                                           'Well_azimuth': self.las['AZIMUT'],
                                           'Well_deviation': self.las['ZENIT'],
                                           'Poisson_ratio': self.las['POISON'],
                                           'TENSILE_STRENGTH': self.las['TENSILE_STRENGTH'],
                                           'UCS': self.las['CO_BEFORE_CALIBRATION'], 'TVD': self.las['TVD'],
                                           'BIOT': self.las['BIOT'],
                                           'mi': self.las['MI'], 'E': self.las['E'],
                                           'SHmax_azimuth': self.las['SH_MAX_AZIMUTH'],
                                           'BS': self.las['BS'], 'CALIPER': self.las['CALIPER'],
                                           'MUD_DENS': self.las['MUD_DENS']}, index=self.las['DEPT'])

        self.Geomech_Model = self.Geomech_Model.dropna()
        self.Geomech_Model['Biot'] = Biot
        self.progress_iterator = 0

    # классификация скважины по вывалам: 0 - номинальный диаметр/глинистая корка, 1 - вывал, 2 - каверна
    # отсечка каверна/вывал при превышении диаметра на 25% выше номинального (по статистике для рассматриваемых площадей)

    def Breakout_classification(self, Caliper, BS):
        index = self.Geomech_Model.index
        Breakout_classification = np.where(Caliper < BS * 1.03, 0, 1)
        Breakout_classification = np.where(Caliper > BS * 1.25, 2, Breakout_classification)
        Breakout_classification = pd.DataFrame({'Breakout_classification': Breakout_classification}, index=index)

        return Breakout_classification

    # классификация скважины по поглощениям: 0 - нет поглощения, 1 - есть поглощение
    # в текущей версии калибровка скважин без поглощений
    def Mud_loss_classify(self, Breakout_classification):
        index = self.Geomech_Model.index
        Mud_loss_classification = pd.DataFrame(
            {'Mud_loss_classification': Breakout_classification.Breakout_classification},
            index=index)
        Mud_loss_classification[:] = 0

        return Mud_loss_classification

    # рассчет компонентов тензора ПОЛНЫХ напряжений в плоскости скважины (трансформация тензора полных напряжений)
    # z-вдоль ствола скважины,
    # x-в направлении нижней стенки скважины,
    # y-90° против часовой стрелки от x, ось y находится в горизонтальной плоскости):

    # входные данные - напряжения и траектория скважины в порядке (Sv, SHmax, Shmin, Well_azimuth, Well_deviation)
    # результат - компоненты тензора напряжений в плоскости скважины

    def Transform_Stress(self, Sv, SHmax, Shmin, SHmax_azimuth, Well_azimuth_input, Well_deviation_input, Degrees=True):
        index = self.Geomech_Model.index
        Azimuth_from_SHmax = np.where(Well_azimuth_input > SHmax_azimuth,
                                      360 - (Well_azimuth_input - SHmax_azimuth), SHmax_azimuth - Well_azimuth_input)
        Well_azimuth = np.deg2rad(Well_azimuth_input)
        Well_deviation = np.deg2rad(Well_deviation_input)

        if not Degrees:
            Well_azimuth = Well_azimuth_input
            Well_deviation = Well_deviation_input
            Azimuth_from_SHmax = np.where(Well_azimuth_input > SHmax_azimuth,
                                          2 * np.pi - (Well_azimuth_input - SHmax_azimuth),
                                          SHmax_azimuth - Well_azimuth_input)

        lxx = np.cos(Well_azimuth) * np.cos(Well_deviation)
        lxy = np.sin(Well_azimuth) * np.cos(Well_deviation)
        lxz = -np.sin(Well_deviation)
        lyx = -np.sin(Well_azimuth)
        lyy = np.cos(Well_azimuth)
        lyz = 0
        lzx = np.cos(Well_azimuth) * np.sin(Well_deviation)
        lzy = np.sin(Well_azimuth) * np.sin(Well_deviation)
        lzz = np.cos(Well_deviation)
        Sxo = lxx ** 2 * SHmax + lxy ** 2 * Shmin + lxz ** 2 * Sv
        Syo = lyx ** 2 * SHmax + lyy ** 2 * Shmin + lyz ** 2 * Sv
        Szo = lzx ** 2 * SHmax + lzy ** 2 * Shmin + lzz ** 2 * Sv
        txyo = lxx * lyx * SHmax + lxy * lyy * Shmin + lxz * lyz * Sv
        tyzo = lyx * lzx * SHmax + lyy * lzy * Shmin + lyz * lzz * Sv
        tzxo = lzx * lxx * SHmax + lzy * lxy * Shmin + lzz * lxz * Sv

        Transformed_df = pd.DataFrame({'Sxo': Sxo, 'Syo': Syo,
                                       'Szo': Szo, 'txyo': txyo, 'tyzo': tyzo,
                                       'tzxo': tzxo}, index=index)
        return Transformed_df

    # рассчет ЭФФЕКТИВНЫХ напряжений на стенке скважины с посмощью уравнения Кирша для точки с углом 0° от оси x
    # против часовой стрелки
    # поскольку радиальное напряжение не меняется для разных углов - рассчитывается только одно значение
    # a,b,c,d,e - временные переменные для суммирования столбиков значений

    # входные данные - напряжения, трансформированные на стенку скважины, поровое давление, давление в скважине, коэфф Пуассона
    # (Sxo, Syo, Szo, txyo, tyzo, tzxo, Ppore, Pw, Poisson_ratio)

    # результат - (St_x_df, Sz_x_df, Ttz_x_df) напряжения тангенсальное, вертикальное и касательное на стенке скважины
    # (Smax_x_df, Smin_x_df) линеаризованные напряжения на стенке скважины
    # i_max_df  -  направление максимального тангенсального напряжения
    # (S_1_df, S_2_df, S_3_df) - главные напряжения для всех глубин и углов

    def Kirsch_Wall(self, Sxo, Syo, Szo, txyo, tyzo, tzxo, Ppore, Pw, Poisson_ratio):
        index = self.Geomech_Model.index
        i = 0
        Sr = Pw - Ppore
        a = Sxo + Syo - 2 * (Sxo - Syo) * np.cos(2 * np.radians(i)) - 4 * txyo * np.sin(2 * np.radians(i)) - Pw - Ppore
        b = Szo - Poisson_ratio * (
                    2 * (Sxo - Syo) * np.cos(2 * np.radians(i)) + 4 * txyo * np.sin(2 * np.radians(i))) - Ppore
        c = 2 * (-tzxo * np.sin(np.radians(i)) + tyzo * np.cos(np.radians(i)))
        d = 0.5 * (b + a + ((b - a) ** 2 + 4 * (c ** 2)) ** 0.5)
        e = 0.5 * (b + a - ((b - a) ** 2 + 4 * (c ** 2)) ** 0.5)
        f = Sr

        # рассчет напряжений на стенке скважины с посмощью уравнения Кирша для точек с углами 1-179° от оси x против часовой стрелки
        # угол 180° - представлен углом 0°
        for i in range(1, 180):
            St_x = Sxo + Syo - 2 * (Sxo - Syo) * np.cos(2 * np.radians(i)) - 4 * txyo * np.sin(
                2 * np.radians(i)) - Pw - Ppore
            Sz_x = Szo - Poisson_ratio * (
                        2 * (Sxo - Syo) * np.cos(2 * np.radians(i)) + 4 * txyo * np.sin(2 * np.radians(i))) - Ppore
            Ttz_x = 2 * (-tzxo * np.sin(np.radians(i)) + tyzo * np.cos(np.radians(i)))
            Smax_x = 0.5 * (Sz_x + St_x + (((Sz_x - St_x) ** 2) + 4 * (Ttz_x ** 2)) ** 0.5)
            Smin_x = 0.5 * (Sz_x + St_x - (((Sz_x - St_x) ** 2) + 4 * (Ttz_x ** 2)) ** 0.5)

            a = np.column_stack((a, St_x))
            b = np.column_stack((b, Sz_x))
            c = np.column_stack((c, Ttz_x))
            d = np.column_stack((d, Smax_x))
            e = np.column_stack((e, Smin_x))
            f = np.column_stack((f, Sr))

        # итоговыe напряжения на стенке скважины с индексами [глубина, угол от 0 до 179]:

        St_x_df = pd.DataFrame(a, index=index)
        Sz_x_df = pd.DataFrame(b, index=index)
        Ttz_x_df = pd.DataFrame(c, index=index)
        Smax_x_df = pd.DataFrame(d, index=index)
        Smin_x_df = pd.DataFrame(e, index=index)
        Sr = pd.DataFrame(f, index=index)

        return St_x_df, Sz_x_df, Ttz_x_df, Smax_x_df, Smin_x_df, Sr

        # определение (выбор или сортировка) ЭФФЕКТИВНЫХ главных нормальных напряжений на стенке скважины:

    def Principal_Stresses(self, Smax_x, Smin_x, Sr):
        index = self.Geomech_Model.index
        S_1 = np.where(Smax_x > Sr, Smax_x, Sr)
        S_1 = np.where(Smin_x > S_1, Smin_x, S_1)
        S_1 = pd.DataFrame(S_1, index=index)

        S_2 = np.where(Smin_x < Smax_x, np.where(Smin_x > Sr, Smin_x, Sr), False)
        S_2 = pd.DataFrame(S_2, index=index)

        S_3 = np.where(Smax_x < Sr, Smax_x, Sr)
        S_3 = np.where(Smin_x < S_3, Smin_x, S_3)
        S_3 = pd.DataFrame(S_3, index=index)

        # определение углов где действуют максимальные напряжения:
        i_max = pd.DataFrame({0: Smax_x.idxmax(axis=1)}, index=index)
        for i in range(1, 91):
            i_max[i] = np.where(i_max[0] + i > 179, i_max[0] + i - 180, i_max[0] + i)

        return S_1, S_2, S_3, i_max

        # сортировка напряжений относительно точки с максимальным тангенсальным напряжением:

    def sort_i_max(self, Smax_x, Smin_x, i_max, S_1, S_3):
        index = self.Geomech_Model.index
        Smax_x_i = pd.DataFrame({0: Smax_x.lookup(i_max.index, i_max[0])}, index=index)
        Smin_x_i = pd.DataFrame({0: Smin_x.lookup(i_max.index, i_max[0])}, index=index)
        S_1_i = pd.DataFrame({0: S_1.lookup(i_max.index, i_max[0])}, index=index)
        S_3_i = pd.DataFrame({0: S_3.lookup(i_max.index, i_max[0])}, index=index)
        for i in range(1, 91):
            Smax_x_i[i] = Smax_x.lookup(i_max.index, i_max[i])
            Smin_x_i[i] = Smin_x.lookup(i_max.index, i_max[i])
            S_1_i[i] = S_1.lookup(i_max.index, i_max[i])
            S_3_i[i] = S_3.lookup(i_max.index, i_max[i])

        return Smax_x_i, Smin_x_i, S_1_i, S_3_i

    # Определение угла вывала с помощью критерия Кулона
    # входные данные - максимальное и минимальное эффективные главные нормальные напряжения, прочность на одноосное сжатие
    # и тангенс угла внутреннего трения

    # результат - угол вывала на стенке скважины

    def Coulumb_breakout(self, S_1, S_3, UCS, mi, Smax_x_i, Ppore, TVD):
        index = self.Geomech_Model.index
        k_factor = pd.DataFrame(((mi ** 2 + 1) ** 0.5 + mi) ** 2, index=index)
        UCS = pd.DataFrame(UCS, index=index)
        Ppore = pd.DataFrame(Ppore, index=index)
        TVD = pd.DataFrame(TVD, index=index)
        for x in range(1, 180):
            k_factor[x] = k_factor[0]
            UCS[x] = UCS[0]
            Ppore[x] = Ppore[0]
            TVD[x] = TVD[0]
        Breakout = pd.DataFrame(np.where(S_1 > UCS + k_factor * S_3, 1, 0), index=index)
        Breakout_probability = pd.DataFrame(S_1 - UCS + k_factor * S_3, index=index)
        Breakout_angle = pd.DataFrame({'Breakout_angle': Breakout.sum(axis=1)}, index=index)
        Breakout_grad = ((Smax_x_i - UCS.loc[:, :90]) / (k_factor.loc[:, :90]) + Ppore.loc[:, :90]) / (
                    TVD.loc[:, :90] * 9.81) * 1000

        return Breakout_angle, Breakout_grad, Breakout_probability

    # определение градиентов ГНВП и поглощений
    # входные данные - (S_3, Shmin, Ppore, TVD, Tensile_strength)

    # результат - градиенты ГНВП и поглощений

    def Pore_Loss(self, S_3, Shmin, Ppore, TVD, Tensile_strength):
        index = self.Geomech_Model.index

        Pore_grad = Ppore / 9.81 / TVD * 1000
        Tensile_frac_grad = (S_3.min(axis=1) + Ppore + Tensile_strength) / 9.81 / TVD * 1000
        Mud_loss_grad = Shmin / 9.81 / TVD * 1000

        Pore_Loss_Grad = pd.DataFrame({'Pore_grad': Pore_grad, 'Tensile_frac_grad': Tensile_frac_grad,
                                       'Mud_loss_grad': Mud_loss_grad}, index=index)

        return Pore_Loss_Grad

    def Solve(self, Sv, SHmax, Shmin, SHmax_azimuth, Ppore, Pw, Poisson_ratio, UCS, mi,
              Tensile_Strength, Well_azimuth_input, Well_deviation_input, TVD):

        self.progress_iterator += 1
        #            print(self.progress_iterator)

        Transformed_Stress = self.Transform_Stress(Sv=Sv, SHmax=SHmax, Shmin=Shmin, SHmax_azimuth=SHmax_azimuth,
                                                   Well_azimuth_input=Well_azimuth_input,
                                                   Well_deviation_input=Well_deviation_input, Degrees=True)

        St_x, Sz_x, Ttz_x, Smax_x, Smin_x, Sr = self.Kirsch_Wall(
            Sxo=Transformed_Stress.Sxo.values, Syo=Transformed_Stress.Syo.values,
            Szo=Transformed_Stress.Szo.values, txyo=Transformed_Stress.txyo.values,
            tyzo=Transformed_Stress.tyzo.values, tzxo=Transformed_Stress.tzxo.values,
            Ppore=Ppore, Pw=Pw, Poisson_ratio=Poisson_ratio)

        S_1, S_2, S_3, i_max = self.Principal_Stresses(Smax_x, Smin_x, Sr)

        Smax_x_i, Smin_x_i, S_1_i, S_3_i = self.sort_i_max(Smax_x, Smin_x, i_max, S_1, S_3)

        Breakout_angle, Breakout_grad, Breakout_probability = self.Coulumb_breakout(S_1, S_3, UCS, mi,
                                                                                    Smax_x_i, Ppore, TVD)

        Pore_Loss_Grad = self.Pore_Loss(S_3, Shmin, Ppore, TVD, Tensile_Strength)

        return Breakout_angle, Breakout_grad, Pore_Loss_Grad, Smax_x_i, S_3_i

    def define_success(self, ratio, Geomech_Model, Breakout_classification,
                       Mud_loss_classification, Breakout_grad, Pore_Loss_Grad):

        index = self.Geomech_Model.index
        df = pd.DataFrame({'Mud_dens': self.Geomech_Model.MUD_DENS,
                           'Breakout_classification': Breakout_classification.Breakout_classification,
                           'Mud_loss_classification': Mud_loss_classification.Mud_loss_classification}, index=index)

        df['Breakout_grad_0_' + str(ratio)] = Breakout_grad[0]
        df['Breakout_grad_90_' + str(ratio)] = Breakout_grad[90]
        df['Mud_loss_grad' + str(ratio)] = Pore_Loss_Grad['Mud_loss_grad']

        df['Success_' + str(ratio)] = np.where(((df['Mud_dens'] > df['Breakout_grad_0_' + str(ratio)]) &
                                                (df['Breakout_classification'] == 0)), 1, 0)

        df['Success_' + str(ratio)] = np.where(((df['Mud_dens'] < df['Breakout_grad_0_' + str(ratio)]) &
                                                (df['Mud_dens'] > df['Breakout_grad_90_' + str(ratio)]) &
                                                (df['Breakout_classification'] == 1)), 1, df['Success_' + str(ratio)])

        df['Success_' + str(ratio)] = np.where(((df['Mud_dens'] < df['Breakout_grad_0_' + str(ratio)]) &
                                                (df['Mud_dens'] < df['Breakout_grad_90_' + str(ratio)]) &
                                                (df['Breakout_classification'] == 2)), 1, df['Success_' + str(ratio)])

        df['Success_' + str(ratio)] = np.where((df['Breakout_classification'] == 3), np.nan,
                                               df['Success_' + str(ratio)])

        df['Success_' + str(ratio)] = np.where(((df['Mud_dens'] > df['Mud_loss_grad' + str(ratio)]) &
                                                (df['Mud_loss_classification'] == 0)), 0, df['Success_' + str(ratio)])

        Success = df['Success_' + str(ratio)].sum() / df['Success_' + str(ratio)].count() * 100

        return Success

    def Define_Strains(self, Breakout_classification, Mud_loss_classification,
                       MD, Pc, start_ratio=1.00, stop_ratio=1.20, step=0.01):

        index = self.Geomech_Model.index
        df = pd.DataFrame({'v': self.Geomech_Model.Poisson_ratio, 'Sv': self.Geomech_Model.Sv,
                           'Pp': self.Geomech_Model.Ppore, 'Sv': self.Geomech_Model.Sv,
                           'v': self.Geomech_Model.Poisson_ratio, 'E': self.Geomech_Model.E * 1000,
                           'Mud_dens': self.Geomech_Model.MUD_DENS,
                           'Breakout_classification': Breakout_classification.Breakout_classification,
                           'Mud_loss_classification': Mud_loss_classification.Mud_loss_classification}, index=index)

        v = self.Geomech_Model.loc[self.Geomech_Model.index == MD, 'Poisson_ratio'].values[0]
        E = self.Geomech_Model.loc[self.Geomech_Model.index == MD, 'E'].values[0] * 1000
        Pp = self.Geomech_Model.loc[self.Geomech_Model.index == MD, 'Ppore'].values[0]
        Sv = self.Geomech_Model.loc[self.Geomech_Model.index == MD, 'Sv'].values[0]
        Biot = self.Geomech_Model.loc[self.Geomech_Model.index == MD, 'Biot'].values[0]

        Strain_max_list = np.array([])
        Strain_min_list = np.array([])
        Success_list = np.array([])

        ratio_list = [round(i, 2) for i in np.arange(start_ratio, stop_ratio + step, step)]
        for ratio in ratio_list:
            Spoison = v * Sv / (1 - v) - v * Biot * Pp / (1 - v) + Biot * Pp
            Strain_max = (Pc - Spoison * (1 - 1 / v) - (Pc * ratio) / v) / ((v - 1 / v) * E / (1 - v ** 2))
            Strain_min = (Pc * ratio - Spoison - E / (1 - v ** 2) * Strain_max) / (v * E / (1 - v ** 2))

            df['Shmin_ratio_' + str(ratio)] = (
                        df['v'] * df['Sv'] / (1 - df['v']) - df['v'] * Biot * df['Pp'] / (1 - df['v']) + Biot * df[
                    'Pp'] +
                        df['E'] * Strain_min / (1 - df['v'] ** 2) + df['v'] * df['E'] * Strain_max / (1 - df['v'] ** 2))
            df['SHmax_ratio_' + str(ratio)] = (
                        df['v'] * df['Sv'] / (1 - df['v']) - df['v'] * Biot * df['Pp'] / (1 - df['v']) + Biot * df[
                    'Pp'] +
                        df['E'] * Strain_max / (1 - df['v'] ** 2) + df['v'] * df['E'] * Strain_min / (1 - df['v'] ** 2))

            Breakout_angle, Breakout_grad, Pore_Loss_Grad, Smax_x_i, S_3_i = self.Solve(
                SHmax=df['SHmax_ratio_' + str(ratio)].values,
                Shmin=df['Shmin_ratio_' + str(ratio)].values,
                Sv=self.Geomech_Model.Sv.values,
                SHmax_azimuth=self.Geomech_Model.SHmax_azimuth.values,
                Ppore=self.Geomech_Model.Ppore.values,
                Pw=self.Geomech_Model.Pw.values,
                Poisson_ratio=self.Geomech_Model.Poisson_ratio.values,
                UCS=self.Geomech_Model.UCS.values,
                mi=self.Geomech_Model.mi.values,
                Tensile_Strength=self.Geomech_Model.TENSILE_STRENGTH.values,
                Well_azimuth_input=self.Geomech_Model.Well_azimuth.values,
                Well_deviation_input=self.Geomech_Model.Well_deviation.values,
                TVD=self.Geomech_Model.TVD.values)

            df['Breakout_grad_0_' + str(ratio)] = Breakout_grad[0]
            df['Breakout_grad_90_' + str(ratio)] = Breakout_grad[90]
            df['Mud_loss_grad' + str(ratio)] = Pore_Loss_Grad['Mud_loss_grad']

            df['Success_' + str(ratio)] = np.where(((df['Mud_dens'] > df['Breakout_grad_0_' + str(ratio)]) &
                                                    (df['Breakout_classification'] == 0)), 1, 0)

            df['Success_' + str(ratio)] = np.where(((df['Mud_dens'] < df['Breakout_grad_0_' + str(ratio)]) &
                                                    (df['Mud_dens'] > df['Breakout_grad_90_' + str(ratio)]) &
                                                    (df['Breakout_classification'] == 1)), 1,
                                                   df['Success_' + str(ratio)])

            df['Success_' + str(ratio)] = np.where(((df['Mud_dens'] < df['Breakout_grad_0_' + str(ratio)]) &
                                                    (df['Mud_dens'] < df['Breakout_grad_90_' + str(ratio)]) &
                                                    (df['Breakout_classification'] == 2)), 1,
                                                   df['Success_' + str(ratio)])

            df['Success_' + str(ratio)] = np.where((df['Breakout_classification'] == 3), np.nan,
                                                   df['Success_' + str(ratio)])

            df['Success_' + str(ratio)] = np.where(((df['Mud_dens'] > df['Mud_loss_grad' + str(ratio)]) &
                                                    (df['Mud_loss_classification'] == 0)), 0,
                                                   df['Success_' + str(ratio)])

            Success = df['Success_' + str(ratio)].sum() / df['Success_' + str(ratio)].count() * 100

            Strain_max_list = np.append(Strain_max_list, float(Strain_max))
            Strain_min_list = np.append(Strain_min_list, float(Strain_min))
            Success_list = np.append(Success_list, float(Success))

        ratio_list = np.array(ratio_list)

        ratio_frame = pd.DataFrame({'ratio': ratio_list, 'Success': Success_list,
                                    'Strain_max': Strain_max_list, 'Strain_min': Strain_min_list})

        best_ratio = ratio_frame.loc[ratio_frame['Success'].idxmax(), 'ratio']
        best_SHmax = df['SHmax_ratio_' + str(best_ratio)]
        best_Shmin = df['Shmin_ratio_' + str(best_ratio)]

        return ratio_frame, best_ratio, best_SHmax, best_Shmin

    def UCS_calibrate(self, Co, mi, Caliper, BS, Breakout_classification, Mud_dens,
                      Breakout_grad, Smax_x_i, S_3_i):

        index = self.Geomech_Model.index
        Co = pd.DataFrame({'Co': Co}, index=index)
        k_factor = pd.DataFrame({'k_factor': ((mi ** 2 + 1) ** 0.5 + mi) ** 2}, index=index)
        Caliper = pd.DataFrame({'Caliper': Caliper}, index=index)
        Mud_dens = pd.DataFrame({'Mud_dens': Mud_dens}, index=index)
        Breakout_grad_0 = pd.DataFrame({'Breakout_grad_0': Breakout_grad[0]}, index=index)
        Breakout_grad_45 = pd.DataFrame({'Breakout_grad_45': Breakout_grad[45]}, index=index)
        S_3_i_0 = pd.DataFrame({'S_3_i_0': S_3_i[0]}, index=index)
        S_3_i_45 = pd.DataFrame({'S_3_i_45': S_3_i[0]}, index=index)
        Smax_x_0 = pd.DataFrame({'Smax_x_0': Smax_x_i[0]}, index=index)
        Smax_x_45 = pd.DataFrame({'Smax_x_45': Smax_x_i[45]}, index=index)

        df = pd.concat([k_factor, Mud_dens, Co, BS, Breakout_classification,
                        Breakout_grad_0, Breakout_grad_45,
                        Smax_x_0, Smax_x_45, Caliper, S_3_i_0, S_3_i_45], axis=1)

        df['dC_0'] = df['Co'] + df['k_factor'] * df['S_3_i_0'] - df['Smax_x_0']
        df['dC_90'] = df['Co'] + df['k_factor'] * df['S_3_i_45'] - df['Smax_x_45']
        df['dC_1'] = df['dC_0'] + (df['dC_90'] - df['dC_0']) * (df['Caliper'] - df['BS']) / (df['BS'] * 1.25)
        df['dC_2'] = df['dC_90'] + (df['dC_0'] - df['dC_90']) / 2

        df['Co_calibrated'] = np.where((df['Mud_dens'] > df['Breakout_grad_0']) &
                                       (df['Breakout_classification'] == 0), df['Co'] - df['dC_0'] * 0.8, df['Co'])
        df['Co_calibrated'] = np.where((df['Mud_dens'] > df['Breakout_grad_0']) &
                                       (df['Breakout_classification'] == 1), df['Co'] - df['dC_1'], df['Co_calibrated'])
        df['Co_calibrated'] = np.where((df['Mud_dens'] < df['Breakout_grad_45']) &
                                       (df['Breakout_classification'] == 1), df['Co'] - df['dC_2'], df['Co_calibrated'])
        df['Co_calibrated'] = np.where((df['Mud_dens'] < df['Breakout_grad_0']) &
                                       (df['Breakout_classification'] == 0), df['Co'] - df['dC_0'] * 1.1,
                                       df['Co_calibrated'])
        df['Co_calibrated'] = np.where((df['Mud_dens'] > df['Breakout_grad_0']) &
                                       (df['Breakout_classification'] == 2), df['Co'] - df['dC_90'] * 1.1,
                                       df['Co_calibrated'])
        df['Co_calibrated'] = np.where((df['Mud_dens'] < df['Breakout_grad_45']) &
                                       (df['Breakout_classification'] == 0), df['Co'] - df['dC_0'] * 1.1,
                                       df['Co_calibrated'])
        df['Co_calibrated'] = np.where(
            (df['Mud_dens'] < df['Breakout_grad_0']) & (df['Mud_dens'] > df['Breakout_grad_45']) &
            (df['Breakout_classification'] == 2), df['Co'] + df['dC_2'] * 1.1, df['Co_calibrated'])

        df['Co_confirmed'] = np.where((df['Breakout_classification'] == 1) |
                                      (df['Breakout_classification'] == 2), df['Co_calibrated'], np.nan)
        df['Co_possible'] = np.where((df['Breakout_classification'] == 0), df['Co_calibrated'], np.nan)

        return df

    def Calibrate(self, MD=3388, Pc=60.37):

        Geomech_Model = self.Geomech_Model
        Caliper = self.Geomech_Model.CALIPER.values
        BS = self.Geomech_Model.BS.values

        Breakout_classification = self.Breakout_classification(Caliper=Caliper, BS=BS)
        Mud_loss_classification = self.Mud_loss_classify(Breakout_classification)

        ratio_frame, best_ratio, best_SHmax, best_Shmin = self.Define_Strains(
            Breakout_classification=Breakout_classification,
            Mud_loss_classification=Mud_loss_classification,
            MD=MD, Pc=Pc, start_ratio=1.00,
            stop_ratio=1.20, step=0.01)
        (Breakout_angle_strain_calibrated, Breakout_grad_strain_calibrated,
         Pore_Loss_Grad_strain_calibrated, Smax_x_i_strain_calibrated,
         S_3_i_strain_calibrated) = self.Solve(SHmax=best_SHmax.values,
                                               Shmin=best_Shmin.values,
                                               Sv=self.Geomech_Model.Sv.values,
                                               SHmax_azimuth=self.Geomech_Model.SHmax_azimuth.values,
                                               Ppore=self.Geomech_Model.Ppore.values,
                                               Pw=self.Geomech_Model.Pw.values,
                                               Poisson_ratio=self.Geomech_Model.Poisson_ratio.values,
                                               UCS=self.Geomech_Model.UCS.values,
                                               mi=self.Geomech_Model.mi.values,
                                               Tensile_Strength=self.Geomech_Model.TENSILE_STRENGTH.values,
                                               Well_azimuth_input=self.Geomech_Model.Well_azimuth.values,
                                               Well_deviation_input=self.Geomech_Model.Well_deviation.values,
                                               TVD=self.Geomech_Model.TVD.values)

        UCS_calibrated = self.UCS_calibrate(Co=self.Geomech_Model.UCS, mi=self.Geomech_Model.mi,
                                            Caliper=self.Geomech_Model.CALIPER, BS=self.Geomech_Model.BS,
                                            Breakout_classification=Breakout_classification,
                                            Mud_dens=self.Geomech_Model.MUD_DENS,
                                            Breakout_grad=Breakout_grad_strain_calibrated,
                                            Smax_x_i=Smax_x_i_strain_calibrated, S_3_i=S_3_i_strain_calibrated)

        (Breakout_angle_calibrated,
         Breakout_grad_calibrated,
         Pore_Loss_Grad_calibrated,
         Smax_x_i_calibrated,
         S_3_i_calibrated) = self.Solve(SHmax=best_SHmax.values,
                                        Shmin=best_Shmin.values,
                                        UCS=UCS_calibrated['Co_calibrated'].values,
                                        Sv=self.Geomech_Model.Sv.values,
                                        SHmax_azimuth=self.Geomech_Model.SHmax_azimuth.values,
                                        Ppore=self.Geomech_Model.Ppore.values,
                                        Pw=self.Geomech_Model.Pw.values,
                                        Poisson_ratio=self.Geomech_Model.Poisson_ratio.values,
                                        mi=self.Geomech_Model.mi.values,
                                        Tensile_Strength=self.Geomech_Model.TENSILE_STRENGTH.values,
                                        Well_azimuth_input=self.Geomech_Model.Well_azimuth.values,
                                        Well_deviation_input=self.Geomech_Model.Well_deviation.values,
                                        TVD=self.Geomech_Model.TVD.values)

        Success = self.define_success(ratio=best_ratio, Geomech_Model=self.Geomech_Model,
                                      Breakout_classification=Breakout_classification,
                                      Mud_loss_classification=Mud_loss_classification,
                                      Breakout_grad=Breakout_grad_calibrated,
                                      Pore_Loss_Grad=Pore_Loss_Grad_calibrated)

        self.Geomech_Model['SHmax_calibrated'] = best_SHmax.values
        self.Geomech_Model['Shmin_calibrated'] = best_Shmin.values
        self.Geomech_Model['UCS_calibrated'] = UCS_calibrated['Co_calibrated'].values
        self.Success = Success
        self.Ratio = best_ratio

        return Success

    def Write_Results(self, results_path):
        las = lasio.LASFile()
        las.well.DATE = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        las.other = 'Output file from Geomechanics Calibration v1 by Dmitry Konoshonkin'
        las.add_curve('DEPT', self.Geomech_Model.index, unit='m')
        las.add_curve('SHmax_calibrated', self.Geomech_Model['SHmax_calibrated'], unit='MPa')
        las.add_curve('Shmin_calibrated', self.Geomech_Model['Shmin_calibrated'], unit='MPa')
        las.add_curve('UCS_calibrated', self.Geomech_Model['UCS_calibrated'], unit='MPa')
        las.write(results_path, version=2)


from tkinter import Tk
import tkinter as tk
import queue
import threading
from tkinter import *
from tkinter.ttk import *
from tkinter.scrolledtext import *
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from tkinter.messagebox import showerror

window = tk.Tk()
window.title("Автокалибровка v1.0")

models = []
q = queue.Queue()


def Open_Model(self):
    filename = askopenfilename()
    try:
        Geomech_Model = Model(las_path=filename)
        Model_path.insert(0, filename)
        models.clear()
        models.append(Geomech_Model)
        tf = open(filename)
        data = tf.read()
        Preview.delete('0.0', END)
        Preview.insert(END, data)
        tf.close()
    except:
        showerror(title="Ошибка входных данных", message="Проверьте входные данные и повторите попытку")


def Calibrate_Model():
    try:
        Pc_value = float(Pc_Entry.get())
        Pc_depth_value = float(Pc_depth_Entry.get())
        progress.start()
        models[0].Calibrate(MD=Pc_depth_value, Pc=Pc_value)
        Success_results.insert(0, np.round(models[0].Success, 1))
        Ratio_results.insert(0, models[0].Ratio)
    except:
        showerror(title="Ошибка расчета", message="Проверьте входные данные и повторите попытку")


def Save_Model(self):
    try:
        results_path = asksaveasfilename(defaultextension=".las")
        models[0].Write_Results(results_path=results_path)
        Save_path.insert(0, results_path)
        tf = open(results_path)
        data = tf.read()
        Preview.delete('0.0', END)
        Preview.insert(END, data)
        tf.close()
    except:
        showerror(title="Ошибка сохранения", message="Не могу сохранить результаты")


def tb_click(self):
    ThreadedTask(q).start()
    window.after(100, process_queue)


def process_queue():
    try:
        msg = q.get(0)
        # Show result of the task if needed
        progress.stop()
        progress['mode'] = 'determinate'
        progress['value'] = 100
        if Success_results.get() == '':
            progress['value'] = 0
            progress['mode'] = 'determinate'
    except queue.Empty:
        window.after(100, process_queue)


class ThreadedTask(threading.Thread):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q

    def run(self):
        Calibrate_Model()  # Simulate long running process
        self.q.put("Task finished")


# Parent widget for the buttons
Mainframe = Frame(window)
Mainframe.grid(row=0, column=0, padx=(5), pady=(5), sticky=N + W)

buttons_frame = LabelFrame(Mainframe, text="Входные данные")
buttons_frame.grid(row=0, column=0, padx=(5), sticky=N + W)

buttons_frame2 = LabelFrame(Mainframe, text="Калибровка")
buttons_frame2.grid(row=0, column=1, padx=(5), sticky=N + W)

Open_btn = Button(buttons_frame, text="Открыть модель")
Open_btn.grid(column=0, row=0, sticky=W + E, ipady=1, pady=1)

Model_path = Entry(buttons_frame, width=50)
Model_path.grid(column=1, row=0, sticky=W + E, ipady=1, pady=1)

Pc_label = Label(buttons_frame, anchor="e", justify=RIGHT, width=27,
                 text="Pc [МПа]:").grid(column=0, row=1, ipady=1, pady=1)

Pc_Entry = Entry(buttons_frame, width=15)
Pc_Entry.grid(column=1, row=1, sticky=W, ipady=1, pady=1)

Pc_depth_label = Label(buttons_frame, anchor="e", justify=LEFT, width=27,
                       text="Глубина ГРП [MD, м]:").grid(column=0, row=2, ipady=1, pady=1)

Pc_depth_Entry = Entry(buttons_frame, width=15)
Pc_depth_Entry.grid(column=1, row=2, sticky=W, ipady=1, pady=1)

Calibrate_btn = Button(buttons_frame2, text="Провести калибровку")
Calibrate_btn.grid(column=0, row=0, ipady=1, pady=1)

progress = Progressbar(buttons_frame2, orient=HORIZONTAL, length=320, mode='indeterminate')
progress.grid(column=1, row=0, columnspan=2, ipady=1, pady=1)

Success_label = Label(buttons_frame2, anchor="e", justify=LEFT, width=27,
                      text="Сходимость, %:").grid(column=0, row=2, ipady=1, pady=1)

Success_results = Entry(buttons_frame2, width=15)
Success_results.grid(column=1, row=2, sticky=W, ipady=1, pady=1)

Ratio_label = Label(buttons_frame2, anchor="e", justify=LEFT, width=27,
                    text="Соотношение напряжений:").grid(column=0, row=3, ipady=1, pady=1)

Ratio_results = Entry(buttons_frame2, width=15)
Ratio_results.grid(column=1, row=3, sticky=W, ipady=1, pady=1)

Save_btn = Button(buttons_frame2, text="Сохранить результат")
Save_btn.grid(column=0, row=4, ipady=1, pady=1)

Save_path = Entry(buttons_frame2, width=50)
Save_path.grid(column=1, row=4, sticky=W + E, ipady=1, pady=1)



from petro_chart import Window

# Group1 Frame ----------------------------------------------------


notebook = Notebook(window)
notebook.grid(row=1, column=0, padx=(5), pady=0, columnspan=2, sticky=E + S + N + W)


group1 = Frame(notebook)

group2 = Frame(notebook)

petro_chart = Window(group2)

notebook.add(group1, text='Предварительный просмотр las файлов')
notebook.add(group2, text='Просмотр планшетов с кривыми')

window.columnconfigure(0, weight=1)
window.rowconfigure(1, weight=1)

group1.rowconfigure(0, weight=1)
group1.columnconfigure(0, weight=1)

Preview = ScrolledText(group1, wrap=WORD)
Preview.grid(column=0, row=0, sticky=E + S + N + W)

Open_btn.bind('<Button-1>', Open_Model)
Calibrate_btn.bind('<Button-1>', tb_click)
Save_btn.bind('<Button-1>', Save_Model)

window.mainloop()
