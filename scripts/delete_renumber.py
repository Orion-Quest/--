"""删除3条未引用参考文献并重新编号参考文献列表"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from docx import Document

path = r'C:\Users\mc_leafwave\OneDrive\文档\统计建模\项目代码\paper\基于CHARLS的夫妻共病轨迹耦合及交互健康效应研究6(4).docx'
doc = Document(path)

# 旧编号 -> 新编号
old_to_new = {}
new_num = 1
for old_num in range(1, 28):
    if old_num in (2, 12, 15):
        old_to_new[old_num] = None
    else:
        old_to_new[old_num] = new_num
        new_num += 1

# 找到参考文献起始位置
ref_start = None
for i, para in enumerate(doc.paragraphs):
    if '\u53c2\u8003\u6587\u732e' in para.text.strip() and len(para.text.strip()) < 20:
        ref_start = i
        break

# 删除旧编号2,12,15对应的段落 (通过清空内容)
# 同时重新编号其余条目
deleted = 0
renumbered = 0

for i in range(ref_start + 1, len(doc.paragraphs)):
    para = doc.paragraphs[i]
    text = para.text.strip()
    if not text:
        continue

    # 尝试提取开头编号
    # 格式可能是 "[1] Zhao..." 或 "Zhao..." (无编号但按顺序)
    # 当前文件中参考文献没有[N]前缀，是按顺序排列的
    # 根据前面的输出，条目从段落251开始，每段一条

    ref_idx = i - (ref_start + 1)  # 0-based index within references
    old_num = ref_idx + 1  # 1-based old number

    if old_num > 27:
        break

    if old_num in (2, 12, 15):
        # 删除这个段落 - 通过清空所有run
        for run in para.runs:
            run.text = ""
        # 同时移除段落的XML元素
        p = para._element
        p.getparent().remove(p)
        deleted += 1
        print(f'  \u5220\u9664 [{old_num}] (para {i})')  # 删除
    else:
        new = old_to_new[old_num]
        # 在第一个run的开头添加 [new] 编号(如果还没有)
        if para.runs:
            first_run = para.runs[0]
            # 检查是否已有编号
            if not first_run.text.startswith('['):
                first_run.text = f'[{new}] ' + first_run.text
            else:
                # 替换已有编号
                first_run.text = re.sub(r'^\[\d+\]\s*', f'[{new}] ', first_run.text)
        renumbered += 1

print(f'\n\u5220\u9664: {deleted} \u6761, \u91cd\u65b0\u7f16\u53f7: {renumbered} \u6761')  # 删除: N 条, 重新编号: N 条

doc.save(path)
print('\u4fdd\u5b58\u5b8c\u6210')  # 保存完成

# 验证
doc2 = Document(path)
ref_started = False
ref_items = []
for para in doc2.paragraphs:
    text = para.text.strip()
    if '\u53c2\u8003\u6587\u732e' in text and len(text) < 20:
        ref_started = True
        continue
    if ref_started and text:
        ref_items.append(text[:80])

print(f'\n\u53c2\u8003\u6587\u732e\u6761\u6570: {len(ref_items)}')  # 参考文献条数
for item in ref_items[:5]:
    print(f'  {item}')
print('  ...')
for item in ref_items[-3:]:
    print(f'  {item}')
