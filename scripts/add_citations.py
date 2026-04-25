"""在论文正文中标注参考文献序号"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
import re

path = r'C:\Users\mc_leafwave\OneDrive\文档\统计建模\项目代码\paper\基于CHARLS的夫妻共病轨迹耦合及交互健康效应研究6(4).docx'
doc = Document(path)

# 定义：正文中需要标注的位置 -> 对应的参考文献序号
# 格式: (段落索引, 搜索文本, 在该文本后插入的标注)
# 基于对论文内容和参考文献列表的逐一比对

citations = [
    # 一、引言 (一) 研究背景
    (36, '心血管代谢性共病的患病率从上升至，老年群体更是高达', '[3]'),
    (36, '共病不仅会增加死亡风险、缩短预期寿命，还带来沉重的医疗经济负担和生活质量下降', '[1]'),
    (36, '《"健康中国2030"规划纲要》', '[22]'),
    (39, '三维共病的概念', '[18]'),

    # (二) 文献综述
    (44, '兰舒华利用数据发现了对有方向性的二元疾病对和条三元疾病轨迹，大多起源于关节炎或风湿病', '[13]'),
    (44, '空气污染（Peng等,2024）', '[6]'),
    (44, '抑郁症状与代谢指标的联合效应（Liu等,2024）', '[7]'),
    (44, '不良童年经历（Liu等,2024;Zhou等,2025）', '[8,9]'),
    (44, '共病与抑郁', '[1,4,5]'),
    (44, '跌倒', '[10,11]'),
    (44, '家庭空气污染', '[12]'),
    (45, '社会生态学理论', '[20]'),
    (45, '王静文，2024）虽然考察了衰弱的配偶溢出效应', '[14]'),
    (45, '睡眠质量与共病之间存在双向关联', '[2]'),

    # (三) 研究目标与创新
    # 无需标注

    # 二、数据与方法
    (58, '基线调查涉及户家庭的人', '[1]'),

    # 统计方法
    (87, '各组内个体遵循相同的时间增长函数', '[17]'),
    (111, '确保分类的质量', '[17]'),
    (113, '交叉滞后面板模型', '[16]'),
    (117, '时间不变性约束', '[16]'),
    (121, '行动者-伙伴互依模型', '[16]'),
    (124, '广义估计方程进行估计', '[21]'),

    # 三、结果
    # (二) 夫妻共病一致性
    (143, '情绪传染和认知环境的共享可能是比生物学风险更强的配偶健康趋同机制', '[19,23]'),

    # 四、讨论
    (230, '配偶共病发展轨迹并非相互独立的', '[23,27]'),
    (231, '抑郁的传染效应远强于身体疾病', '[19]'),
    (232, '王静文关于配偶衰弱对妻子生活满意度影响更大的结论相呼应', '[14]'),
    (234, '等,;等,）相比', '[4,5]'),
    (235, '情绪感染、共同压力源暴露和社会退缩的连锁反应等机制实现传播', '[19,26]'),
    (237, '慢性病防控策略具有直接的政策启示', '[22]'),
]

def add_superscript_citation(paragraph, search_text, citation_text):
    """在段落中找到search_text后插入上标格式的citation_text"""
    full_text = paragraph.text
    pos = full_text.find(search_text)
    if pos == -1:
        return False

    insert_pos = pos + len(search_text)

    # 找到插入位置所在的run
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

    # 修改当前run为插入点之前的文本
    target_run.text = text_before

    # 创建上标run (插入在当前run之后)
    from lxml import etree
    new_run = etree.SubElement(target_run._element.getparent(), qn('w:r'))

    # 复制原run的格式属性
    rPr_src = target_run._element.find(qn('w:rPr'))
    if rPr_src is not None:
        import copy
        new_rPr = copy.deepcopy(rPr_src)
    else:
        new_rPr = etree.SubElement(new_run, qn('w:rPr'))

    # 添加上标属性
    vertAlign = new_rPr.find(qn('w:vertAlign'))
    if vertAlign is None:
        vertAlign = etree.SubElement(new_rPr, qn('w:vertAlign'))
    vertAlign.set(qn('w:val'), 'superscript')

    # 设置字号稍小
    sz = new_rPr.find(qn('w:sz'))
    if sz is not None:
        sz.set(qn('w:val'), '16')  # 8pt
    else:
        sz = etree.SubElement(new_rPr, qn('w:sz'))
        sz.set(qn('w:val'), '16')

    new_run.insert(0, new_rPr)
    new_t = etree.SubElement(new_run, qn('w:t'))
    new_t.text = citation_text
    new_t.set(qn('xml:space'), 'preserve')

    # 将new_run移到target_run之后
    target_run._element.addnext(new_run)

    # 如果有剩余文本，创建一个新run放在上标之后
    if text_after:
        after_run = etree.SubElement(new_run.getparent(), qn('w:r'))
        if rPr_src is not None:
            import copy
            after_rPr = copy.deepcopy(rPr_src)
            after_run.insert(0, after_rPr)
        after_t = etree.SubElement(after_run, qn('w:t'))
        after_t.text = text_after
        after_t.set(qn('xml:space'), 'preserve')
        new_run.addnext(after_run)

    return True

# 应用所有标注
success = 0
fail = 0
for para_idx, search, cite in citations:
    if para_idx < len(doc.paragraphs):
        result = add_superscript_citation(doc.paragraphs[para_idx], search, cite)
        if result:
            success += 1
            print(f'  OK [{para_idx}] {cite}')
        else:
            fail += 1
            # 尝试搜索文本的前20个字符
            short = search[:20]
            print(f'  MISS [{para_idx}] {cite} (找不到: "{short}...")')

print(f'\n成功标注: {success}, 未匹配: {fail}')

# 保存
doc.save(path)
print(f'文件已保存: {path}')
