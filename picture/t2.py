
import matplotlib.pyplot as plt
import matplotlib
# matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体为黑体
# matplotlib.rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号'-'显示为方块的问题

# 示例数据
x = [1,2,3,4,5,6 ]
y1 = [0.517947408, 0.396930929, 0.320982735, 0.282249506, 0.284945947, 0.284622025] # y轴1的数据
y2 = [0.471698113, 0.29245283, 0.141509434, 0.103773585, 0.132075472, 0.103773585] # y轴2的数据
ppl =[12.87817576, 15.76485153, 18.36462124, 20.21755815, 21.96628753, 23.14019983]
std_dev=[0.263,0.221,0.217,0.197,0.209,0.191]

y3=[0.679,0.597,0.518,0.416,0.390,0.384]
y4=[0.717,0.603,0.462,0.273,0.226,0.216]
ppl2=[10.66,12.19,13.46,15.01,16.70,18.69]

# 创建主图
fig, ax1 = plt.subplots()

# 绘制第一个y轴的数据
ax1.plot(x, y1, 'r-', label='Exp. Max. Tox.',color='green', marker='s') # linestyle='--',
# ax1.errorbar(x, y1, yerr=std_dev, fmt='none', ecolor=(0.87,0.70,1.0), elinewidth=2, capsize=4)
#
ax1.set_xlabel('λ')
ax1.set_ylabel('Exp.Max.Tox.&Tox.Prob.', color='black')
ax1.tick_params(axis='y', labelcolor='black')

# 创建第二个y轴，共享x轴
# ax2 = ax1.twiny()

# 绘制第二个y轴的数据
ax1.plot(x, y2, 'b-', label='Tox. Prob .',color='red', marker='o')
# ax2.set_ylabel('Tox. Prob .', color='b')
ax1.tick_params(axis='y', labelcolor='black')
# ax2.grid(True)


ax3 = ax1.twinx()

# 绘制第二个y轴的数据
ax3.plot(x, ppl, 'b-', label='PPL',color='orange', marker='x')
ax3.set_ylabel('PPL', color='black')
ax3.tick_params(axis='y', labelcolor='black')
ax3.grid(True)

# 显示图例
fig.legend(loc='upper left', bbox_to_anchor=(0.4, 0.98))

# 显示图表
plt.show()
plt.savefig('my_figure.svg')  # 保存图表为SVG文件

plt.savefig('my_figure.png', dpi=1000)

""""""
