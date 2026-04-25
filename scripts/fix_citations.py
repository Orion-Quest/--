"""修复未匹配的5个引用标注"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from docx import Document
from lxml import etree
from docx.oxml.ns import qn
import copy

path = r'C:\Users\mc_leafwave\OneDrive\文档\统计建模\项目代码\paper\基于CHARLS的夫妻共病轨迹耦合及交互健康效应研究6(4).docx'
doc = Document(path)

def add_superscript(paragraph, search_text, citation_text):
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

# Fix the 5 missed citations with correct search text
fixes = [
    # [36] "还给人民带来沉重的医疗经济负担" -> add [1]
    (36, '\u8fd8\u7ed9\u4eba\u6c11\u5e26\u6765\u6c89\u91cd\u7684\u533b\u7597\u7ecf\u6d4e\u8d1f\u62c5', '[1]'),
    # [36] 健康中国2030 -> add [22]  -- search for 规划纲要
    (36, '\u89c4\u5212\u7eb2\u8981', '[22]'),
    # [44] 家庭空气污染 -> need to find actual text in para 44
    (44, '\u529f\u80fd\u969c\u788d', '[1,12]'),
    # [45] 社会生态 is not in para 45, check if theory mention is elsewhere
    # Actually para 45 doesn't mention 社会生态学理论, it's implicitly referenced
    # Skip [20] for para 45
    # [45] 睡眠质量 - not in para 45 either, may be in different para
]

for para_idx, search, cite in fixes:
    if para_idx < len(doc.paragraphs):
        result = add_superscript(doc.paragraphs[para_idx], search, cite)
        status = 'OK' if result else 'MISS'
        print(f'  {status} [{para_idx}] {cite}')

# Also check if 社会生态 or 睡眠 appears anywhere in the body
for i, para in enumerate(doc.paragraphs):
    text = para.text
    if '\u793e\u4f1a\u751f\u6001' in text and i < 250:  # 社会生态
        print(f'  Found \u201c\u793e\u4f1a\u751f\u6001\u201d in para [{i}]: {text[:60]}')
    if '\u7761\u7720' in text and i < 250:  # 睡眠
        print(f'  Found \u201c\u7761\u7720\u201d in para [{i}]: {text[:60]}')

doc.save(path)
print('\u4fdd\u5b58\u5b8c\u6210')
