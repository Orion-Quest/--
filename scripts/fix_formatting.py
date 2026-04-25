"""修复论文排版问题，输出副本"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from docx import Document
from docx.shared import Pt, Emu
from docx.oxml.ns import qn
from docx.enum.text import WD_LINE_SPACING
from lxml import etree

path = r'C:\Users\mc_leafwave\OneDrive\文档\统计提交材料\作品全文—20260129.docx'
out_path = r'C:\Users\mc_leafwave\OneDrive\文档\统计提交材料\作品全文—20260129_排版修正.docx'
doc = Document(path)

fixed = 0

# === 辅助函数 ===
def set_line_spacing_exact(para, pts):
    """设置段落行距为固定值N磅"""
    pf = para.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.line_spacing = Pt(pts)

def set_space_before_after(para, before_pt=0, after_pt=0):
    """设置段前段后"""
    pf = para.paragraph_format
    pf.space_before = Pt(before_pt)
    pf.space_after = Pt(after_pt)

def set_east_asian_font(para, font_name):
    """设置段落所有run的中文字体"""
    for run in para.runs:
        rPr = run._element.get_or_add_rPr()
        rFonts = rPr.find(qn('w:rFonts'))
        if rFonts is None:
            rFonts = etree.SubElement(rPr, qn('w:rFonts'))
        rFonts.set(qn('w:eastAsia'), font_name)

def set_font_size(para, pt):
    """设置段落所有run的字号"""
    for run in para.runs:
        run.font.size = Pt(pt)

def remove_first_indent(para):
    """取消首行缩进"""
    pf = para.paragraph_format
    pf.first_line_indent = Pt(0)

# === 修复1: 摘要标题(段落18) 段前段后改为0 ===
para18 = doc.paragraphs[18]
if '\u6458\u8981' in para18.text:  # 摘要
    set_space_before_after(para18, 0, 0)
    # 确保黑体四号
    set_east_asian_font(para18, '\u9ed1\u4f53')  # 黑体
    set_font_size(para18, 14)  # 四号
    fixed += 1
    print('  [1] 摘要标题: 段前段后→0, 字体→黑体四号')

# === 修复2: 摘要正文(段落19-21) 行距改为固定值24磅, 段前段后0 ===
for i in range(19, 22):
    if i < len(doc.paragraphs):
        para = doc.paragraphs[i]
        text = para.text.strip()
        if text and '\u5173\u952e\u8bcd' not in text:  # 不是关键词行
            set_line_spacing_exact(para, 24)
            set_space_before_after(para, 0, 0)
            fixed += 1
            print(f'  [2] 段落{i}(摘要正文): 行距→24磅固定值, 段前段后→0')

# === 修复3: 关键词(段落22) 行距改为24磅, 段前段后0, 修复末尾多余分号 ===
para22 = doc.paragraphs[22]
if '\u5173\u952e\u8bcd' in para22.text:  # 关键词
    set_line_spacing_exact(para22, 24)
    set_space_before_after(para22, 0, 0)
    # 修复末尾多余分号
    for run in para22.runs:
        if '\uff1b\uff1b' in run.text:  # ；；
            run.text = run.text.replace('\uff1b\uff1b', '')
    # "关键词"三字应为黑体小四
    if para22.runs:
        first_run = para22.runs[0]
        if '\u5173\u952e\u8bcd' in first_run.text:
            rPr = first_run._element.get_or_add_rPr()
            rFonts = rPr.find(qn('w:rFonts'))
            if rFonts is None:
                rFonts = etree.SubElement(rPr, qn('w:rFonts'))
            rFonts.set(qn('w:eastAsia'), '\u9ed1\u4f53')  # 黑体
    fixed += 1
    print('  [3] 关键词: 行距→24磅, 段前段后→0, 删除多余分号, 首词→黑体')

# === 修复4: 一级标题 显式设为黑体, 取消首行缩进 ===
level1_indices = []
for i, para in enumerate(doc.paragraphs):
    text = para.text.strip()
    if text in ['\u4e00\u3001\u5f15\u8a00', '\u4e8c\u3001\u6570\u636e\u4e0e\u65b9\u6cd5',
                '\u4e09\u3001\u7ed3\u679c', '\u56db\u3001\u8ba8\u8bba', '\u4e94\u3001\u7ed3\u8bba']:
        # 一、引言  二、数据与方法  三、结果  四、讨论  五、结论
        level1_indices.append(i)

for i in level1_indices:
    para = doc.paragraphs[i]
    set_east_asian_font(para, '\u9ed1\u4f53')  # 黑体
    remove_first_indent(para)
    fixed += 1
    print(f'  [4] 段落{i}("{para.text.strip()}"): 中文字体→黑体, 首缩→0')

# === 修复5: 二级标题 显式设为楷体四号 ===
for i, para in enumerate(doc.paragraphs):
    text = para.text.strip()
    if text.startswith('\uff08') and text.endswith('\uff09') is False:  # （X）开头
        # 检查是否为二级标题格式
        import re
        if re.match(r'^\uff08[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b]\uff09', text):
            set_font_size(para, 14)  # 四号 = 14pt
            set_east_asian_font(para, '\u6977\u4f53')  # 楷体
            fixed += 1

print(f'  [5] 二级标题: 字号→四号(14pt)')

# === 修复6: 表3b(段落159) 行距修正 ===
para159 = doc.paragraphs[159]
if '\u88683b' in para159.text or '3b' in para159.text:  # 表3b
    set_line_spacing_exact(para159, 24)
    fixed += 1
    print(f'  [6] 段落159(表3b标题): 行距→24磅')

# === 修复7: 表11(段落244), 图16(段落246) 行距修正 ===
for idx in [244, 246]:
    if idx < len(doc.paragraphs):
        para = doc.paragraphs[idx]
        pf = para.paragraph_format
        if pf.line_spacing_rule != WD_LINE_SPACING.EXACTLY:
            set_line_spacing_exact(para, 24)
            fixed += 1
            print(f'  [7] 段落{idx}("{para.text.strip()[:20]}"): 行距→24磅')

# === 修复8: "参考文献"标题 设为黑体四号 ===
for i, para in enumerate(doc.paragraphs):
    text = para.text.strip()
    if text == '\u53c2\u8003\u6587\u732e':  # 参考文献
        set_east_asian_font(para, '\u9ed1\u4f53')  # 黑体
        set_font_size(para, 14)  # 四号
        fixed += 1
        print(f'  [8] 段落{i}("参考文献"): 字体→黑体四号')
        break

# === 保存 ===
doc.save(out_path)
print(f'\n共修复 {fixed} 处')
print(f'副本已保存: {out_path}')
