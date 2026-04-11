"""
基于CHARLS的夫妻共病轨迹耦合及交互健康效应研究
Phase 3 - Part 1: 共病轨迹识别 (LCGA)
使用潜在类别增长分析识别丈夫/妻子各自的共病发展轨迹组
"""

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt
import seaborn as sns
import os, warnings
warnings.filterwarnings('ignore')

BASE_DIR = r"C:\Users\mc_leafwave\OneDrive\文档\统计建模\项目代码"
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
FIG_DIR = os.path.join(BASE_DIR, "output", "figures")
TAB_DIR = os.path.join(BASE_DIR, "output", "tables")

df_wide = pd.read_csv(os.path.join(PROC_DIR, "couples_wide.csv"))
df_long = pd.read_csv(os.path.join(PROC_DIR, "couples_long.csv"))

WAVES = [1, 2, 3, 4]
WAVE_YEARS = {1: 2011, 2: 2013, 3: 2015, 4: 2018}

# ============================================================
# 1. 构建轨迹分析矩阵
# ============================================================
# 只使用共同参与全部4轮的夫妻 (最干净的面板)
full_panel = df_long.groupby('householdID').filter(lambda x: len(x) == 4)
hh_ids = full_panel['householdID'].unique()
print(f"全部4轮完整参与: {len(hh_ids)} 对夫妻")

# 构建宽格式轨迹矩阵: 每行一对夫妻，列为各波次共病计数
traj_data = {}
for hhid in hh_ids:
    couple = full_panel[full_panel['householdID'] == hhid].sort_values('wave')
    row = {'householdID': hhid}
    for _, r in couple.iterrows():
        w = int(r['wave'])
        row[f'h_phys_w{w}'] = r['h_phys_count']
        row[f'w_phys_w{w}'] = r['w_phys_count']
        row[f'h_multi_w{w}'] = r['h_multi_dim']
        row[f'w_multi_w{w}'] = r['w_multi_dim']
        row[f'h_cesd_w{w}'] = r['h_cesd10']
        row[f'w_cesd_w{w}'] = r['w_cesd10']
        row[f'h_pattern_w{w}'] = r['h_mm_pattern']
        row[f'w_pattern_w{w}'] = r['w_mm_pattern']
    traj_data[hhid] = row

df_traj = pd.DataFrame.from_dict(traj_data, orient='index')
print(f"轨迹矩阵: {df_traj.shape}")

# ============================================================
# 2. LCGA: 潜在类别增长分析 (Latent Class Growth Analysis)
# ============================================================
# 时间点编码: 2011=0, 2013=2, 2015=4, 2018=7 (以年为单位的间距)
TIME_POINTS = [0, 2, 4, 7]

def fit_lcga(data_matrix, time_points=None, max_groups=6, poly_order=1, var_name=""):
    """
    潜在类别增长分析 (LCGA) - GBTM的标准实现。
    每个潜在类别k拟合独立的多项式时间函数: Y_it = β_0k + β_1k * t + ε_it
    通过EM算法估计参数。

    data_matrix: N x T 矩阵 (N人, T时间点)
    time_points: 长度T的时间点向量
    poly_order: 多项式阶数 (1=线性, 2=二次)
    """
    if time_points is None:
        time_points = TIME_POINTS
    valid_mask = ~np.any(np.isnan(data_matrix), axis=1)
    Y = data_matrix[valid_mask]
    N, T = Y.shape
    t = np.array(time_points, dtype=float)
    print(f"  {var_name}: 有效样本 {N}/{data_matrix.shape[0]}")

    # 构建时间设计矩阵 (T x p)
    if poly_order == 1:
        X_time = np.column_stack([np.ones(T), t])
    else:
        X_time = np.column_stack([np.ones(T), t, t**2])
    p = X_time.shape[1]

    results = {}
    for K in range(2, max_groups + 1):
        best_ll = -np.inf
        best_params = None

        for init_run in range(20):
            np.random.seed(42 + init_run * 7)
            # 初始化: K-means初始化 + OLS拟合各组参数
            pi = np.ones(K) / K
            labels_init = np.random.choice(K, N)
            Beta = np.zeros((K, p))
            sigma2 = np.ones(K)

            for k in range(K):
                mask_k = labels_init == k
                if mask_k.sum() < 2:
                    Beta[k] = np.random.randn(p) * 0.5
                    sigma2[k] = 1.0
                    continue
                Y_bar_k = Y[mask_k].mean(axis=0)
                Beta[k] = np.linalg.lstsq(X_time, Y_bar_k, rcond=None)[0]
                residuals = Y[mask_k] - (X_time @ Beta[k])
                sigma2[k] = max(residuals.var(), 0.01)

            prev_ll = -np.inf
            for em_iter in range(300):
                # === E-step: 后验概率 ===
                log_resp = np.zeros((N, K))
                for k in range(K):
                    mu_k = X_time @ Beta[k]  # T维均值向量
                    residuals = Y - mu_k     # N x T
                    log_resp[:, k] = (np.log(pi[k] + 1e-300)
                                      - 0.5 * T * np.log(2 * np.pi * sigma2[k])
                                      - 0.5 * np.sum(residuals**2, axis=1) / sigma2[k])

                # 数值稳定softmax
                log_resp_max = log_resp.max(axis=1, keepdims=True)
                resp = np.exp(log_resp - log_resp_max)
                resp_sum = resp.sum(axis=1, keepdims=True)
                resp = resp / resp_sum

                ll = np.sum(np.log(resp_sum.ravel()) + log_resp_max.ravel())

                # === M-step: 更新参数 ===
                N_k = resp.sum(axis=0)
                pi = N_k / N

                for k in range(K):
                    if N_k[k] < 1:
                        continue
                    w = resp[:, k]
                    # 加权均值轨迹
                    Y_bar = (Y.T * w).sum(axis=1) / N_k[k]
                    Beta[k] = np.linalg.lstsq(X_time, Y_bar, rcond=None)[0]
                    residuals = Y - X_time @ Beta[k]
                    sigma2[k] = max(np.sum(w[:, None] * residuals**2) / (N_k[k] * T), 0.001)

                if em_iter > 0 and abs(ll - prev_ll) < 1e-6:
                    break
                prev_ll = ll

            if ll > best_ll:
                best_ll = ll
                best_params = (pi.copy(), Beta.copy(), sigma2.copy(), resp.copy())

        pi, Beta, sigma2, resp = best_params
        labels = resp.argmax(axis=1)
        avg_pp = np.mean(resp.max(axis=1))
        entropy = -np.sum(resp * np.log(resp + 1e-10)) / N

        # BIC & AIC
        n_params = K * (p + 1) + (K - 1)  # Beta(K*p) + sigma2(K) + pi(K-1)
        bic = -2 * best_ll + n_params * np.log(N)
        aic = -2 * best_ll + 2 * n_params

        results[K] = {
            'bic': bic, 'aic': aic, 'avg_pp': avg_pp,
            'entropy': entropy,
            'labels': labels, 'probs': resp,
            'Beta': Beta, 'sigma2': sigma2, 'pi': pi,
            'valid_mask': valid_mask, 'll': best_ll
        }
        print(f"    K={K}: BIC={bic:.0f}, AIC={aic:.0f}, AvgPP={avg_pp:.3f}, "
              f"Entropy={entropy:.3f}, LL={best_ll:.1f}")

    # 选择最优K: BIC最小 且 AvgPP >= 0.70
    candidates = {k: v for k, v in results.items() if v['avg_pp'] >= 0.70}
    if candidates:
        best_k = min(candidates, key=lambda k: candidates[k]['bic'])
    else:
        best_k = min(results, key=lambda k: results[k]['bic'])

    print(f"  最优组数: K={best_k} (BIC={results[best_k]['bic']:.0f}, "
          f"AvgPP={results[best_k]['avg_pp']:.3f})")
    return results, best_k

# --- 丈夫身体共病轨迹 ---
print("\n=== 丈夫身体共病轨迹 (LCGA) ===")
h_phys_matrix = df_traj[[f'h_phys_w{w}' for w in WAVES]].values
h_results, h_best_k = fit_lcga(h_phys_matrix, TIME_POINTS, max_groups=6, var_name="丈夫身体共病")

# --- 妻子身体共病轨迹 ---
print("\n=== 妻子身体共病轨迹 (LCGA) ===")
w_phys_matrix = df_traj[[f'w_phys_w{w}' for w in WAVES]].values
w_results, w_best_k = fit_lcga(w_phys_matrix, TIME_POINTS, max_groups=6, var_name="妻子身体共病")

# --- 丈夫多维共病轨迹 ---
print("\n=== 丈夫多维共病轨迹 (LCGA) ===")
h_multi_matrix = df_traj[[f'h_multi_w{w}' for w in WAVES]].values
h_multi_results, h_multi_best_k = fit_lcga(h_multi_matrix, TIME_POINTS, max_groups=5, var_name="丈夫多维共病")

# --- 妻子多维共病轨迹 ---
print("\n=== 妻子多维共病轨迹 (LCGA) ===")
w_multi_matrix = df_traj[[f'w_multi_w{w}' for w in WAVES]].values
w_multi_results, w_multi_best_k = fit_lcga(w_multi_matrix, TIME_POINTS, max_groups=5, var_name="妻子多维共病")

# ============================================================
# 3. 轨迹组标签赋值 & 按均值排序
# ============================================================
def assign_trajectory_labels(results, best_k, matrix, prefix, df_traj_ref):
    """将轨迹组标签添加到df_traj, 按各组均值排序命名"""
    res = results[best_k]
    valid_mask = res['valid_mask']
    labels = res['labels']
    Beta = res['Beta']
    t = np.array(TIME_POINTS, dtype=float)
    X_time = np.column_stack([np.ones(len(t)), t])

    # 计算各组的拟合轨迹 (基于多项式参数)
    group_means = {}
    for g in range(best_k):
        group_means[g] = X_time @ Beta[g]  # 拟合均值轨迹

    # 按总体均值排序
    overall_means = {g: m.mean() for g, m in group_means.items()}
    sorted_groups = sorted(overall_means, key=overall_means.get)

    # 创建重映射
    remap = {old: new for new, old in enumerate(sorted_groups)}

    # 赋标签
    full_labels = np.full(len(df_traj_ref), np.nan)
    full_labels[valid_mask] = np.array([remap[l] for l in labels])

    # 重排均值
    sorted_means = {remap[g]: m for g, m in group_means.items()}
    group_sizes = {remap[g]: (labels == g).sum() for g in range(best_k)}

    return full_labels, sorted_means, group_sizes

h_traj_labels, h_means, h_sizes = assign_trajectory_labels(
    h_results, h_best_k, h_phys_matrix, 'h_phys', df_traj)
w_traj_labels, w_means, w_sizes = assign_trajectory_labels(
    w_results, w_best_k, w_phys_matrix, 'w_phys', df_traj)
h_multi_labels, h_multi_means, h_multi_sizes = assign_trajectory_labels(
    h_multi_results, h_multi_best_k, h_multi_matrix, 'h_multi', df_traj)
w_multi_labels, w_multi_means, w_multi_sizes = assign_trajectory_labels(
    w_multi_results, w_multi_best_k, w_multi_matrix, 'w_multi', df_traj)

df_traj['h_phys_traj'] = h_traj_labels
df_traj['w_phys_traj'] = w_traj_labels
df_traj['h_multi_traj'] = h_multi_labels
df_traj['w_multi_traj'] = w_multi_labels

# 命名轨迹组
def name_trajectory(means, n_groups):
    """根据轨迹形状自动命名"""
    names = {}
    for g, m in means.items():
        level = m.mean()
        slope = m[-1] - m[0]
        if level < 0.8:
            base = '低位稳定'
        elif level < 1.5:
            base = '中低水平'
        elif level < 2.5:
            base = '中等水平'
        else:
            base = '高位'

        if abs(slope) < 0.3:
            trend = '稳定'
        elif slope > 0:
            trend = '上升'
        else:
            trend = '下降'

        names[g] = f'{base}-{trend}' if trend != '稳定' else base
    return names

h_traj_names = name_trajectory(h_means, h_best_k)
w_traj_names = name_trajectory(w_means, w_best_k)
h_multi_traj_names = name_trajectory(h_multi_means, h_multi_best_k)
w_multi_traj_names = name_trajectory(w_multi_means, w_multi_best_k)

# ============================================================
# 4. 可视化: 轨迹图
# ============================================================
def plot_trajectories(means, sizes, names, title, ylabel, filename):
    """绘制轨迹图"""
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ['#4CAF50', '#2196F3', '#FF9800', '#F44336', '#9C27B0', '#00BCD4']
    years = [WAVE_YEARS[w] for w in WAVES]
    total = sum(sizes.values())

    for g in sorted(means.keys()):
        m = means[g]
        pct = sizes[g] / total * 100
        label = f'{names[g]} (n={sizes[g]}, {pct:.1f}%)'
        ax.plot(years, m, 'o-', color=colors[g % len(colors)],
                linewidth=2.5, markersize=8, label=label)

    ax.set_xlabel('年份', fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend(fontsize=10, loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_xticks(years)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, filename), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"已保存: {filename}")

plot_trajectories(h_means, h_sizes, h_traj_names,
    '丈夫身体共病发展轨迹', '身体疾病数', 'fig7a_traj_h_phys.png')
plot_trajectories(w_means, w_sizes, w_traj_names,
    '妻子身体共病发展轨迹', '身体疾病数', 'fig7b_traj_w_phys.png')
plot_trajectories(h_multi_means, h_multi_sizes, h_multi_traj_names,
    '丈夫多维共病发展轨迹', '共病维度数 (0-3)', 'fig7c_traj_h_multi.png')
plot_trajectories(w_multi_means, w_multi_sizes, w_multi_traj_names,
    '妻子多维共病发展轨迹', '共病维度数 (0-3)', 'fig7d_traj_w_multi.png')

# ============================================================
# 5. 输出轨迹组信息
# ============================================================
print("\n=== 轨迹组汇总 (LCGA) ===")
for label, means, sizes, names in [
    ('丈夫身体共病', h_means, h_sizes, h_traj_names),
    ('妻子身体共病', w_means, w_sizes, w_traj_names),
    ('丈夫多维共病', h_multi_means, h_multi_sizes, h_multi_traj_names),
    ('妻子多维共病', w_multi_means, w_multi_sizes, w_multi_traj_names)
]:
    print(f"\n{label}:")
    total = sum(sizes.values())
    for g in sorted(means.keys()):
        m = means[g]
        print(f"  组{g} ({names[g]}): n={sizes[g]} ({sizes[g]/total:.1%}), "
              f"均值轨迹={[f'{v:.2f}' for v in m]}")

# 保存轨迹标签到文件
df_traj.to_csv(os.path.join(PROC_DIR, "couples_trajectories.csv"), index=False, encoding='utf-8-sig')
print(f"\n轨迹标签已保存到 couples_trajectories.csv")

# 保存模型选择表
model_selection = []
for label, results in [('丈夫身体', h_results), ('妻子身体', w_results),
                        ('丈夫多维', h_multi_results), ('妻子多维', w_multi_results)]:
    for k, res in results.items():
        model_selection.append({
            '变量': label, 'K': k,
            'BIC': f"{res['bic']:.0f}", 'AIC': f"{res['aic']:.0f}",
            'AvgPP': f"{res['avg_pp']:.3f}", 'Entropy': f"{res['entropy']:.3f}"
        })
pd.DataFrame(model_selection).to_csv(
    os.path.join(TAB_DIR, "table5_model_selection.csv"), index=False, encoding='utf-8-sig')

print("\nPhase 3 Part 1 (LCGA轨迹识别) 完成!")
