import numpy as np
import matplotlib.pyplot as plt

class FillGraph:
    def __init__(self, x, y, colorLine, colorFill, lineWidth, alpha,  w, h):
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
            print(x)
            print(self.y[count])
            ax.plot(x, self.y[count], color=self.colorLine[count], linewidth=self.lineWidth[count])
            ax.fill(x, self.y[count], color=self.colorFill[count], alpha=self.alpha[count])
            count += 1
            
        if self.w != None and self.h != None:
            fig.set_figwidth(self.w)
            fig.set_figheight(self.h)
            
        plt.show()

if __name__ == '__main__':
    x = [[1, 3, 4, 5, 7], [7, 5, 4, 3, 1]]
    y = [[2, 4, 3, 4, 2], [4, 2, 3, 2, 4]]
    colorLine = ['b', 'g']
    colorFill = ['y', 'r']
    lineWidth = [2, 2]
    alpha = [0.5, 0.5]

    a = FillGraph(x, y, colorLine, colorFill, lineWidth, alpha, None, None)
    a.draw();
