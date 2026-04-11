"""
基于CHARLS的夫妻共病轨迹耦合及交互健康效应研究
Phase 4: 结果可视化优化 + 敏感性分析
"""

import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.genmod.families import Gaussian
from statsmodels.genmod.cov_struct import Exchangeable, Independence, Autoregressive
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import seaborn as sns
import os, warnings
warnings.filterwarnings('ignore')

BASE_DIR = r"C:\Users\mc_leafwave\OneDrive\文档\统计建模\项目代码"
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
FIG_DIR = os.path.join(BASE_DIR, "output", "figures")
TAB_DIR = os.path.join(BASE_DIR, "output", "tables")

df_wide = pd.read_csv(os.path.join(PROC_DIR, "couples_wide.csv"))
df_long = pd.read_csv(os.path.join(PROC_DIR, "couples_long.csv"))
df_traj = pd.read_csv(os.path.join(PROC_DIR, "couples_trajectories.csv"))

WAVES = [1, 2, 3, 4]
WAVE_YEARS = {1: 2011, 2: 2013, 3: 2015, 4: 2018}

# ============================================================
# 1. CLPM 路径图 (专业风格)
# ============================================================
print("绘制 CLPM 路径图...")

# 读取CLPM结果
clpm_df = pd.read_csv(os.path.join(TAB_DIR, "table6_clpm_results.csv"))

fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 10)
ax.set_ylim(0, 8)
ax.axis('off')

# 节点位置
positions = {
    'h_phys_t': (1.5, 6.5), 'h_phys_t1': (5, 6.5), 'h_phys_t2': (8.5, 6.5),
    'w_phys_t': (1.5, 1.5), 'w_phys_t1': (5, 1.5), 'w_phys_t2': (8.5, 1.5),
}

# 标签
labels = {
    'h_phys_t': '丈夫共病\n(t期)', 'h_phys_t1': '丈夫共病\n(t+1期)', 'h_phys_t2': '丈夫共病\n(t+2期)',
    'w_phys_t': '妻子共病\n(t期)', 'w_phys_t1': '妻子共病\n(t+1期)', 'w_phys_t2': '妻子共病\n(t+2期)',
}

# 绘制节点
for key, (x, y) in positions.items():
    color = '#2196F3' if 'h_' in key else '#E91E63'
    rect = plt.Rectangle((x-0.7, y-0.4), 1.4, 0.8, facecolor=color, alpha=0.15,
                          edgecolor=color, linewidth=2, zorder=2)
    ax.add_patch(rect)
    ax.text(x, y, labels[key], ha='center', va='center', fontsize=11, fontweight='bold', zorder=3)

# 箭头函数
def draw_arrow(ax, start, end, label, color='black', style='->', lw=2, curve=0):
    x1, y1 = positions[start]
    x2, y2 = positions[end]
    # 调整起止点到矩形边缘
    if x1 < x2: x1 += 0.7; x2 -= 0.7
    elif x1 > x2: x1 -= 0.7; x2 += 0.7
    if y1 < y2: y1 += 0.4; y2 -= 0.4
    elif y1 > y2: y1 -= 0.4; y2 += 0.4

    if curve != 0:
        arrow = FancyArrowPatch((x1, y1), (x2, y2),
                                arrowstyle='->', mutation_scale=15,
                                connectionstyle=f'arc3,rad={curve}',
                                color=color, linewidth=lw, zorder=1)
    else:
        arrow = FancyArrowPatch((x1, y1), (x2, y2),
                                arrowstyle='->', mutation_scale=15,
                                color=color, linewidth=lw, zorder=1)
    ax.add_patch(arrow)

    # 标签位置
    mx, my = (x1+x2)/2, (y1+y2)/2
    if curve != 0:
        my += curve * 1.5
    ax.text(mx, my, label, ha='center', va='center', fontsize=10,
            color=color, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none', alpha=0.8))

# 自回归路径 (水平)
draw_arrow(ax, 'h_phys_t', 'h_phys_t1', 'β=0.947***', '#2196F3', lw=3)
draw_arrow(ax, 'h_phys_t1', 'h_phys_t2', 'β=0.947***', '#2196F3', lw=3)
draw_arrow(ax, 'w_phys_t', 'w_phys_t1', 'β=0.959***', '#E91E63', lw=3)
draw_arrow(ax, 'w_phys_t1', 'w_phys_t2', 'β=0.959***', '#E91E63', lw=3)

# 交叉滞后路径 (对角线)
draw_arrow(ax, 'w_phys_t', 'h_phys_t1', 'β=0.022***', '#FF9800', lw=2, curve=-0.15)
draw_arrow(ax, 'h_phys_t', 'w_phys_t1', 'β=0.026***', '#FF9800', lw=2, curve=0.15)
draw_arrow(ax, 'w_phys_t1', 'h_phys_t2', 'β=0.022***', '#FF9800', lw=2, curve=-0.15)
draw_arrow(ax, 'h_phys_t1', 'w_phys_t2', 'β=0.026***', '#FF9800', lw=2, curve=0.15)

ax.set_title('交叉滞后面板模型 (CLPM): 夫妻身体共病的双向溢出效应\n*** P<0.001',
             fontsize=15, fontweight='bold', pad=20)

# 图例
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], color='#2196F3', lw=3, label='丈夫自回归'),
    Line2D([0], [0], color='#E91E63', lw=3, label='妻子自回归'),
    Line2D([0], [0], color='#FF9800', lw=2, label='交叉滞后 (配偶溢出)'),
]
ax.legend(handles=legend_elements, loc='upper right', fontsize=11)

plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "fig11_clpm_path.png"), dpi=300, bbox_inches='tight')
plt.close()
print("已保存: fig11_clpm_path.png")

# ============================================================
# 2. CLPM 三变量对比图 (身体/CESD/多维)
# ============================================================
print("绘制 CLPM 系数对比图...")

clpm_cross = clpm_df[clpm_df['效应类型'] == '交叉效应(Partner)'].copy()

# 若筛选为空，尝试匹配新格式的效应类型名
if len(clpm_cross) == 0:
    clpm_cross = clpm_df[clpm_df['效应类型'].str.contains('交叉|Partner|Cross', case=False, na=False)].copy()

if len(clpm_cross) > 0:
    fig, ax = plt.subplots(figsize=(10, 6))

    # 按β值排序展示
    clpm_cross['β_float'] = clpm_cross['β'].apply(lambda x: float(x))
    clpm_cross = clpm_cross.sort_values('β_float')

    y_pos = range(len(clpm_cross))
    beta_vals = clpm_cross['β_float']
    max_abs_beta = float(np.max(np.abs(beta_vals))) if len(beta_vals) > 0 else 0.0

    # 根据因变量名着色：身体=蓝，CESD/抑郁=橙，多维=紫
    def get_color(name):
        name = str(name)
        if '身体' in name or 'phys' in name.lower():
            return '#2196F3'
        elif 'CESD' in name or '抑郁' in name or 'cesd' in name.lower():
            return '#FF9800'
        else:
            return '#9C27B0'

    colors = [get_color(v) for v in clpm_cross['因变量']]

    bars = ax.barh(list(y_pos), beta_vals, color=colors, alpha=0.85, height=0.55)
    ax.axvline(x=0, color='black', linestyle='--', linewidth=0.8)

    # 根据系数范围自动扩展x轴，避免右侧标签被截断
    x_pad = max(max_abs_beta * 0.18, 0.01)
    x_left = min(float(np.min(beta_vals)) - x_pad, -0.003)
    x_right = max(float(np.max(beta_vals)) + x_pad, 0.003)
    ax.set_xlim(x_left, x_right)

    # 添加数值标签（仅显示系数，显著性统一在图注说明）
    for i, (v, sig) in enumerate(zip(beta_vals, clpm_cross['显著性'])):
        offset = max(abs(v) * 0.08, 0.002)
        if v >= 0:
            x_text = v + offset
            ha = 'left'
        else:
            x_text = v - offset
            ha = 'right'
        ax.text(x_text, i, f'{v:.4f}', va='center', ha=ha, fontsize=10, fontweight='bold')

    # Y轴标签：简化因变量名
    ylabels = []
    for name in clpm_cross['因变量']:
        name = str(name)
        name = name.replace('(t+1)', '').replace('（t+1）', '').strip()
        ylabels.append(name)

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(ylabels, fontsize=11)
    ax.set_xlabel('交叉滞后系数 β（伙伴效应）', fontsize=12)
    ax.set_title('CLPM：配偶共病溢出效应系数对比', fontsize=14, fontweight='bold')
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.3f}'))
    ax.grid(True, alpha=0.3, axis='x')
    ax.text(0.0, -0.12, '注: * p<0.05, ** p<0.01, *** p<0.001',
            transform=ax.transAxes, fontsize=9, color='dimgray',
            ha='left', va='top', clip_on=False)

    # 图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2196F3', alpha=0.85, label='身体共病'),
        Patch(facecolor='#FF9800', alpha=0.85, label='抑郁得分'),
        Patch(facecolor='#9C27B0', alpha=0.85, label='多维共病'),
    ]
    ax.legend(handles=legend_elements, fontsize=10, loc='lower right')

    plt.tight_layout(rect=(0, 0.06, 1, 1))
    plt.savefig(os.path.join(FIG_DIR, "fig12_clpm_comparison.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("已保存: fig12_clpm_comparison.png")
else:
    print("警告: 未找到交叉效应数据，跳过图12")

# ============================================================
# 3. 夫妻轨迹组合与健康结局热力图
# ============================================================
print("绘制轨迹组合-健康结局热力图...")

traj_labels = df_traj[['householdID', 'h_phys_traj', 'w_phys_traj']].copy()
df_merged = df_long.merge(traj_labels, on='householdID', how='inner')

# 最后一波的CESD均值, 按丈夫×妻子轨迹组分组
w4 = df_merged[df_merged['wave'] == 4].copy()

for outcome, label, cmap in [
    ('h_cesd10', '丈夫CESD-10 (2018)', 'YlOrRd'),
    ('w_cesd10', '妻子CESD-10 (2018)', 'YlOrRd'),
]:
    pivot = w4.groupby(['h_phys_traj', 'w_phys_traj'])[outcome].mean().unstack()
    pivot.index = [f'丈夫-组{int(i)}' for i in pivot.index]
    pivot.columns = [f'妻子-组{int(i)}' for i in pivot.columns]

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(pivot, annot=True, fmt='.1f', cmap=cmap, ax=ax,
                linewidths=0.5, cbar_kws={'label': label})
    ax.set_title(f'夫妻轨迹组合与{label}', fontsize=14)
    plt.tight_layout()
    suffix = 'h' if 'h_cesd' in outcome else 'w'
    plt.savefig(os.path.join(FIG_DIR, f"fig13_traj_outcome_{suffix}.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"已保存: fig13_traj_outcome_{suffix}.png")

# ============================================================
# 4. 敏感性分析
# ============================================================
print("\n" + "="*60)
print("敏感性分析")
print("="*60)

sensitivity_results = []

# --- 4a. 排除2018年数据 (仅用前3轮) ---
print("\n--- SA1: 排除2018年，仅用2011-2015 ---")
full3 = df_long[df_long['wave'].isin([1, 2, 3])].groupby('householdID').filter(lambda x: len(x) == 3)

clpm3_rows = []
for hhid in full3['householdID'].unique():
    c = full3[full3['householdID'] == hhid].sort_values('wave').set_index('wave')
    for t, t1 in [(1,2), (2,3)]:
        if t in c.index and t1 in c.index:
            clpm3_rows.append({
                'householdID': hhid,
                'h_phys_t': c.loc[t, 'h_phys_count'], 'w_phys_t': c.loc[t, 'w_phys_count'],
                'h_phys_t1': c.loc[t1, 'h_phys_count'], 'w_phys_t1': c.loc[t1, 'w_phys_count'],
                'h_cesd_t': c.loc[t, 'h_cesd10'], 'w_cesd_t': c.loc[t, 'w_cesd10'],
                'h_cesd_t1': c.loc[t1, 'h_cesd10'], 'w_cesd_t1': c.loc[t1, 'w_cesd10'],
            })
df_sa1 = pd.DataFrame(clpm3_rows)

for outcome, preds, label in [
    ('h_phys_t1', ['h_phys_t', 'w_phys_t'], '丈夫身体(SA1)'),
    ('w_phys_t1', ['w_phys_t', 'h_phys_t'], '妻子身体(SA1)'),
    ('h_cesd_t1', ['h_cesd_t', 'w_cesd_t'], '丈夫CESD(SA1)'),
    ('w_cesd_t1', ['w_cesd_t', 'h_cesd_t'], '妻子CESD(SA1)'),
]:
    data = df_sa1[['householdID', outcome] + preds].dropna()
    if len(data) < 100: continue
    y = data[outcome]
    X = sm.add_constant(data[preds])
    try:
        gee = GEE(y, X, groups=data['householdID'], family=Gaussian(), cov_struct=Exchangeable())
        res = gee.fit()
        cross_pred = preds[1]
        b, p = res.params[cross_pred], res.pvalues[cross_pred]
        se = res.bse[cross_pred]
        sig = '***' if p<0.001 else ('**' if p<0.01 else ('*' if p<0.05 else ''))
        print(f"  {label} Partner: β={b:.4f} (SE={se:.4f}) P={p:.4f}{sig}")
        sensitivity_results.append({'分析': 'SA1-排除2018', '模型': label, 'β': b, 'SE': se, 'P': p, '显著': sig})
    except: pass

# --- 4b. 不同共病定义 (阈值 >=3 种身体疾病) ---
print("\n--- SA2: 身体共病阈值改为 >=3 种 ---")
df_long_sa2 = df_long.copy()
for prefix in ['h', 'w']:
    df_long_sa2[f'{prefix}_phys_high'] = (df_long_sa2[f'{prefix}_phys_count'] >= 3).astype(float)

clpm_sa2_rows = []
full4 = df_long_sa2.groupby('householdID').filter(lambda x: len(x) == 4)
for hhid in full4['householdID'].unique():
    c = full4[full4['householdID'] == hhid].sort_values('wave').set_index('wave')
    for t, t1 in [(1,2), (2,3), (3,4)]:
        if t in c.index and t1 in c.index:
            clpm_sa2_rows.append({
                'householdID': hhid,
                'h_phys_t': c.loc[t, 'h_phys_high'], 'w_phys_t': c.loc[t, 'w_phys_high'],
                'h_phys_t1': c.loc[t1, 'h_phys_high'], 'w_phys_t1': c.loc[t1, 'w_phys_high'],
            })
df_sa2 = pd.DataFrame(clpm_sa2_rows)

for outcome, preds, label in [
    ('h_phys_t1', ['h_phys_t', 'w_phys_t'], '丈夫(SA2-阈值3)'),
    ('w_phys_t1', ['w_phys_t', 'h_phys_t'], '妻子(SA2-阈值3)'),
]:
    data = df_sa2[['householdID', outcome] + preds].dropna()
    if len(data) < 100: continue
    y = data[outcome]
    X = sm.add_constant(data[preds])
    try:
        gee = GEE(y, X, groups=data['householdID'], family=Gaussian(), cov_struct=Exchangeable())
        res = gee.fit()
        cross_pred = preds[1]
        b, p = res.params[cross_pred], res.pvalues[cross_pred]
        se = res.bse[cross_pred]
        sig = '***' if p<0.001 else ('**' if p<0.01 else ('*' if p<0.05 else ''))
        print(f"  {label} Partner: β={b:.4f} (SE={se:.4f}) P={p:.4f}{sig}")
        sensitivity_results.append({'分析': 'SA2-阈值3', '模型': label, 'β': b, 'SE': se, 'P': p, '显著': sig})
    except: pass

# --- 4c. 使用 Independent 相关结构替代 Exchangeable ---
print("\n--- SA3: GEE使用Independent相关结构 ---")
full_panel = df_long.groupby('householdID').filter(lambda x: len(x) == 4)
clpm_rows_full = []
for hhid in full_panel['householdID'].unique():
    c = full_panel[full_panel['householdID'] == hhid].sort_values('wave').set_index('wave')
    for t, t1 in [(1,2), (2,3), (3,4)]:
        if t in c.index and t1 in c.index:
            clpm_rows_full.append({
                'householdID': hhid,
                'h_phys_t': c.loc[t, 'h_phys_count'], 'w_phys_t': c.loc[t, 'w_phys_count'],
                'h_phys_t1': c.loc[t1, 'h_phys_count'], 'w_phys_t1': c.loc[t1, 'w_phys_count'],
                'h_cesd_t': c.loc[t, 'h_cesd10'], 'w_cesd_t': c.loc[t, 'w_cesd10'],
                'h_cesd_t1': c.loc[t1, 'h_cesd10'], 'w_cesd_t1': c.loc[t1, 'w_cesd10'],
            })
df_sa3 = pd.DataFrame(clpm_rows_full)

for outcome, preds, label in [
    ('h_phys_t1', ['h_phys_t', 'w_phys_t'], '丈夫身体(SA3)'),
    ('w_phys_t1', ['w_phys_t', 'h_phys_t'], '妻子身体(SA3)'),
    ('h_cesd_t1', ['h_cesd_t', 'w_cesd_t'], '丈夫CESD(SA3)'),
    ('w_cesd_t1', ['w_cesd_t', 'h_cesd_t'], '妻子CESD(SA3)'),
]:
    data = df_sa3[['householdID', outcome] + preds].dropna()
    if len(data) < 100: continue
    y = data[outcome]
    X = sm.add_constant(data[preds])
    try:
        gee = GEE(y, X, groups=data['householdID'], family=Gaussian(), cov_struct=Independence())
        res = gee.fit()
        cross_pred = preds[1]
        b, p = res.params[cross_pred], res.pvalues[cross_pred]
        se = res.bse[cross_pred]
        sig = '***' if p<0.001 else ('**' if p<0.01 else ('*' if p<0.05 else ''))
        print(f"  {label} Partner: β={b:.4f} (SE={se:.4f}) P={p:.4f}{sig}")
        sensitivity_results.append({'分析': 'SA3-Independent', '模型': label, 'β': b, 'SE': se, 'P': p, '显著': sig})
    except: pass

# --- 4d. 仅限完整4轮参与的夫妻 (已是主分析，此处作为对照，纳入至少2轮的) ---
print("\n--- SA4: 放宽为至少参与2轮的夫妻 ---")
panel2 = df_long.groupby('householdID').filter(lambda x: len(x) >= 2)
clpm_sa4 = []
for hhid in panel2['householdID'].unique():
    c = panel2[panel2['householdID'] == hhid].sort_values('wave').set_index('wave')
    waves_present = sorted(c.index.tolist())
    for i in range(len(waves_present)-1):
        t, t1 = waves_present[i], waves_present[i+1]
        clpm_sa4.append({
            'householdID': hhid,
            'h_phys_t': c.loc[t, 'h_phys_count'], 'w_phys_t': c.loc[t, 'w_phys_count'],
            'h_phys_t1': c.loc[t1, 'h_phys_count'], 'w_phys_t1': c.loc[t1, 'w_phys_count'],
            'h_cesd_t': c.loc[t, 'h_cesd10'], 'w_cesd_t': c.loc[t, 'w_cesd10'],
            'h_cesd_t1': c.loc[t1, 'h_cesd10'], 'w_cesd_t1': c.loc[t1, 'w_cesd10'],
        })
df_sa4 = pd.DataFrame(clpm_sa4)

for outcome, preds, label in [
    ('h_phys_t1', ['h_phys_t', 'w_phys_t'], '丈夫身体(SA4)'),
    ('w_phys_t1', ['w_phys_t', 'h_phys_t'], '妻子身体(SA4)'),
    ('h_cesd_t1', ['h_cesd_t', 'w_cesd_t'], '丈夫CESD(SA4)'),
    ('w_cesd_t1', ['w_cesd_t', 'h_cesd_t'], '妻子CESD(SA4)'),
]:
    data = df_sa4[['householdID', outcome] + preds].dropna()
    if len(data) < 100: continue
    y = data[outcome]
    X = sm.add_constant(data[preds])
    try:
        gee = GEE(y, X, groups=data['householdID'], family=Gaussian(), cov_struct=Exchangeable())
        res = gee.fit()
        cross_pred = preds[1]
        b, p = res.params[cross_pred], res.pvalues[cross_pred]
        se = res.bse[cross_pred]
        sig = '***' if p<0.001 else ('**' if p<0.01 else ('*' if p<0.05 else ''))
        print(f"  {label} Partner: β={b:.4f} (SE={se:.4f}) P={p:.4f}{sig}")
        sensitivity_results.append({'分析': 'SA4-至少2轮', '模型': label, 'β': b, 'SE': se, 'P': p, '显著': sig})
    except: pass

# 保存敏感性分析结果
sa_df = pd.DataFrame(sensitivity_results)
sa_df.to_csv(os.path.join(TAB_DIR, "table9_sensitivity.csv"), index=False, encoding='utf-8-sig')
print(f"\n敏感性结果已保存: table9_sensitivity.csv")

# ============================================================
# 5. 敏感性分析森林图
# ============================================================
print("\n绘制敏感性分析森林图...")

# 读取主分析结果
main_clpm = pd.read_csv(os.path.join(TAB_DIR, "table6_clpm_results.csv"))
main_cross = main_clpm[main_clpm['效应类型'] == '交叉效应(Partner)'].copy()
main_cross['β'] = main_cross['β'].astype(float)

fig, axes = plt.subplots(1, 2, figsize=(16, 8))

for ax_idx, var_type in enumerate(['身体', 'CESD']):
    ax = axes[ax_idx]

    # 主分析
    main_sub = main_cross[main_cross['因变量'].str.contains(var_type)]
    sa_sub = sa_df[sa_df['模型'].str.contains(var_type)]

    all_rows = []
    for _, r in main_sub.iterrows():
        all_rows.append({
            'label': f"主分析-{r['因变量'][:4]}",
            'beta': float(r['β']), 'se': float(r['SE']),
            'color': '#2196F3'
        })
    for _, r in sa_sub.iterrows():
        all_rows.append({
            'label': f"{r['分析']}-{r['模型'][:4]}",
            'beta': r['β'], 'se': r['SE'],
            'color': '#FF9800'
        })

    if not all_rows:
        continue

    y_positions = range(len(all_rows))
    betas = [r['beta'] for r in all_rows]
    errors = [1.96 * r['se'] for r in all_rows]
    colors = [r['color'] for r in all_rows]
    labels = [r['label'] for r in all_rows]

    ax.errorbar(betas, list(y_positions), xerr=errors, fmt='o', color='black',
                capsize=4, markersize=6, linewidth=1.5, zorder=3)
    for i, (b, c) in enumerate(zip(betas, colors)):
        ax.scatter(b, i, color=c, s=80, zorder=4)

    ax.axvline(x=0, color='grey', linestyle='--', linewidth=0.8)
    ax.set_yticks(list(y_positions))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel('Partner效应 β (95% CI)', fontsize=12)
    ax.set_title(f'{var_type}共病: 主分析 vs 敏感性分析', fontsize=13)
    ax.grid(True, alpha=0.3, axis='x')

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2196F3', label='主分析'),
        Patch(facecolor='#FF9800', label='敏感性分析'),
    ]
    ax.legend(handles=legend_elements, fontsize=10)

plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "fig14_sensitivity_forest.png"), dpi=300, bbox_inches='tight')
plt.close()
print("已保存: fig14_sensitivity_forest.png")

# ============================================================
# 6. 综合结果汇总图
# ============================================================
print("\n绘制综合结果概览图...")

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# 6a. 共病趋势 (左上)
ax = axes[0, 0]
for suffix, label, color in [('h', '丈夫', '#2196F3'), ('w', '妻子', '#E91E63')]:
    means = []
    for w in WAVES:
        vals = df_long[df_long['wave'] == w][f'{suffix}_phys_count'].dropna()
        means.append(vals.mean())
    ax.plot([WAVE_YEARS[w] for w in WAVES], means, 'o-', label=f'{label}身体疾病数',
            color=color, linewidth=2.5, markersize=8)
ax.set_xlabel('年份', fontsize=11)
ax.set_ylabel('平均疾病数', fontsize=11)
ax.set_title('A. 夫妻身体疾病数变化趋势', fontsize=13, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)

# 6b. 夫妻相关性趋势 (右上)
ax = axes[0, 1]
corrs_phys, corrs_cesd = [], []
for w in WAVES:
    wd = df_long[df_long['wave'] == w]
    v1 = wd[['h_phys_count', 'w_phys_count']].dropna()
    v2 = wd[['h_cesd10', 'w_cesd10']].dropna()
    r1, _ = stats.spearmanr(v1['h_phys_count'], v1['w_phys_count'])
    r2, _ = stats.spearmanr(v2['h_cesd10'], v2['w_cesd10'])
    corrs_phys.append(r1)
    corrs_cesd.append(r2)
years = [WAVE_YEARS[w] for w in WAVES]
ax.plot(years, corrs_phys, 'o-', label='身体疾病数', color='#4CAF50', linewidth=2.5, markersize=8)
ax.plot(years, corrs_cesd, 's-', label='CESD-10', color='#FF9800', linewidth=2.5, markersize=8)
ax.set_xlabel('年份', fontsize=11)
ax.set_ylabel('Spearman相关系数', fontsize=11)
ax.set_title('B. 夫妻健康指标相关性趋势', fontsize=13, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)

# 6c. CLPM Partner效应对比 (左下)
ax = axes[1, 0]
if len(clpm_cross) > 0:
    clpm_c = clpm_cross.copy()
    beta_c = clpm_c['β_float'] if 'β_float' in clpm_c.columns else clpm_c['β'].apply(lambda x: float(x))
    y_pos_c = range(len(clpm_c))
    colors_c = [get_color(v) for v in clpm_c['因变量']]
    ax.barh(list(y_pos_c), beta_c, color=colors_c, alpha=0.85, height=0.5)
    for i, (v, sig) in enumerate(zip(beta_c, clpm_c['显著性'])):
        ax.text(v + 0.001, i, f'{v:.4f}{sig}', va='center', fontsize=9)
    ax.set_yticks(list(y_pos_c))
    short_labels = [str(v).replace('(t+1)', '').replace('（t+1）', '').strip() for v in clpm_c['因变量']]
    ax.set_yticklabels(short_labels, fontsize=10)
ax.set_xlabel('伙伴效应 β', fontsize=11)
ax.set_title('C. CLPM 配偶溢出效应', fontsize=13, fontweight='bold')
ax.axvline(x=0, color='black', linestyle='--', linewidth=0.8)
ax.grid(True, alpha=0.3, axis='x')

# 6d. APIM 行动者 vs 伙伴 (右下)
ax = axes[1, 1]
apim_df = pd.read_csv(os.path.join(TAB_DIR, "table7_apim_results.csv"))
apim_main = apim_df[apim_df['效应类型'].isin(['Actor效应', 'Partner效应',
                                              '行动者效应', '伙伴效应'])].copy()
apim_main = apim_main[~apim_main['结局变量'].str.contains('交互')].copy()

y_pos = range(len(apim_main))
colors = ['#2196F3' if ('Actor' in e or '行动者' in e) else '#E91E63' for e in apim_main['效应类型']]
ax.barh(list(y_pos), apim_main['β'], color=colors, alpha=0.8, height=0.5)
for i, (v, sig) in enumerate(zip(apim_main['β'], apim_main['显著性'])):
    offset = 0.01 if abs(v) < 0.1 else v * 0.05
    ax.text(v + offset, i, f'{v:.3f}{sig}', va='center', fontsize=9)
ax.set_yticks(list(y_pos))
labels = [f"{r['结局变量'][:6]}-{r['效应类型'][:6]}" for _, r in apim_main.iterrows()]
ax.set_yticklabels(labels, fontsize=9)
ax.set_xlabel('β', fontsize=11)
ax.set_title('D. APIM: Actor vs Partner效应', fontsize=13, fontweight='bold')
ax.axvline(x=0, color='black', linestyle='--', linewidth=0.8)
ax.grid(True, alpha=0.3, axis='x')

plt.suptitle('基于CHARLS的夫妻共病轨迹耦合及交互健康效应研究 — 核心结果概览',
             fontsize=16, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "fig15_overview.png"), dpi=300, bbox_inches='tight')
plt.close()
print("已保存: fig15_overview.png")

# ============================================================
# 最终文件清单
# ============================================================
print("\n" + "="*60)
print("Phase 4 完成! 生成文件清单:")
print("="*60)
print("\n=== 图表 ===")
for f in sorted(os.listdir(FIG_DIR)):
    print(f"  {f}")
print("\n=== 表格 ===")
for f in sorted(os.listdir(TAB_DIR)):
    print(f"  {f}")
