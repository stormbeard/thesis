import matplotlib.pyplot as plt

d8 = open("10.61.192.108-tier_usage.txt").readlines()
d8 = map(lambda x: float(x.split(",")[1]) / float(x.split(",")[0]), d8)

d9 = open("10.61.192.109-tier_usage.txt").readlines()
d9 = map(lambda x: float(x.split(",")[1]) / float(x.split(",")[0]), d9)

d10 = open("10.61.192.110-tier_usage.txt").readlines()
d10 = map(lambda x: float(x.split(",")[1]) / float(x.split(",")[0]), d10)

dev = []
for ii in range(min(len(d8), len(d9))):
    avg_val = (d8[ii] + d9[ii]) / 2.0
    pct_diff = avg_val - d10[ii]
    dev.append(pct_diff)

legend = ["8", "9", "10", "deviation"]
minlength = min([len(d8), len(d9), len(d10)])
minrange = range(minlength)

plt.plot(minrange, d8[:minlength])
plt.plot(minrange, d9[:minlength])
plt.plot(minrange, d10[:minlength])
plt.plot(minrange, dev[:minlength])
plt.legend(legend)
plt.show()
