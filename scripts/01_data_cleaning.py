"""
基于CHARLS的夫妻共病轨迹耦合及交互健康效应研究
Phase 1: 数据清洗与夫妻配对
数据源: Harmonized CHARLS (H_CHARLS_D_Data.dta)
"""

import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 0. 路径配置
# ============================================================
BASE_DIR = r"C:\Users\mc_leafwave\OneDrive\文档\统计建模\项目代码"
RAW_PATH = os.path.join(BASE_DIR, "data", "raw", "H_CHARLS_D_Data.dta")
OUT_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(OUT_DIR, exist_ok=True)

print("读取 Harmonized CHARLS 数据...")
df = pd.read_stata(RAW_PATH)
print(f"原始数据: {df.shape[0]} 人, {df.shape[1]} 变量")

# ============================================================
# 1. 变量提取
# ============================================================
# Wave 对应: w1=2011, w2=2013, w3=2015, w4=2018
WAVES = [1, 2, 3, 4]
WAVE_YEARS = {1: 2011, 2: 2013, 3: 2015, 4: 2018}

# --- ID 与配对变量 ---
id_vars = ['ID', 'householdID', 'communityID']
couple_vars = [f'h{w}coupid' for w in WAVES]
wave_vars = [f'inw{w}' for w in WAVES]
iwstat_vars = [f'r{w}iwstat' for w in WAVES]

# --- 人口学变量（时不变）---
demo_vars = ['ragender', 'rabyear', 'raeduc_c', 'raeducl']

# --- 疾病变量（7种身体疾病，按波次）---
DISEASES = ['hibpe', 'diabe', 'hearte', 'stroke', 'lunge', 'arthre', 'cancre']
DISEASE_LABELS = {
    'hibpe': '高血压', 'diabe': '糖尿病', 'hearte': '心脏病',
    'stroke': '脑卒中', 'lunge': '慢性肺病', 'arthre': '关节炎', 'cancre': '癌症'
}

disease_r = [f'r{w}{d}' for w in WAVES for d in DISEASES]
disease_s = [f's{w}{d}' for w in WAVES for d in DISEASES]

# --- 心理健康: CESD-10 抑郁量表 ---
cesd_r = [f'r{w}cesd10' for w in WAVES]
cesd_s = [f's{w}cesd10' for w in WAVES]
depress_r = [f'r{w}depresl' for w in WAVES]  # 抑郁诊断
depress_s = [f's{w}depresl' for w in WAVES]

# --- 认知功能 ---
# tr20: TICS总分(电话认知筛查), imrc: 即时词语回忆, dlrc: 延迟词语回忆, ser7: 连续7减
cog_items = ['tr20', 'imrc', 'dlrc', 'ser7']
cog_r = [f'r{w}{c}' for w in WAVES for c in cog_items]
cog_s = [f's{w}{c}' for w in WAVES for c in cog_items if f's{w}{c}' in df.columns]

# --- 健康结局变量 ---
# ADL/IADL
adl_r = [f'r{w}adla_c' for w in WAVES]
adl_s = [f's{w}adla_c' for w in WAVES]
iadl_r = [f'r{w}iadla_c' for w in WAVES] if 'r1iadla_c' in df.columns else []
iadl_s = [f's{w}iadla_c' for w in WAVES] if 's1iadla_c' in df.columns else []

# 自评健康
shlt_r = [f'r{w}shlt' for w in WAVES if f'r{w}shlt' in df.columns]
shlt_s = [f's{w}shlt' for w in WAVES if f's{w}shlt' in df.columns]

# 生活满意度
satlife_r = [f'r{w}satlife' for w in WAVES]
satlife_s = [f's{w}satlife' for w in WAVES]

# --- 协变量 ---
# 婚姻状态
mstat_r = [f'r{w}mstat' for w in WAVES]
# 户口
hukou_r = [f'r{w}hukou' for w in WAVES]
# BMI
bmi_r = [f'r{w}mbmi' for w in WAVES if f'r{w}mbmi' in df.columns]
bmi_s = [f's{w}mbmi' for w in WAVES if f's{w}mbmi' in df.columns]
# 吸烟饮酒
smoke_r = [f'r{w}smokev' for w in WAVES if f'r{w}smokev' in df.columns]
drink_r = [f'r{w}drinkev' for w in WAVES if f'r{w}drinkev' in df.columns]

# 收集所有需要的列
all_vars = (id_vars + couple_vars + wave_vars + iwstat_vars + demo_vars +
            disease_r + disease_s + cesd_r + cesd_s + depress_r + depress_s +
            cog_r + adl_r + adl_s + shlt_r + shlt_s + satlife_r + satlife_s +
            mstat_r + hukou_r + bmi_r + bmi_s + smoke_r + drink_r)

# 只保留存在的列
all_vars = [v for v in all_vars if v in df.columns]
# 去重
all_vars = list(dict.fromkeys(all_vars))

# 添加 cog_s 中存在的列
for v in cog_s:
    if v in df.columns and v not in all_vars:
        all_vars.append(v)
# 添加 iadl
for v in iadl_r + iadl_s:
    if v in df.columns and v not in all_vars:
        all_vars.append(v)

df_sub = df[all_vars].copy()
print(f"提取变量后: {df_sub.shape[0]} 人, {df_sub.shape[1]} 变量")

# ============================================================
# 2. 数据类型清洗：将分类变量转为数值
# ============================================================
def cat_to_numeric(series):
    """将 Stata 分类标签 (如 '1.Yes', '0.No') 转为数值"""
    if series.dtype == 'category' or series.dtype == object:
        s = series.astype(str)
        # 提取开头的数字
        numeric = s.str.extract(r'^(-?\d+\.?\d*)')[0]
        return pd.to_numeric(numeric, errors='coerce')
    return pd.to_numeric(series, errors='coerce')

print("\n转换分类变量为数值...")
for col in df_sub.columns:
    if col in id_vars + ['communityID']:
        continue  # 保留ID为字符串
    df_sub[col] = cat_to_numeric(df_sub[col])

# ============================================================
# 3. 疾病二值化 & 共病计数
# ============================================================
# 疾病变量: 1=Yes, 0=No, 其他=缺失
for d in DISEASES:
    for w in WAVES:
        for prefix in ['r', 's']:
            col = f'{prefix}{w}{d}'
            if col in df_sub.columns:
                df_sub[col] = df_sub[col].apply(lambda x: 1 if x == 1 else (0 if x == 0 else np.nan))

# 计算每波次的身体共病计数
for w in WAVES:
    for prefix in ['r', 's']:
        disease_cols = [f'{prefix}{w}{d}' for d in DISEASES if f'{prefix}{w}{d}' in df_sub.columns]
        df_sub[f'{prefix}{w}phys_count'] = df_sub[disease_cols].sum(axis=1, min_count=1)

# 抑郁二值化 (CESD-10 >= 10 为抑郁)
for w in WAVES:
    for prefix in ['r', 's']:
        cesd_col = f'{prefix}{w}cesd10'
        if cesd_col in df_sub.columns:
            df_sub[f'{prefix}{w}depressed'] = (df_sub[cesd_col] >= 10).astype(float)
            df_sub.loc[df_sub[cesd_col].isna(), f'{prefix}{w}depressed'] = np.nan

# 认知障碍二值化 (TICS tr20 < 中位数视为认知障碍，后续可调整)
for w in WAVES:
    for prefix in ['r', 's']:
        cog_col = f'{prefix}{w}tr20'
        if cog_col in df_sub.columns:
            median_val = df_sub[cog_col].median()
            df_sub[f'{prefix}{w}cog_impair'] = (df_sub[cog_col] < median_val).astype(float)
            df_sub.loc[df_sub[cog_col].isna(), f'{prefix}{w}cog_impair'] = np.nan

# 综合共病计数 (身体+心理+认知)
for w in WAVES:
    for prefix in ['r', 's']:
        phys = f'{prefix}{w}phys_count'
        dep = f'{prefix}{w}depressed'
        cog = f'{prefix}{w}cog_impair'
        # 共病维度数 (0-3: 无/仅身体/仅心理/仅认知/多维共病)
        dims = []
        if phys in df_sub.columns:
            dims.append((df_sub[phys] >= 2).astype(float))  # 身体共病=至少2种身体疾病
        if dep in df_sub.columns:
            dims.append(df_sub[dep])
        if cog in df_sub.columns:
            dims.append(df_sub[cog])
        if dims:
            df_sub[f'{prefix}{w}multi_dim'] = sum(dims)  # 共病维度数 (0-3)

# 共病模式编码
for w in WAVES:
    for prefix in ['r', 's']:
        phys = f'{prefix}{w}phys_count'
        dep = f'{prefix}{w}depressed'
        cog = f'{prefix}{w}cog_impair'
        has_phys = (df_sub.get(phys, pd.Series(dtype=float)) >= 2).fillna(False)
        has_dep = (df_sub.get(dep, pd.Series(dtype=float)) == 1).fillna(False)
        has_cog = (df_sub.get(cog, pd.Series(dtype=float)) == 1).fillna(False)

        def encode_pattern(p, d, c):
            if p and d and c: return 7  # 身体+心理+认知
            elif p and d: return 4      # 身体+心理
            elif p and c: return 5      # 身体+认知
            elif d and c: return 6      # 心理+认知
            elif p: return 1            # 仅身体
            elif d: return 2            # 仅心理
            elif c: return 3            # 仅认知
            else: return 0              # 无共病

        df_sub[f'{prefix}{w}mm_pattern'] = [
            encode_pattern(p, d, c) for p, d, c in zip(has_phys, has_dep, has_cog)
        ]

PATTERN_LABELS = {
    0: '无共病', 1: '仅身体', 2: '仅心理', 3: '仅认知',
    4: '身体+心理', 5: '身体+认知', 6: '心理+认知', 7: '身体+心理+认知'
}

# ============================================================
# 4. 夫妻配对
# ============================================================
print("\n开始夫妻配对...")

# 筛选条件1: 至少在wave1参与调查
df_w1 = df_sub[df_sub['inw1'] == 1].copy()
print(f"Wave 1 参与者: {len(df_w1)} 人")

# 筛选条件2: wave1时已婚且与配偶同住 (r1mstat == 1)
df_married = df_w1[df_w1['r1mstat'] == 1].copy()
print(f"Wave 1 已婚同住: {len(df_married)} 人")

# 筛选条件3: 年龄 >= 45 (基于 rabyear, wave1年份2011)
df_married['baseline_age'] = 2011 - df_married['rabyear']
df_age = df_married[df_married['baseline_age'] >= 45].copy()
print(f"年龄 >= 45岁: {len(df_age)} 人")

# 利用 householdID 进行配对：同一家庭中的两人即为夫妻
# 先找出每个家庭中恰好有2人的家庭
hh_counts = df_age.groupby('householdID').size()
hh_two = hh_counts[hh_counts == 2].index
df_pairs = df_age[df_age['householdID'].isin(hh_two)].copy()
print(f"同住2人家庭中的个体: {len(df_pairs)} 人 ({len(hh_two)} 对)")

# 按家庭分组，识别丈夫/妻子
couples = []
for hhid, group in df_pairs.groupby('householdID'):
    if len(group) != 2:
        continue
    persons = group.sort_values('ragender')  # 1=男, 2=女 (通常)
    p1, p2 = persons.iloc[0], persons.iloc[1]
    # 确保一男一女
    if p1['ragender'] == 1 and p2['ragender'] == 2:
        husband, wife = p1, p2
    elif p1['ragender'] == 2 and p2['ragender'] == 1:
        husband, wife = p2, p1
    else:
        continue  # 同性别，跳过

    couple_row = {'householdID': hhid}

    # 丈夫变量 (加 _h 后缀)
    for col in persons.columns:
        if col in ['householdID', 'communityID']:
            continue
        couple_row[f'{col}_h'] = husband[col]
        couple_row[f'{col}_w'] = wife[col]

    # 保留communityID
    couple_row['communityID'] = husband['communityID']
    couples.append(couple_row)

df_couple = pd.DataFrame(couples)
print(f"\n成功配对: {len(df_couple)} 对夫妻")

# ============================================================
# 5. 参与波次统计 & 筛选
# ============================================================
# 计算每对夫妻双方共同参与的波次数
for w in WAVES:
    df_couple[f'both_inw{w}'] = (
        (df_couple[f'inw{w}_h'] == 1) & (df_couple[f'inw{w}_w'] == 1)
    ).astype(int)

df_couple['n_common_waves'] = sum(df_couple[f'both_inw{w}'] for w in WAVES)

# 筛选: 至少共同参与2轮
df_final = df_couple[df_couple['n_common_waves'] >= 2].copy()
print(f"至少共同参与2轮: {len(df_final)} 对夫妻")

# 波次分布
print("\n共同参与波次分布:")
print(df_final['n_common_waves'].value_counts().sort_index())

# ============================================================
# 6. 基本描述统计
# ============================================================
print("\n" + "="*60)
print("基线描述统计 (Wave 1)")
print("="*60)

print(f"\n丈夫平均年龄: {df_final['baseline_age_h'].mean():.1f} (SD={df_final['baseline_age_h'].std():.1f})")
print(f"妻子平均年龄: {df_final['baseline_age_w'].mean():.1f} (SD={df_final['baseline_age_w'].std():.1f})")

print(f"\n丈夫 Wave1 身体疾病数: {df_final['r1phys_count_h'].mean():.2f} (SD={df_final['r1phys_count_h'].std():.2f})")
print(f"妻子 Wave1 身体疾病数: {df_final['r1phys_count_w'].mean():.2f} (SD={df_final['r1phys_count_w'].std():.2f})")

print(f"\n丈夫 Wave1 CESD-10: {df_final['r1cesd10_h'].mean():.2f} (SD={df_final['r1cesd10_h'].std():.2f})")
print(f"妻子 Wave1 CESD-10: {df_final['r1cesd10_w'].mean():.2f} (SD={df_final['r1cesd10_w'].std():.2f})")

print(f"\n丈夫 Wave1 抑郁比例: {df_final['r1depressed_h'].mean():.1%}")
print(f"妻子 Wave1 抑郁比例: {df_final['r1depressed_w'].mean():.1%}")

if 'r1cog_impair_h' in df_final.columns:
    print(f"\n丈夫 Wave1 认知障碍比例: {df_final['r1cog_impair_h'].mean():.1%}")
    print(f"妻子 Wave1 认知障碍比例: {df_final['r1cog_impair_w'].mean():.1%}")

# 共病模式分布
print("\n丈夫 Wave1 共病模式分布:")
for code, label in PATTERN_LABELS.items():
    pct = (df_final['r1mm_pattern_h'] == code).mean()
    print(f"  {label}: {pct:.1%}")

print("\n妻子 Wave1 共病模式分布:")
for code, label in PATTERN_LABELS.items():
    pct = (df_final['r1mm_pattern_w'] == code).mean()
    print(f"  {label}: {pct:.1%}")

# ============================================================
# 7. 构建长格式面板数据 (用于轨迹建模)
# ============================================================
print("\n构建长格式面板数据...")

long_rows = []
for idx, row in df_final.iterrows():
    hhid = row['householdID']
    for w in WAVES:
        if row[f'both_inw{w}'] != 1:
            continue
        long_row = {
            'householdID': hhid,
            'wave': w,
            'year': WAVE_YEARS[w],
            # 丈夫
            'h_age': WAVE_YEARS[w] - row['rabyear_h'],
            'h_phys_count': row.get(f'r{w}phys_count_h', np.nan),
            'h_cesd10': row.get(f'r{w}cesd10_h', np.nan),
            'h_depressed': row.get(f'r{w}depressed_h', np.nan),
            'h_cog_impair': row.get(f'r{w}cog_impair_h', np.nan),
            'h_multi_dim': row.get(f'r{w}multi_dim_h', np.nan),
            'h_mm_pattern': row.get(f'r{w}mm_pattern_h', np.nan),
            'h_adl': row.get(f'r{w}adla_c_h', np.nan),
            'h_shlt': row.get(f'r{w}shlt_h', np.nan),
            'h_satlife': row.get(f'r{w}satlife_h', np.nan),
            'h_tr20': row.get(f'r{w}tr20_h', np.nan),
            # 妻子
            'w_age': WAVE_YEARS[w] - row['rabyear_w'],
            'w_phys_count': row.get(f'r{w}phys_count_w', np.nan),
            'w_cesd10': row.get(f'r{w}cesd10_w', np.nan),
            'w_depressed': row.get(f'r{w}depressed_w', np.nan),
            'w_cog_impair': row.get(f'r{w}cog_impair_w', np.nan),
            'w_multi_dim': row.get(f'r{w}multi_dim_w', np.nan),
            'w_mm_pattern': row.get(f'r{w}mm_pattern_w', np.nan),
            'w_adl': row.get(f'r{w}adla_c_w', np.nan),
            'w_shlt': row.get(f'r{w}shlt_w', np.nan),
            'w_satlife': row.get(f'r{w}satlife_w', np.nan),
            'w_tr20': row.get(f'r{w}tr20_w', np.nan),
        }
        # 疾病明细
        for d in DISEASES:
            long_row[f'h_{d}'] = row.get(f'r{w}{d}_h', np.nan)
            long_row[f'w_{d}'] = row.get(f'r{w}{d}_w', np.nan)

        long_rows.append(long_row)

df_long = pd.DataFrame(long_rows)
print(f"长格式数据: {df_long.shape[0]} 行 (夫妻-波次), {df_long.shape[1]} 列")

# ============================================================
# 8. 保存
# ============================================================
wide_path = os.path.join(OUT_DIR, "couples_wide.csv")
long_path = os.path.join(OUT_DIR, "couples_long.csv")

df_final.to_csv(wide_path, index=False, encoding='utf-8-sig')
df_long.to_csv(long_path, index=False, encoding='utf-8-sig')

print(f"\n宽格式数据已保存: {wide_path}")
print(f"长格式数据已保存: {long_path}")
print(f"\n宽格式: {df_final.shape}")
print(f"长格式: {df_long.shape}")
print("\nPhase 1 完成!")
