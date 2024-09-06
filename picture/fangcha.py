import numpy as np
import matplotlib.pyplot as plt

# 示例数据
x = np.arange(1, 7)  # X轴数据
y = np.array([2, 3, 5, 7, 11,12])  # Y轴数据

# 假设的标准差（方差的平方根）
std_dev=[0.263,0.221,0.217,0.197,0.209,0.191]
# 绘制折线图
plt.plot(x, y, marker='o', linestyle='-')

# 添加误差条
plt.errorbar(x, y, yerr=std_dev, fmt='o', ecolor='r', elinewidth=2, capsize=4)

# 添加标题和坐标轴标签
plt.title('折线图与误差条')
plt.xlabel('X轴')
plt.ylabel('Y轴')

# 显示图表
plt.show()