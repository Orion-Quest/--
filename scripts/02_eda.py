"""
基于CHARLS的夫妻共病轨迹耦合及交互健康效应研究
Phase 2: 探索性分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
import seaborn as sns
from scipy import stats
import os
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 0. 加载数据
# ============================================================
BASE_DIR = r"C:\Users\mc_leafwave\OneDrive\文档\统计建模\项目代码"
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
FIG_DIR = os.path.join(BASE_DIR, "output", "figures")
TAB_DIR = os.path.join(BASE_DIR, "output", "tables")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(TAB_DIR, exist_ok=True)

df_wide = pd.read_csv(os.path.join(PROC_DIR, "couples_wide.csv"))
df_long = pd.read_csv(os.path.join(PROC_DIR, "couples_long.csv"))

WAVES = [1, 2, 3, 4]
WAVE_YEARS = {1: 2011, 2: 2013, 3: 2015, 4: 2018}
DISEASES = ['hibpe', 'diabe', 'hearte', 'stroke', 'lunge', 'arthre', 'cancre']
DISEASE_CN = {
    'hibpe': '高血压', 'diabe': '糖尿病', 'hearte': '心脏病',
    'stroke': '脑卒中', 'lunge': '慢性肺病', 'arthre': '关节炎', 'cancre': '癌症'
}
PATTERN_LABELS = {
    0: '无共病', 1: '仅身体', 2: '仅心理', 3: '仅认知',
    4: '身体+心理', 5: '身体+认知', 6: '心理+认知', 7: '三重共病'
}

print(f"宽格式: {df_wide.shape}, 长格式: {df_long.shape}")

# ============================================================
# 1. Table 1: 基线特征表
# ============================================================
print("\n" + "="*60)
print("Table 1: 基线特征")
print("="*60)

def describe_continuous(series, name):
    valid = series.dropna()
    return {'变量': name, '均值': f'{valid.mean():.2f}', 'SD': f'{valid.std():.2f}',
            'N': len(valid), '缺失': series.isna().sum()}

def describe_binary(series, name):
    valid = series.dropna()
    pos = valid.sum()
    return {'变量': name, '频数': int(pos), '比例': f'{pos/len(valid):.1%}',
            'N': len(valid), '缺失': series.isna().sum()}

table1_rows = []

# 人口学
for suffix, label in [('_h', '丈夫'), ('_w', '妻子')]:
    table1_rows.append({'变量': f'=== {label} ===', '均值': '', 'SD': '', 'N': '', '缺失': ''})
    table1_rows.append(describe_continuous(df_wide[f'baseline_age{suffix}'], '年龄'))

    # 教育
    educ_col = f'raeducl{suffix}'
    if educ_col in df_wide.columns:
        table1_rows.append(describe_continuous(df_wide[educ_col], '教育水平'))

    # 户口
    hukou_col = f'r1hukou{suffix}'
    if hukou_col in df_wide.columns:
        rural = (df_wide[hukou_col] == 1).astype(float)
        table1_rows.append(describe_binary(rural, '农村户口'))

    # 疾病
    for d in DISEASES:
        col = f'r1{d}{suffix}'
        if col in df_wide.columns:
            table1_rows.append(describe_binary(df_wide[col], DISEASE_CN[d]))

    # 身体疾病数
    table1_rows.append(describe_continuous(df_wide[f'r1phys_count{suffix}'], '身体疾病计数'))

    # CESD
    table1_rows.append(describe_continuous(df_wide[f'r1cesd10{suffix}'], 'CESD-10得分'))
    table1_rows.append(describe_binary(df_wide[f'r1depressed{suffix}'], '抑郁(CESD≥10)'))

    # 认知
    tr20_col = f'r1tr20{suffix}'
    if tr20_col in df_wide.columns:
        table1_rows.append(describe_continuous(df_wide[tr20_col], 'TICS认知得分'))
    cog_col = f'r1cog_impair{suffix}'
    if cog_col in df_wide.columns:
        table1_rows.append(describe_binary(df_wide[cog_col], '认知障碍'))

    # ADL
    adl_col = f'r1adla_c{suffix}'
    if adl_col in df_wide.columns:
        table1_rows.append(describe_continuous(df_wide[adl_col], 'ADL障碍数'))

    # 自评健康
    shlt_col = f'r1shlt{suffix}'
    if shlt_col in df_wide.columns:
        table1_rows.append(describe_continuous(df_wide[shlt_col], '自评健康(1好-5差)'))

    # 共病维度
    md_col = f'r1multi_dim{suffix}'
    if md_col in df_wide.columns:
        table1_rows.append(describe_continuous(df_wide[md_col], '共病维度数(0-3)'))

table1 = pd.DataFrame(table1_rows)
table1.to_csv(os.path.join(TAB_DIR, "table1_baseline.csv"), index=False, encoding='utf-8-sig')
print(table1.to_string(index=False))

# ============================================================
# 2. 各轮共病患病率趋势
# ============================================================
print("\n" + "="*60)
print("共病趋势分析")
print("="*60)

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# 2a. 各疾病患病率趋势
for ax_idx, (suffix, title) in enumerate([('h', '丈夫'), ('w', '妻子')]):
    ax = axes[ax_idx]
    for d in DISEASES:
        rates = []
        for w in WAVES:
            col = f'{suffix}_{d}'
            wave_data = df_long[df_long['wave'] == w][col].dropna()
            rates.append(wave_data.mean() * 100)
        ax.plot([WAVE_YEARS[w] for w in WAVES], rates, 'o-', label=DISEASE_CN[d], linewidth=2)
    ax.set_xlabel('年份', fontsize=12)
    ax.set_ylabel('患病率 (%)', fontsize=12)
    ax.set_title(f'{title} - 各疾病患病率趋势', fontsize=14)
    ax.legend(fontsize=9, ncol=2)
    ax.grid(True, alpha=0.3)

# 2b. 共病维度数趋势
ax = axes[2]
for suffix, label, color in [('h', '丈夫', '#2196F3'), ('w', '妻子', '#E91E63')]:
    means = []
    ci_lower, ci_upper = [], []
    for w in WAVES:
        col = f'{suffix}_multi_dim'
        vals = df_long[df_long['wave'] == w][col].dropna()
        m = vals.mean()
        se = vals.std() / np.sqrt(len(vals))
        means.append(m)
        ci_lower.append(m - 1.96*se)
        ci_upper.append(m + 1.96*se)
    years = [WAVE_YEARS[w] for w in WAVES]
    ax.plot(years, means, 'o-', label=label, color=color, linewidth=2)
    ax.fill_between(years, ci_lower, ci_upper, alpha=0.2, color=color)
ax.set_xlabel('年份', fontsize=12)
ax.set_ylabel('共病维度数 (0-3)', fontsize=12)
ax.set_title('夫妻共病维度数变化趋势', fontsize=14)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "fig1_disease_trends.png"), dpi=300, bbox_inches='tight')
plt.close()
print("图1 已保存: fig1_disease_trends.png")

# ============================================================
# 3. 共病模式分布及变化
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for ax_idx, (suffix, title) in enumerate([('h', '丈夫'), ('w', '妻子')]):
    ax = axes[ax_idx]
    pattern_data = {}
    for w in WAVES:
        col = f'{suffix}_mm_pattern'
        wave_data = df_long[df_long['wave'] == w][col].dropna()
        dist = wave_data.value_counts(normalize=True).sort_index()
        for code in range(8):
            pattern_data.setdefault(PATTERN_LABELS[code], []).append(dist.get(code, 0) * 100)

    years = [str(WAVE_YEARS[w]) for w in WAVES]
    bottom = np.zeros(4)
    colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336', '#00BCD4', '#795548', '#E91E63']
    for i, (pattern, values) in enumerate(pattern_data.items()):
        ax.bar(years, values, bottom=bottom, label=pattern, color=colors[i], alpha=0.85)
        bottom += values
    ax.set_xlabel('年份', fontsize=12)
    ax.set_ylabel('比例 (%)', fontsize=12)
    ax.set_title(f'{title} - 共病模式分布', fontsize=14)
    ax.legend(fontsize=8, loc='center left', bbox_to_anchor=(1, 0.5))

plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "fig2_pattern_distribution.png"), dpi=300, bbox_inches='tight')
plt.close()
print("图2 已保存: fig2_pattern_distribution.png")

# ============================================================
# 4. 夫妻一致性分析
# ============================================================
print("\n" + "="*60)
print("夫妻共病一致性分析")
print("="*60)

# 4a. 各疾病的夫妻Kappa一致性系数 & 卡方检验
print("\n--- Wave 1 各疾病夫妻一致性 ---")
kappa_results = []
for d in DISEASES:
    h_col = f'h_{d}'
    w_col = f'w_{d}'
    w1 = df_long[df_long['wave'] == 1][[h_col, w_col]].dropna()
    if len(w1) == 0:
        continue

    # 列联表
    ct = pd.crosstab(w1[h_col], w1[w_col])

    # 卡方检验
    chi2, p_chi, dof, expected = stats.chi2_contingency(ct)

    # Cohen's Kappa
    h = w1[h_col].values.astype(int)
    w = w1[w_col].values.astype(int)
    n = len(h)
    po = np.sum(h == w) / n
    pe = (np.sum(h == 1) * np.sum(w == 1) + np.sum(h == 0) * np.sum(w == 0)) / n**2
    kappa = (po - pe) / (1 - pe) if pe < 1 else 0

    result = {
        '疾病': DISEASE_CN[d],
        '丈夫患病率': f"{w1[h_col].mean():.1%}",
        '妻子患病率': f"{w1[w_col].mean():.1%}",
        '双方均患比例': f"{((w1[h_col]==1)&(w1[w_col]==1)).mean():.1%}",
        'Kappa': f"{kappa:.3f}",
        'Chi2': f"{chi2:.2f}",
        'P值': f"{p_chi:.4f}" if p_chi > 0.0001 else "<0.0001"
    }
    kappa_results.append(result)
    print(f"  {DISEASE_CN[d]}: Kappa={kappa:.3f}, Chi2={chi2:.2f}, P={'<0.0001' if p_chi < 0.0001 else f'{p_chi:.4f}'}")

kappa_df = pd.DataFrame(kappa_results)
kappa_df.to_csv(os.path.join(TAB_DIR, "table2_kappa.csv"), index=False, encoding='utf-8-sig')

# 4b. 抑郁、认知障碍的夫妻一致性
print("\n--- 心理/认知共病夫妻一致性 ---")
for var, label in [('depressed', '抑郁'), ('cog_impair', '认知障碍')]:
    w1 = df_long[df_long['wave'] == 1][[f'h_{var}', f'w_{var}']].dropna() if f'h_{var}' in df_long.columns else pd.DataFrame()
    if len(w1) == 0:
        # try long format naming
        h_col = f'h_{var}'
        w_col = f'w_{var}'
        if h_col not in df_long.columns:
            continue
        w1 = df_long[df_long['wave'] == 1][[h_col, w_col]].dropna()
    if len(w1) == 0:
        continue

    h_col = f'h_{var}'
    w_col = f'w_{var}'
    ct = pd.crosstab(w1[h_col], w1[w_col])
    chi2, p_chi, _, _ = stats.chi2_contingency(ct)
    h = w1[h_col].values.astype(int)
    w = w1[w_col].values.astype(int)
    n = len(h)
    po = np.sum(h == w) / n
    pe = (np.sum(h == 1) * np.sum(w == 1) + np.sum(h == 0) * np.sum(w == 0)) / n**2
    kappa = (po - pe) / (1 - pe) if pe < 1 else 0
    print(f"  {label}: Kappa={kappa:.3f}, Chi2={chi2:.2f}, P={'<0.0001' if p_chi < 0.0001 else f'{p_chi:.4f}'}")

# 4c. 共病维度数的夫妻相关
print("\n--- 各波次夫妻共病计数 Spearman 相关 ---")
corr_results = []
for w in WAVES:
    w_data = df_long[df_long['wave'] == w][['h_phys_count', 'w_phys_count',
                                             'h_multi_dim', 'w_multi_dim']].dropna()
    r_phys, p_phys = stats.spearmanr(w_data['h_phys_count'], w_data['w_phys_count'])
    r_multi, p_multi = stats.spearmanr(w_data['h_multi_dim'], w_data['w_multi_dim'])
    print(f"  Wave {w} ({WAVE_YEARS[w]}): 身体疾病数 r={r_phys:.3f} (P={'<0.0001' if p_phys<0.0001 else f'{p_phys:.4f}'}), "
          f"共病维度数 r={r_multi:.3f} (P={'<0.0001' if p_multi<0.0001 else f'{p_multi:.4f}'})")
    corr_results.append({
        '波次': f'Wave {w} ({WAVE_YEARS[w]})',
        '身体疾病数_r': f'{r_phys:.3f}', '身体疾病数_P': f'{p_phys:.4f}',
        '共病维度数_r': f'{r_multi:.3f}', '共病维度数_P': f'{p_multi:.4f}'
    })

corr_df = pd.DataFrame(corr_results)
corr_df.to_csv(os.path.join(TAB_DIR, "table3_spousal_correlation.csv"), index=False, encoding='utf-8-sig')

# ============================================================
# 5. 夫妻疾病交叉相关热力图
# ============================================================
print("\n绘制夫妻疾病交叉相关热力图...")

w1 = df_long[df_long['wave'] == 1].copy()
disease_vars_h = [f'h_{d}' for d in DISEASES]
disease_vars_w = [f'w_{d}' for d in DISEASES]
# 加入抑郁和认知
all_health_h = disease_vars_h + ['h_depressed', 'h_cog_impair']
all_health_w = disease_vars_w + ['w_depressed', 'w_cog_impair']
labels_h = [DISEASE_CN[d] for d in DISEASES] + ['抑郁', '认知障碍']
labels_w = labels_h.copy()

# 计算 Phi 系数矩阵 (2x2二值变量的Pearson相关)
phi_matrix = np.zeros((len(all_health_h), len(all_health_w)))
p_matrix = np.zeros_like(phi_matrix)

for i, h_var in enumerate(all_health_h):
    for j, w_var in enumerate(all_health_w):
        valid = w1[[h_var, w_var]].dropna()
        if len(valid) < 10:
            phi_matrix[i, j] = np.nan
            p_matrix[i, j] = 1
            continue
        ct = pd.crosstab(valid[h_var], valid[w_var])
        if ct.shape == (2, 2):
            chi2, p, _, _ = stats.chi2_contingency(ct)
            phi = np.sqrt(chi2 / len(valid))
            # 方向: 正相关/负相关
            if ct.iloc[1, 1] * ct.iloc[0, 0] < ct.iloc[0, 1] * ct.iloc[1, 0]:
                phi = -phi
            phi_matrix[i, j] = phi
            p_matrix[i, j] = p
        else:
            phi_matrix[i, j] = np.nan
            p_matrix[i, j] = 1

fig, ax = plt.subplots(figsize=(12, 10))
mask = np.isnan(phi_matrix)
sns.heatmap(phi_matrix, annot=True, fmt='.3f', cmap='RdBu_r', center=0,
            xticklabels=[f'妻-{l}' for l in labels_w],
            yticklabels=[f'夫-{l}' for l in labels_h],
            ax=ax, mask=mask, vmin=-0.15, vmax=0.15,
            linewidths=0.5, square=True)

# 标记显著性
for i in range(len(all_health_h)):
    for j in range(len(all_health_w)):
        if not np.isnan(phi_matrix[i, j]) and p_matrix[i, j] < 0.05:
            ax.text(j + 0.5, i + 0.85, '*' if p_matrix[i, j] < 0.01 else '†',
                    ha='center', va='center', fontsize=8, color='black')

ax.set_title('夫妻健康状况交叉 Phi 相关系数矩阵 (Wave 1)\n* P<0.01, † P<0.05', fontsize=14)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "fig3_spousal_phi_heatmap.png"), dpi=300, bbox_inches='tight')
plt.close()
print("图3 已保存: fig3_spousal_phi_heatmap.png")

# ============================================================
# 6. 共病模式夫妻联合分布
# ============================================================
print("\n绘制夫妻共病模式联合分布热力图...")

w1_patterns = df_long[df_long['wave'] == 1][['h_mm_pattern', 'w_mm_pattern']].dropna()
ct = pd.crosstab(w1_patterns['h_mm_pattern'], w1_patterns['w_mm_pattern'], normalize='all') * 100

# 重命名
pattern_short = {0: '无', 1: '身体', 2: '心理', 3: '认知', 4: '身+心', 5: '身+认', 6: '心+认', 7: '三重'}
ct.index = [f"夫-{pattern_short[i]}" for i in ct.index]
ct.columns = [f"妻-{pattern_short[i]}" for i in ct.columns]

fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(ct, annot=True, fmt='.1f', cmap='YlOrRd', ax=ax,
            linewidths=0.5, square=True, cbar_kws={'label': '比例 (%)'})
ax.set_title('夫妻共病模式联合分布 (Wave 1, %)', fontsize=14)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "fig4_couple_pattern_joint.png"), dpi=300, bbox_inches='tight')
plt.close()
print("图4 已保存: fig4_couple_pattern_joint.png")

# 卡方检验: 夫妻模式是否独立
ct_raw = pd.crosstab(w1_patterns['h_mm_pattern'], w1_patterns['w_mm_pattern'])
chi2, p, dof, expected = stats.chi2_contingency(ct_raw)
print(f"夫妻共病模式独立性检验: Chi2={chi2:.2f}, df={dof}, P={'<0.0001' if p < 0.0001 else f'{p:.4f}'}")

# ============================================================
# 7. Sankey 图: 共病模式跨波次转换
# ============================================================
print("\n绘制共病模式转换 Sankey 图...")

try:
    import plotly.graph_objects as go

    pattern_colors = {
        0: '#4CAF50', 1: '#2196F3', 2: '#FF9800', 3: '#9C27B0',
        4: '#F44336', 5: '#00BCD4', 6: '#795548', 7: '#E91E63'
    }

    for suffix, title in [('h', '丈夫'), ('w', '妻子')]:
        labels = []
        source, target, value, link_colors = [], [], [], []

        for w in WAVES:
            for code, name in pattern_short.items():
                labels.append(f"{WAVE_YEARS[w]}-{name}")

        for w_idx in range(len(WAVES) - 1):
            w_from, w_to = WAVES[w_idx], WAVES[w_idx + 1]
            both = df_long[df_long['wave'].isin([w_from, w_to])].groupby('householdID').filter(
                lambda x: len(x) == 2
            )
            from_data = both[both['wave'] == w_from].set_index('householdID')[f'{suffix}_mm_pattern']
            to_data = both[both['wave'] == w_to].set_index('householdID')[f'{suffix}_mm_pattern']
            common = from_data.index.intersection(to_data.index)

            for code_from in range(8):
                for code_to in range(8):
                    count = ((from_data.loc[common] == code_from) & (to_data.loc[common] == code_to)).sum()
                    if count > 0:
                        src_idx = w_idx * 8 + code_from
                        tgt_idx = (w_idx + 1) * 8 + code_to
                        source.append(src_idx)
                        target.append(tgt_idx)
                        value.append(int(count))
                        # 将hex颜色转为rgba
                        hex_c = pattern_colors[code_from].lstrip('#')
                        r_c, g_c, b_c = int(hex_c[:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)
                        link_colors.append(f'rgba({r_c},{g_c},{b_c},0.3)')

        node_colors = [pattern_colors[i % 8] for i in range(len(labels))]

        fig = go.Figure(go.Sankey(
            node=dict(pad=15, thickness=20, label=labels, color=node_colors),
            link=dict(source=source, target=target, value=value, color=link_colors)
        ))
        fig.update_layout(title_text=f"{title} - 共病模式跨波次转换流", font_size=12,
                         width=1200, height=600)
        fig.write_image(os.path.join(FIG_DIR, f"fig5_sankey_{suffix}.png"), scale=2)
        print(f"图5 已保存: fig5_sankey_{suffix}.png")

except ImportError:
    print("plotly 未安装, 跳过 Sankey 图。可用 pip install plotly kaleido 安装后重试。")
except Exception as e:
    print(f"Sankey 图生成失败: {e}")
    print("可能需要安装 kaleido: pip install kaleido")

# ============================================================
# 8. 夫妻共病计数散点图 + 回归线 (各波次)
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
for idx, w in enumerate(WAVES):
    ax = axes[idx // 2][idx % 2]
    w_data = df_long[df_long['wave'] == w][['h_phys_count', 'w_phys_count']].dropna()

    # 加抖动避免重叠
    jitter = 0.15
    x = w_data['h_phys_count'] + np.random.normal(0, jitter, len(w_data))
    y = w_data['w_phys_count'] + np.random.normal(0, jitter, len(w_data))

    ax.scatter(x, y, alpha=0.15, s=8, color='steelblue')

    # 回归线
    slope, intercept, r, p, se = stats.linregress(w_data['h_phys_count'], w_data['w_phys_count'])
    x_line = np.linspace(0, 7, 100)
    ax.plot(x_line, intercept + slope * x_line, 'r-', linewidth=2,
            label=f'β={slope:.3f}, r={r:.3f}')

    ax.set_xlabel('丈夫身体疾病数', fontsize=11)
    ax.set_ylabel('妻子身体疾病数', fontsize=11)
    ax.set_title(f'Wave {w} ({WAVE_YEARS[w]})', fontsize=13)
    ax.legend(fontsize=10)
    ax.set_xlim(-0.5, 7)
    ax.set_ylim(-0.5, 7)
    ax.grid(True, alpha=0.3)

plt.suptitle('夫妻身体疾病数量关联 (各波次)', fontsize=15, y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "fig6_couple_scatter.png"), dpi=300, bbox_inches='tight')
plt.close()
print("图6 已保存: fig6_couple_scatter.png")

# ============================================================
# 9. 汇总统计：共病转换矩阵
# ============================================================
print("\n--- 共病模式转换矩阵 (Wave 1 → Wave 4) ---")
for suffix, title in [('h', '丈夫'), ('w', '妻子')]:
    w1_data = df_long[df_long['wave'] == 1].set_index('householdID')[f'{suffix}_mm_pattern']
    w4_data = df_long[df_long['wave'] == 4].set_index('householdID')[f'{suffix}_mm_pattern']
    common = w1_data.index.intersection(w4_data.index)
    trans = pd.crosstab(
        w1_data.loc[common].map(pattern_short),
        w4_data.loc[common].map(pattern_short),
        normalize='index'
    ) * 100
    print(f"\n{title} (行=2011, 列=2018, %):")
    print(trans.round(1).to_string())
    trans.to_csv(os.path.join(TAB_DIR, f"table4_transition_{suffix}.csv"), encoding='utf-8-sig')

print("\n" + "="*60)
print("Phase 2 完成!")
print(f"表格保存在: {TAB_DIR}")
print(f"图片保存在: {FIG_DIR}")
print("="*60)
