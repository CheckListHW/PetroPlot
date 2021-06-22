from tkinter import *

window = Tk()
window.geometry('300x200')
window.title("Header")

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

a = Cell(window, False, 0, 0, "Title", "yellow", "0.00", "", "200.0")

window.mainloop()