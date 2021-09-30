import math
from tkinter import *

import numpy as np
from matplotlib import pyplot as plt


class Cell:
    def __init__(self, window, null, i, j, name, lineColor, leftValue, measure, rightValue):
        self = Frame(window, background='gray', highlightbackground="black", highlightthickness=1)
        self.place(x = i*152, y = j*45, width=152, height=45)

        if not null:
            title = Label(self, bg='gray', text=name)
            title.place(height=20)
            title.grid(row=0, column=0, columnspan=3, sticky=E+W+S+N)

            line = Frame(self, width=150, height=1, bg=lineColor)
            line.grid(row=1, column=0, columnspa=3)

            leftV = Label(self, bg='gray', text=leftValue)
            leftV.place(height=20)
            leftV.grid(row=2, column=0, sticky=W)

            measure = Label(self, bg='gray', text=measure)
            measure.place(height=20)
            measure.grid(row=2, column=1, sticky=W+E)

            label_4 = Label(self, bg='gray', text=rightValue)
            label_4.place(height=20)
            label_4.grid(row=2, column=2, sticky=E)


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

        borders = list(borders)
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


class FillGraph:
    def __init__(self, x, y, colorLine, colorFill, lineWidth, alpha, w, h):
        self.x = x
        self.y = y
        self.colorLine = colorLine
        self.colorFill = colorFill
        self.lineWidth = lineWidth
        self.alpha = alpha
        self.w = w
        self.h = h

    def draw(self):
        fig, ax = plt.subplots()
        count = 0
        for x in self.x:
            ax.plot(x, self.y[count], color=self.colorLine[count], linewidth=self.lineWidth[count])
            ax.fill(x, self.y[count], color=self.colorFill[count], alpha=self.alpha[count])
            count += 1

        if self.w != None and self.h != None:
            fig.set_figwidth(self.w)
            fig.set_figheight(self.h)

        plt.show()

