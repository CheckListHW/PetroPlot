import matplotlib.pyplot as plt

for i in range(20):
    x = [3*i, 5]
    y = [5, 6]
    c = plt.plot(x, y)
    for cc in c:
        print(cc.get_color())

plt.show()
