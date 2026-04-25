"""补标剩余6条参考文献"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from docx import Document
from lxml import etree
from docx.oxml.ns import qn
import copy

path = r'C:\Users\mc_leafwave\OneDrive\文档\统计建模\项目代码\paper\基于CHARLS的夫妻共病轨迹耦合及交互健康效应研究6(4).docx'
doc = Document(path)

def add_sup(paragraph, search_text, citation_text):
    full_text = paragraph.text
    pos = full_text.find(search_text)
    if pos == -1:
        return False
    insert_pos = pos + len(search_text)
    char_count = 0
    target_run_idx = -1
    offset_in_run = 0
    for idx, run in enumerate(paragraph.runs):
        run_len = len(run.text)
        if char_count + run_len >= insert_pos:
            target_run_idx = idx
            offset_in_run = insert_pos - char_count
            break
        char_count += run_len
    if target_run_idx == -1:
        return False
    target_run = paragraph.runs[target_run_idx]
    text_before = target_run.text[:offset_in_run]
    text_after = target_run.text[offset_in_run:]
    target_run.text = text_before
    new_run = etree.SubElement(target_run._element.getparent(), qn('w:r'))
    rPr_src = target_run._element.find(qn('w:rPr'))
    if rPr_src is not None:
        new_rPr = copy.deepcopy(rPr_src)
    else:
        new_rPr = etree.SubElement(new_run, qn('w:rPr'))
    vertAlign = new_rPr.find(qn('w:vertAlign'))
    if vertAlign is None:
        vertAlign = etree.SubElement(new_rPr, qn('w:vertAlign'))
    vertAlign.set(qn('w:val'), 'superscript')
    sz = new_rPr.find(qn('w:sz'))
    if sz is not None:
        sz.set(qn('w:val'), '16')
    else:
        sz = etree.SubElement(new_rPr, qn('w:sz'))
        sz.set(qn('w:val'), '16')
    new_run.insert(0, new_rPr)
    new_t = etree.SubElement(new_run, qn('w:t'))
    new_t.text = citation_text
    new_t.set(qn('xml:space'), 'preserve')
    target_run._element.addnext(new_run)
    if text_after:
        after_run = etree.SubElement(new_run.getparent(), qn('w:r'))
        if rPr_src is not None:
            after_rPr = copy.deepcopy(rPr_src)
            after_run.insert(0, after_rPr)
        after_t = etree.SubElement(after_run, qn('w:t'))
        after_t.text = text_after
        after_t.set(qn('xml:space'), 'preserve')
        new_run.addnext(after_run)
    return True

# [2] Wang - 睡眠与共病: 在讨论中找到引用点
# [12] Chen - 家庭空气污染: 文献综述中空气污染后补充
# [15] 卫瑞港 - 深度学习: 可能不需要引用
# [20] Bronfenbrenner - 社会生态: para 42 or 45 "社会生态"
# [24] Bookwala - 照护负担: 讨论中照护责任
# [25] Berg - 夫妻应对模型: 讨论中夫妻健康

fixes = [
    # [20] 社会生态 -> para 42 or 45
    (42, '\u793e\u4f1a\u751f\u6001\u673a\u5236', '[20]'),  # 社会生态机制
    # [2] 睡眠 -> 讨论中如果提到双向关联
    # Search for bidirectional or 双向
    # [24] 照护 -> para with 照护责任
    (214, '\u914d\u5076\u60a3\u75c5\u589e\u52a0\u4e86\u5176\u7167\u62a4\u8d1f\u62c5', '[24]'),  # 配偶患病增加了其照护负担
    # [25] 夫妻应对 -> could go in discussion about dyadic health
    (230, '\u5065\u5eb7\u540c\u5316\u6548\u5e94', '[25]'),  # 健康同化效应
]

for para_idx, search, cite in fixes:
    if para_idx < len(doc.paragraphs):
        result = add_sup(doc.paragraphs[para_idx], search, cite)
        status = 'OK' if result else 'MISS'
        print(f'  {status} [{para_idx}] {cite}')

doc.save(path)
print('\u4fdd\u5b58\u5b8c\u6210')
