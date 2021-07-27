import random

import numpy as np
import matplotlib.pyplot as plt


class StolbGraph:
    def __init__(self, maxX, x, y, colorLine, w, h, borders, fig=None, ax=None):
        self.fig = fig
        self.ax = ax
        self.y = []
        self.color = []
        new_border = None

        for step in range(len(x)):
            for i in range(1, len(borders)):
                if borders[i - 1] <= x[step] < borders[i]:
                    if new_border != borders[i - 1]:
                        next_color = i - 1
                        new_border = borders[i - 1]
                        self.y.append(y[step])
                        self.color.append(colorLine[next_color])
                        print(borders[i - 1], x[step], borders[i], colorLine[next_color])

        self.y.append(borders[-1])
        self.x = np.linspace(0, maxX, maxX)
        self.w = w
        self.h = h

    def draw(self):
        if self.fig is None or self.ax is None:
            self.fig, self.ax = plt.subplots(nrows=1, ncols=1, figsize=(3, 8))

        for i in range(0, len(self.y) - 1):
            print(self.y[i], self.y[i + 1])
            self.ax.fill_between(self.x, self.y[i], self.y[i + 1], color=self.color[i])
            # ax.text(2.5, self.y[i + 1] + abs(self.y[i + 1] - self.y[i]) / 2, self.text[i])

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

    borders = [0, 7, 19, 21]
    color = ['y', 'b', 'r', 'g']

    a = StolbGraph(2, x, range(len(x)), color, None, None, borders)
    a.draw()
