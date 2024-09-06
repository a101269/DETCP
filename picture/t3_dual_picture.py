import matplotlib.pyplot as plt

# 数据
x = [1, 2, 3, 4, 5, 6]
y1 = [0.517947408, 0.396930929, 0.320982735, 0.282249506, 0.284945947, 0.284622025]
y2 = [0.471698113, 0.29245283, 0.141509434, 0.103773585, 0.132075472, 0.103773585]
y3 = [0.679, 0.597, 0.518, 0.416, 0.390, 0.384]
y4 = [0.717, 0.603, 0.462, 0.273, 0.226, 0.216]
p1 = [12.87817576, 15.76485153, 18.36462124, 20.21755815, 21.96628753, 23.14019983]
ppl2 = [10.66, 12.19, 13.46, 15.01, 16.70, 18.69]  # 注意这里使用了ppl2而不是p2

# 创建图形和轴
fig, ax1 = plt.subplots()

# 第一个Y轴
color = 'black'
ax1.set_xlabel('λ')
ax1.set_ylabel('Exp.Max.Tox.&Tox.Prob.', color=color)
ax1.plot(x, y1, color="tab:orange", label='Exp. Max. Tox.(concatenate original prompt)', marker='o')
ax1.plot(x, y2, color='tab:orange', label='Tox. Prob. (concatenate original prompt)', marker='s')
ax1.plot(x, y3, '--',color='tab:blue', label='Exp. Max. Tox. (DETCP)', marker='o')
ax1.plot(x, y4, '--', color='tab:blue', label='Tox. Prob. (DETCP)', marker='s')
ax1.tick_params(axis='y', labelcolor=color)
ax1.legend(loc='upper right')
# fig.legend(loc='upper left', bbox_to_anchor=(0.4, 0.85))
# 第二个Y轴
# ax2 = ax1.twinx()  # 创建共享X轴的新Y轴
# color = 'tab:green'
# ax2.set_ylabel('ppl', color=color)  # 我们也在这里添加y轴标签
# ax2.plot(x, p1, color=color, label='ppl (Model 1)', marker='D')
# ax2.plot(x, ppl2, '--', color=color, label='ppl (Model 2)', marker='D')
# ax2.tick_params(axis='y', labelcolor=color)
# ax2.legend(loc='upper right')

# 显示图形
# plt.title('Toxicity Measures and ppl Comparison')
plt.show()