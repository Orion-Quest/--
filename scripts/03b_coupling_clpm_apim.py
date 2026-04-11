"""
基于CHARLS的夫妻共病轨迹耦合及交互健康效应研究
Phase 3 - Part 2: 夫妻轨迹耦合分析 + CLPM + APIM
"""

import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.genmod.families import Gaussian, Binomial
from statsmodels.genmod.cov_struct import Exchangeable, Independence
from semopy import Model as SEMModel
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

df_traj = pd.read_csv(os.path.join(PROC_DIR, "couples_trajectories.csv"))
df_long = pd.read_csv(os.path.join(PROC_DIR, "couples_long.csv"))
df_wide = pd.read_csv(os.path.join(PROC_DIR, "couples_wide.csv"))

WAVES = [1, 2, 3, 4]
WAVE_YEARS = {1: 2011, 2: 2013, 3: 2015, 4: 2018}

print(f"轨迹数据: {df_traj.shape[0]} 对夫妻")

# ============================================================
# 模型一: 夫妻轨迹耦合分析
# ============================================================
print("\n" + "="*60)
print("模型一: 夫妻轨迹耦合分析")
print("="*60)

# 1a. 交叉列联表 + 卡方检验
for var, label in [('phys_traj', '身体共病轨迹'), ('multi_traj', '多维共病轨迹')]:
    h_col = f'h_{var}'
    w_col = f'w_{var}'
    valid = df_traj[[h_col, w_col]].dropna()
    ct = pd.crosstab(valid[h_col], valid[w_col])
    ct_pct = pd.crosstab(valid[h_col], valid[w_col], normalize='all') * 100
    chi2, p, dof, expected = stats.chi2_contingency(ct)

    # Cramer's V
    n = ct.values.sum()
    k = min(ct.shape)
    v = np.sqrt(chi2 / (n * (k - 1)))

    print(f"\n--- {label} ---")
    print(f"卡方={chi2:.2f}, df={dof}, P={'<0.0001' if p < 0.0001 else f'{p:.4f}'}, Cramer's V={v:.3f}")
    print(f"\n联合分布 (%):")
    ct_pct.index = [f'丈夫-组{int(i)}' for i in ct_pct.index]
    ct_pct.columns = [f'妻子-组{int(i)}' for i in ct_pct.columns]
    print(ct_pct.round(1).to_string())

    # 绘制热力图
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(ct_pct, annot=True, fmt='.1f', cmap='YlOrRd', ax=ax,
                linewidths=0.5, cbar_kws={'label': '%'})
    ax.set_title(f'夫妻{label}联合分布 (%)', fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, f'fig8_{var}_coupling.png'), dpi=300, bbox_inches='tight')
    plt.close()

# 1b. 多项Logistic回归: 配偶轨迹预测自身轨迹
print("\n--- 多项Logistic: 丈夫轨迹 ~ 妻子轨迹 (控制协变量) ---")
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# 准备协变量 (从df_wide中获取基线信息)
# 合并轨迹标签和基线变量
df_model = df_traj[['householdID', 'h_phys_traj', 'w_phys_traj',
                     'h_multi_traj', 'w_multi_traj']].copy()

# 从wide数据获取基线协变量
baseline_vars = {}
for idx, row in df_wide.iterrows():
    hhid = row['householdID']
    baseline_vars[hhid] = {
        'h_age': row.get('baseline_age_h', np.nan),
        'w_age': row.get('baseline_age_w', np.nan),
        'h_educ': row.get('raeducl_h', np.nan),
        'w_educ': row.get('raeducl_w', np.nan),
        'h_hukou': row.get('r1hukou_h', np.nan),
        'w_hukou': row.get('r1hukou_w', np.nan),
    }
baseline_df = pd.DataFrame.from_dict(baseline_vars, orient='index')
baseline_df.index.name = 'householdID'
baseline_df = baseline_df.reset_index()

df_model = df_model.merge(baseline_df, on='householdID', how='left')
df_model_clean = df_model.dropna()
print(f"完整数据用于回归: {len(df_model_clean)} 对")

# 多项Logistic (丈夫轨迹 ~ 妻子轨迹 + 协变量)
for dep, indep, label in [
    ('h_phys_traj', 'w_phys_traj', '丈夫身体轨迹~妻子身体轨迹'),
    ('w_phys_traj', 'h_phys_traj', '妻子身体轨迹~丈夫身体轨迹'),
    ('h_multi_traj', 'w_multi_traj', '丈夫多维轨迹~妻子多维轨迹'),
    ('w_multi_traj', 'h_multi_traj', '妻子多维轨迹~丈夫多维轨迹'),
]:
    y = df_model_clean[dep].astype(int)
    X = df_model_clean[[indep, 'h_age', 'w_age', 'h_educ', 'w_educ']].copy()
    X[indep] = X[indep].astype(int)

    # 使用 statsmodels MNLogit
    X_const = sm.add_constant(X)
    try:
        mnl = sm.MNLogit(y, X_const)
        result = mnl.fit(disp=0, maxiter=200)
        print(f"\n{label}:")
        # 提取配偶轨迹的系数
        coef_table = result.summary2().tables[1]
        # 只打印配偶轨迹变量的行
        partner_rows = coef_table[coef_table.index.str.contains(indep)]
        if len(partner_rows) > 0:
            print(partner_rows[['Coef.', 'Std.Err.', 'z', 'P>|z|']].to_string())
        print(f"  Pseudo R2: {result.prsquared:.4f}")
    except Exception as e:
        print(f"\n{label}: 拟合失败 ({e})")

# ============================================================
# 模型二: 交叉滞后面板模型 (CLPM) — 基于SEM
# ============================================================
print("\n" + "="*60)
print("模型二: 交叉滞后面板模型 (CLPM) — SEM实现")
print("="*60)

# 构建CLPM所需的宽格式数据 (每行一对夫妻, 列=各波次变量)
# df_traj 已有 h_phys_w1...h_phys_w4, w_phys_w1...w_phys_w4 等列
# 同时需要 CESD 和多维共病的宽格式
clpm_wide = df_traj[['householdID']].copy()
for var_prefix, long_col in [
    ('h_phys', 'h_phys_count'), ('w_phys', 'w_phys_count'),
    ('h_cesd', 'h_cesd10'), ('w_cesd', 'w_cesd10'),
    ('h_multi', 'h_multi_dim'), ('w_multi', 'w_multi_dim'),
]:
    for w in WAVES:
        wide_col = f'{var_prefix}_w{w}'
        if wide_col in df_traj.columns:
            clpm_wide[wide_col] = df_traj[wide_col]
        else:
            # 从长格式获取
            w_data = df_long[df_long['wave'] == w][['householdID', long_col]].drop_duplicates('householdID')
            w_data = w_data.rename(columns={long_col: wide_col})
            clpm_wide = clpm_wide.merge(w_data, on='householdID', how='left')

clpm_data = clpm_wide.dropna()
print(f"CLPM数据 (完整): {len(clpm_data)} 对夫妻")

clpm_results = []

def run_sem_clpm(data, h_prefix, w_prefix, label, constrained=True):
    """
    用semopy拟合SEM-CLPM模型。
    constrained=True时约束系数跨时间不变 (时间不变性)。
    """
    # 变量名
    hv = [f'{h_prefix}_w{w}' for w in WAVES]
    wv = [f'{w_prefix}_w{w}' for w in WAVES]

    # 检查所有变量存在
    for v in hv + wv:
        if v not in data.columns:
            print(f"  {label}: 缺少变量 {v}, 跳过")
            return []

    subset = data[hv + wv].dropna()
    if len(subset) < 100:
        print(f"  {label}: 样本不足 ({len(subset)}), 跳过")
        return []

    # 构建SEM模型语法
    lines = []
    for i in range(len(WAVES) - 1):
        t, t1 = WAVES[i], WAVES[i+1]
        h_t, h_t1 = f'{h_prefix}_w{t}', f'{h_prefix}_w{t1}'
        w_t, w_t1 = f'{w_prefix}_w{t}', f'{w_prefix}_w{t1}'

        if constrained:
            # 自回归 (约束系数跨时间不变)
            lines.append(f'{h_t1} ~ a1*{h_t}')
            lines.append(f'{w_t1} ~ a2*{w_t}')
            # 交叉滞后 (约束系数跨时间不变)
            lines.append(f'{h_t1} ~ c1*{w_t}')
            lines.append(f'{w_t1} ~ c2*{h_t}')
        else:
            lines.append(f'{h_t1} ~ {h_t}')
            lines.append(f'{w_t1} ~ {w_t}')
            lines.append(f'{h_t1} ~ {w_t}')
            lines.append(f'{w_t1} ~ {h_t}')

    # 同期残差相关
    for w in WAVES:
        lines.append(f'{h_prefix}_w{w} ~~ {w_prefix}_w{w}')

    model_desc = '\n'.join(lines)

    try:
        model = SEMModel(model_desc)
        result = model.fit(subset)
        estimates = model.inspect()

        print(f"\n  --- {label} (SEM-CLPM) ---")
        results_list = []

        # 提取关键系数
        for _, row in estimates.iterrows():
            lval = row['lval']
            op = row['op']
            rval = row['rval']
            est = row['Estimate']
            se = row.get('Std. Err', np.nan)
            z = row.get('z-value', np.nan)
            p = row.get('p-value', np.nan)

            if op == '~':
                # 判断效应类型
                if h_prefix in lval and h_prefix in rval:
                    etype = '自回归(Actor-H)'
                elif w_prefix in lval and w_prefix in rval:
                    etype = '自回归(Actor-W)'
                elif h_prefix in lval and w_prefix in rval:
                    etype = '交叉效应(W→H)'
                elif w_prefix in lval and h_prefix in rval:
                    etype = '交叉效应(H→W)'
                else:
                    continue

                if np.isnan(p):
                    p_str = 'NA'
                    sig = ''
                else:
                    p_str = '<0.0001' if p < 0.0001 else f'{p:.4f}'
                    sig = '***' if p < 0.001 else ('**' if p < 0.01 else ('*' if p < 0.05 else ''))

                ci_low = est - 1.96 * se if not np.isnan(se) else np.nan
                ci_high = est + 1.96 * se if not np.isnan(se) else np.nan

                print(f"    {rval} → {lval} [{etype}]: β={est:.4f} "
                      f"(SE={se:.4f}, 95%CI: {ci_low:.4f}~{ci_high:.4f}), P={p_str}{sig}")

                results_list.append({
                    '因变量': lval, '自变量': rval,
                    '效应类型': etype,
                    'β': f'{est:.4f}', 'SE': f'{se:.4f}',
                    '95%CI': f'({ci_low:.4f}, {ci_high:.4f})',
                    'P': p_str, '显著性': sig
                })

        # 模型拟合指标
        stats_dict = model.calc_stats()
        if isinstance(stats_dict, pd.DataFrame):
            print(f"    模型拟合: ", end="")
            for col in stats_dict.columns:
                val = stats_dict[col].iloc[0]
                if isinstance(val, float):
                    print(f"{col}={val:.3f}  ", end="")
            print()

        return results_list

    except Exception as e:
        print(f"  {label}: SEM拟合失败 ({e})")
        # 回退到GEE实现
        print(f"  {label}: 回退到GEE交叉滞后回归...")
        return run_gee_clpm_fallback(data, h_prefix, w_prefix, label)


def run_gee_clpm_fallback(data, h_prefix, w_prefix, label):
    """GEE回退方案: 当SEM失败时使用"""
    full_panel = df_long.groupby('householdID').filter(lambda x: len(x) == 4)
    clpm_rows = []
    for hhid in full_panel['householdID'].unique():
        couple = full_panel[full_panel['householdID'] == hhid].sort_values('wave').set_index('wave')
        h_col_map = {'h_phys': 'h_phys_count', 'h_cesd': 'h_cesd10', 'h_multi': 'h_multi_dim'}
        w_col_map = {'w_phys': 'w_phys_count', 'w_cesd': 'w_cesd10', 'w_multi': 'w_multi_dim'}
        h_long = h_col_map.get(h_prefix, h_prefix)
        w_long = w_col_map.get(w_prefix, w_prefix)
        for t, t1 in [(1,2), (2,3), (3,4)]:
            if t in couple.index and t1 in couple.index:
                clpm_rows.append({
                    'householdID': hhid,
                    'h_t': couple.loc[t, h_long], 'w_t': couple.loc[t, w_long],
                    'h_t1': couple.loc[t1, h_long], 'w_t1': couple.loc[t1, w_long],
                })
    df_clpm = pd.DataFrame(clpm_rows)
    results_list = []
    for outcome, preds, sub_label in [
        ('h_t1', ['h_t', 'w_t'], f'{label}-H(t+1)'),
        ('w_t1', ['w_t', 'h_t'], f'{label}-W(t+1)'),
    ]:
        d = df_clpm[['householdID', outcome] + preds].dropna()
        if len(d) < 100: continue
        y = d[outcome]
        X = sm.add_constant(d[preds])
        try:
            gee = GEE(y, X, groups=d['householdID'], family=Gaussian(), cov_struct=Exchangeable())
            res = gee.fit()
            for pred in preds:
                coef = res.params[pred]
                se = res.bse[pred]
                p = res.pvalues[pred]
                ci_l, ci_h = coef - 1.96*se, coef + 1.96*se
                is_cross = (('h' in outcome and 'w' in pred) or ('w' in outcome and 'h' in pred))
                etype = '交叉效应(Partner)' if is_cross else '自回归(Actor)'
                p_str = '<0.0001' if p < 0.0001 else f'{p:.4f}'
                sig = '***' if p<0.001 else ('**' if p<0.01 else ('*' if p<0.05 else ''))
                print(f"    [GEE回退] {pred} → {outcome} [{etype}]: β={coef:.4f}, P={p_str}{sig}")
                results_list.append({
                    '因变量': sub_label, '自变量': pred, '效应类型': etype,
                    'β': f'{coef:.4f}', 'SE': f'{se:.4f}',
                    '95%CI': f'({ci_l:.4f}, {ci_h:.4f})', 'P': p_str, '显著性': sig
                })
        except: pass
    return results_list


# 运行CLPM
for h_pref, w_pref, label in [
    ('h_phys', 'w_phys', '身体共病'),
    ('h_cesd', 'w_cesd', 'CESD抑郁'),
    ('h_multi', 'w_multi', '多维共病'),
]:
    res = run_sem_clpm(clpm_data, h_pref, w_pref, label)
    clpm_results.extend(res)

clpm_df = pd.DataFrame(clpm_results)
clpm_df.to_csv(os.path.join(TAB_DIR, "table6_clpm_results.csv"), index=False, encoding='utf-8-sig')
print(f"\nCLPM结果已保存: table6_clpm_results.csv")

# ============================================================
# 模型三: Actor-Partner Interdependence Model (APIM)
# ============================================================
print("\n" + "="*60)
print("模型三: APIM — 交互健康效应")
print("="*60)

# 合并轨迹标签到长格式数据
traj_labels = df_traj[['householdID', 'h_phys_traj', 'w_phys_traj',
                         'h_multi_traj', 'w_multi_traj']].copy()
df_apim = df_long.merge(traj_labels, on='householdID', how='inner')
print(f"APIM数据: {df_apim.shape[0]} 条")

# 将数据重构为个体层面 (dyadic format)
# 每行代表一个个体-波次，包含自身和配偶的轨迹信息
apim_rows = []
for _, row in df_apim.iterrows():
    # 丈夫作为focal person
    apim_rows.append({
        'householdID': row['householdID'],
        'wave': row['wave'],
        'person_id': f"{row['householdID']}_h",
        'gender': 0,  # 0=男
        'actor_phys_traj': row['h_phys_traj'],
        'partner_phys_traj': row['w_phys_traj'],
        'actor_multi_traj': row['h_multi_traj'],
        'partner_multi_traj': row['w_multi_traj'],
        'actor_phys_count': row['h_phys_count'],
        'partner_phys_count': row['w_phys_count'],
        'actor_cesd': row['h_cesd10'],
        'partner_cesd': row['w_cesd10'],
        'actor_adl': row['h_adl'],
        'actor_shlt': row['h_shlt'],
        'actor_tr20': row['h_tr20'],
        'age': row['h_age'],
    })
    # 妻子作为focal person
    apim_rows.append({
        'householdID': row['householdID'],
        'wave': row['wave'],
        'person_id': f"{row['householdID']}_w",
        'gender': 1,  # 1=女
        'actor_phys_traj': row['w_phys_traj'],
        'partner_phys_traj': row['h_phys_traj'],
        'actor_multi_traj': row['w_multi_traj'],
        'partner_multi_traj': row['h_multi_traj'],
        'actor_phys_count': row['w_phys_count'],
        'partner_phys_count': row['h_phys_count'],
        'actor_cesd': row['w_cesd10'],
        'partner_cesd': row['h_cesd10'],
        'actor_adl': row['w_adl'],
        'actor_shlt': row['w_shlt'],
        'actor_tr20': row['w_tr20'],
        'age': row['w_age'],
    })

df_apim_ind = pd.DataFrame(apim_rows)
print(f"APIM个体数据: {df_apim_ind.shape[0]} 条")

# 3a. APIM 回归: 各健康结局
apim_results = []

for outcome, outcome_label in [
    ('actor_cesd', 'CESD-10抑郁得分'),
    ('actor_adl', 'ADL障碍数'),
    ('actor_shlt', '自评健康(1好-5差)'),
    ('actor_tr20', 'TICS认知得分'),
]:
    # 使用共病计数作为连续预测变量
    predictors = ['actor_phys_count', 'partner_phys_count', 'gender', 'age', 'wave']
    data = df_apim_ind[['householdID', 'person_id', outcome] + predictors].dropna()

    if len(data) < 200:
        print(f"\n  {outcome_label}: 样本不足，跳过")
        continue

    y = data[outcome]
    X = sm.add_constant(data[predictors])
    groups = data['person_id']  # 以个体为聚类单元，控制个体内重复测量

    try:
        gee = GEE(y, X, groups=groups, family=Gaussian(),
                  cov_struct=Exchangeable())
        result = gee.fit()

        print(f"\n  --- {outcome_label} ---")
        for pred in ['actor_phys_count', 'partner_phys_count', 'gender']:
            coef = result.params[pred]
            se = result.bse[pred]
            p = result.pvalues[pred]
            ci_low, ci_high = coef - 1.96*se, coef + 1.96*se
            p_str = '<0.0001' if p < 0.0001 else f'{p:.4f}'
            sig = '***' if p<0.001 else ('**' if p<0.01 else ('*' if p<0.05 else ''))

            if pred == 'actor_phys_count':
                etype = 'Actor效应'
            elif pred == 'partner_phys_count':
                etype = 'Partner效应'
            else:
                etype = '性别效应'

            print(f"    {etype}: β={coef:.4f} (95%CI: {ci_low:.4f}, {ci_high:.4f}), P={p_str}{sig}")

            apim_results.append({
                '结局变量': outcome_label, '效应类型': etype,
                'β': coef, 'SE': se,
                'CI_lower': ci_low, 'CI_upper': ci_high,
                'P': p, '显著性': sig
            })

    except Exception as e:
        print(f"  {outcome_label}: 拟合失败 ({e})")

# 3b. APIM with 轨迹组交互效应
print("\n\n--- APIM: 轨迹组交互效应 ---")
for outcome, outcome_label in [
    ('actor_cesd', 'CESD-10抑郁得分'),
    ('actor_adl', 'ADL障碍数'),
]:
    predictors = ['actor_phys_traj', 'partner_phys_traj', 'gender', 'age', 'wave']
    data = df_apim_ind[['householdID', 'person_id', outcome] + predictors].dropna()
    if len(data) < 200:
        continue

    # 添加交互项
    data = data.copy()
    data['actor_x_partner'] = data['actor_phys_traj'] * data['partner_phys_traj']

    y = data[outcome]
    X = sm.add_constant(data[predictors + ['actor_x_partner']])
    groups = data['person_id']  # 以个体为聚类单元

    try:
        gee = GEE(y, X, groups=groups, family=Gaussian(), cov_struct=Exchangeable())
        result = gee.fit()

        print(f"\n  --- {outcome_label} (含交互) ---")
        for pred in ['actor_phys_traj', 'partner_phys_traj', 'actor_x_partner', 'gender']:
            coef = result.params[pred]
            se = result.bse[pred]
            p = result.pvalues[pred]
            ci_low, ci_high = coef - 1.96*se, coef + 1.96*se
            p_str = '<0.0001' if p < 0.0001 else f'{p:.4f}'
            sig = '***' if p<0.001 else ('**' if p<0.01 else ('*' if p<0.05 else ''))

            etype_map = {
                'actor_phys_traj': 'Actor轨迹',
                'partner_phys_traj': 'Partner轨迹',
                'actor_x_partner': 'Actor×Partner交互',
                'gender': '性别'
            }
            etype = etype_map.get(pred, pred)
            print(f"    {etype}: β={coef:.4f} ({ci_low:.4f}, {ci_high:.4f}), P={p_str}{sig}")

            apim_results.append({
                '结局变量': f'{outcome_label}(含交互)', '效应类型': etype,
                'β': coef, 'SE': se,
                'CI_lower': ci_low, 'CI_upper': ci_high,
                'P': p, '显著性': sig
            })
    except Exception as e:
        print(f"  {outcome_label}: 拟合失败 ({e})")

apim_df = pd.DataFrame(apim_results)
apim_df.to_csv(os.path.join(TAB_DIR, "table7_apim_results.csv"), index=False, encoding='utf-8-sig')

# ============================================================
# 模型四: 异质性分析 (亚组)
# ============================================================
print("\n" + "="*60)
print("模型四: 亚组异质性分析")
print("="*60)

# 获取基线户口信息
hukou_map = {}
for _, row in df_wide.iterrows():
    hhid = row['householdID']
    hukou_map[hhid] = row.get('r1hukou_h', np.nan)

df_apim_ind['hukou'] = df_apim_ind['householdID'].map(hukou_map)
df_apim_ind['age_group'] = pd.cut(df_apim_ind['age'], bins=[0, 60, 70, 100],
                                   labels=['45-60', '60-70', '70+'])

subgroup_results = []

for subgroup_var, subgroup_label, categories in [
    ('gender', '性别', {0: '男性', 1: '女性'}),
    ('hukou', '户口', {1: '农村', 2: '城镇'}),
    ('age_group', '年龄组', {'45-60': '45-60岁', '60-70': '60-70岁', '70+': '70岁+'}),
]:
    print(f"\n--- 按{subgroup_label}分层 (结局: CESD-10) ---")
    for cat_val, cat_label in categories.items():
        subset = df_apim_ind[df_apim_ind[subgroup_var] == cat_val].copy()
        data = subset[['householdID', 'person_id', 'actor_cesd', 'actor_phys_count',
                       'partner_phys_count', 'age', 'wave']].dropna()
        if len(data) < 100:
            print(f"  {cat_label}: 样本不足 ({len(data)})")
            continue

        y = data['actor_cesd']
        X = sm.add_constant(data[['actor_phys_count', 'partner_phys_count', 'age', 'wave']])
        groups = data['person_id']  # 以个体为聚类单元

        try:
            gee = GEE(y, X, groups=groups, family=Gaussian(), cov_struct=Exchangeable())
            result = gee.fit()
            for pred, etype in [('actor_phys_count', 'Actor'), ('partner_phys_count', 'Partner')]:
                coef = result.params[pred]
                se = result.bse[pred]
                p = result.pvalues[pred]
                ci_low, ci_high = coef - 1.96*se, coef + 1.96*se
                sig = '***' if p<0.001 else ('**' if p<0.01 else ('*' if p<0.05 else ''))
                print(f"  {cat_label} {etype}: β={coef:.4f} ({ci_low:.4f},{ci_high:.4f}) P={p:.4f}{sig}")
                subgroup_results.append({
                    '分层变量': subgroup_label, '分组': cat_label,
                    '效应': etype, 'β': coef, 'SE': se,
                    'CI_lower': ci_low, 'CI_upper': ci_high,
                    'P': p, '显著性': sig
                })
        except Exception as e:
            print(f"  {cat_label}: 失败 ({e})")

subgroup_df = pd.DataFrame(subgroup_results)
subgroup_df.to_csv(os.path.join(TAB_DIR, "table8_subgroup.csv"), index=False, encoding='utf-8-sig')

# ============================================================
# 可视化: APIM 森林图
# ============================================================
print("\n绘制 APIM 森林图...")

# Actor vs Partner 效应对比
apim_main = apim_df[apim_df['效应类型'].isin(['Actor效应', 'Partner效应'])].copy()
if len(apim_main) > 0:
    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = range(len(apim_main))
    colors = ['#2196F3' if 'Actor' in e else '#E91E63' for e in apim_main['效应类型']]

    ax.barh(y_pos, apim_main['β'], xerr=[apim_main['β'] - apim_main['CI_lower'],
            apim_main['CI_upper'] - apim_main['β']], color=colors, alpha=0.7,
            capsize=3, height=0.6)
    ax.axvline(x=0, color='black', linestyle='--', linewidth=0.8)

    labels = [f"{r['结局变量']}\n{r['效应类型']}{r['显著性']}" for _, r in apim_main.iterrows()]
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel('回归系数 β', fontsize=12)
    ax.set_title('APIM: Actor效应 vs Partner效应', fontsize=14)

    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='#2196F3', alpha=0.7, label='Actor效应 (自身共病→自身结局)'),
                       Patch(facecolor='#E91E63', alpha=0.7, label='Partner效应 (配偶共病→自身结局)')]
    ax.legend(handles=legend_elements, fontsize=10, loc='lower right')
    ax.grid(True, alpha=0.3, axis='x')

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig9_apim_forest.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("已保存: fig9_apim_forest.png")

# 亚组森林图
if len(subgroup_df) > 0:
    fig, axes = plt.subplots(1, 2, figsize=(14, 8))
    for ax_idx, etype in enumerate(['Actor', 'Partner']):
        ax = axes[ax_idx]
        sub = subgroup_df[subgroup_df['效应'] == etype].copy()
        y_pos = range(len(sub))
        ax.errorbar(sub['β'], y_pos, xerr=[sub['β'] - sub['CI_lower'],
                    sub['CI_upper'] - sub['β']], fmt='o', color='#2196F3' if etype=='Actor' else '#E91E63',
                    capsize=4, markersize=6, linewidth=1.5)
        ax.axvline(x=0, color='black', linestyle='--', linewidth=0.8)

        labels = [f"{r['分层变量']}-{r['分组']}{r['显著性']}" for _, r in sub.iterrows()]
        ax.set_yticks(list(y_pos))
        ax.set_yticklabels(labels, fontsize=10)
        ax.set_xlabel('β', fontsize=12)
        ax.set_title(f'{etype}效应 - 亚组分析 (结局: CESD-10)', fontsize=13)
        ax.grid(True, alpha=0.3, axis='x')

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "fig10_subgroup_forest.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("已保存: fig10_subgroup_forest.png")

# ============================================================
# CLPM 路径图 (文字版，用于论文制图参考)
# ============================================================
print("\n--- CLPM 路径系数汇总 (用于绘制路径图) ---")
if len(clpm_df) > 0:
    for _, row in clpm_df.iterrows():
        print(f"  {row['自变量']} → {row['因变量']}: β={row['β']} [{row['效应类型']}] {row['显著性']}")

print("\n" + "="*60)
print("Phase 3 完成!")
print(f"结果表格: {TAB_DIR}")
print(f"图表: {FIG_DIR}")
print("="*60)
