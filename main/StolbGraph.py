import math
import random
import re

import lasio
import numpy as np
import matplotlib.pyplot as plt


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


if __name__ == '__main__':
    x = [random.randint(0, 21) for i in range(100)]

    x = [13, 15, 9, 11, 0, 15, 12, 12, 2, 18, 4, 0, 3, 8, 20, 13, 9,
         16, 12, 10, 19, 4, 12, 1, 3, 20, 0, 21, 19, 17, 4, 6, 19, 7,
         16, 21, 11, 9, 0, 21, 8, 4, 19, 5, 8, 19, 9, 4, 21, 19, 21,
         18, 20, 15, 5, 3, 13, 10, 9, 0, 16, 19, 9, 6, 2, 3, 5, 0, 8,
         21, 18, 21, 1, 18, 3, 4, 2, 14, 6, 20, 2, 20, 21, 11, 4, 18,
         1, 2, 7, 17, 5, 1, 18, 18, 13, 11, 7, 9, 5, 6]

    filename = 'C:/Users/kosac/PycharmProjects/petro_chart/main/148R.las'

    las = lasio.read(filename, encoding='utf-8')
    match = re.findall(r'\w*.las', filename)
    short_filename = match[0].replace('.las', '')

    curves = {}

    for item in las.items():
        curves[str(item[0]) + ' ' + short_filename] = {
            'unit': las.sections.get('Curves').__getitem__(item[0]).__getitem__('unit'),
            'dots': item[1],
        }


    y = curves['AZIMUT 148R']['dots']
    x = curves['DEPT 148R']['dots']

    borders = [4, 150, 350]
    color = ['y', 'b', 'r']

    a = StolbGraph(2, y, x, color, borders, text=color)
    a.draw()
