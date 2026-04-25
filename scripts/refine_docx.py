"""精炼论文docx文件"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from docx import Document

path = r'C:\Users\mc_leafwave\OneDrive\文档\基于CHARLS的夫妻共病轨迹耦合及交互健康效应研究 - 修订.docx'
doc = Document(path)

replacements = {}

# ---- ABSTRACT: merge into one dense paragraph ----
new_abstract = (
    '\u968f\u7740\u4eba\u53e3\u8001\u9f84\u5316\u7684\u52a0\u901f\uff0c\u5171\u75c5\u5df2\u6210\u4e3a\u5a01\u80c1\u4e2d\u8001\u5e74\u4eba\u7fa4\u5065\u5eb7\u7684\u91cd\u5927\u516c\u5171\u536b\u751f\u95ee\u9898\uff0c'  # 随着人口老龄化的加速，共病已成为威胁中老年人群健康的重大公共卫生问题，
    '\u4f46\u73b0\u6709\u7814\u7a76\u51e0\u4e4e\u5747\u4ee5\u4e2a\u4f53\u4e3a\u5206\u6790\u5355\u5143\uff0c'  # 但现有研究几乎均以个体为分析单元，
    '\u672a\u80fd\u63ed\u793a\u592b\u59bb\u8fd9\u4e00\u6700\u7d27\u5bc6\u793e\u4f1a\u4e8c\u5143\u4f53\u4e4b\u95f4\u7684\u5171\u75c5\u534f\u540c\u6f14\u5316\u673a\u5236\u3002'  # 未能揭示夫妻这一最紧密社会二元体之间的共病协同演化机制。
    '\u672c\u7814\u7a76\u57fa\u4e8eCHARLS 2011\u20142018\u5e74\u56db\u8f6e\u7eb5\u5411\u6570\u636e\uff0c'  # 本研究基于CHARLS 2011—2018年四轮纵向数据，
    '\u4ee55,779\u5bf9\u4e2d\u8001\u5e74\u592b\u59bb\u4e3a\u7814\u7a76\u5bf9\u8c61\uff0c'  # 以5,779对中老年夫妻为研究对象，
    '\u6784\u5efa\u201cGBTM\u2014CLPM\u2014APIM\u201d\u4e09\u9636\u6bb5\u5efa\u6a21\u6846\u67b6\uff0c'  # 构建"GBTM—CLPM—APIM"三阶段建模框架，
    '\u4ece\u8f68\u8ff9\u8bc6\u522b\u3001\u52a8\u6001\u8026\u5408\u5230\u4ea4\u4e92\u6548\u5e94\u4e09\u4e2a\u5c42\u6b21\u7cfb\u7edf\u5206\u6790\u592b\u59bb\u5171\u75c5\u7684\u534f\u540c\u6f14\u5316\u3002'  # 从轨迹识别、动态耦合到交互效应三个层次系统分析夫妻共病的协同演化。
    '\u7ed3\u679c\u8868\u660e\uff1aGBTM\u8bc6\u522b\u51fa\u4e08\u592b\u548c\u59bb\u5b50\u54046\u7ec4\u8eab\u4f53\u5171\u75c5\u8f68\u8ff9\u4e0e5\u7ec4\u591a\u7ef4\u5171\u75c5\u8f68\u8ff9\uff0c'  # 结果表明：GBTM识别出丈夫和妻子各6组身体共病轨迹与5组多维共病轨迹，
    '\u592b\u59bb\u8f68\u8ff9\u7684\u8054\u5408\u5206\u5e03\u663e\u8457\u504f\u79bb\u72ec\u7acb\u5047\u8bbe\uff08P<0.001\uff09\uff0c'  # 夫妻轨迹的联合分布显著偏离独立假设（P<0.001），
    '\u591a\u7ef4\u5171\u75c5\u7684\u8026\u5408\u6548\u5e94\u7ea6\u4e3a\u7eaf\u8eab\u4f53\u5171\u75c5\u76841.7\u500d\uff1b'  # 多维共病的耦合效应约为纯身体共病的1.7倍；
    'CLPM\u63ed\u793a\u4e86\u914d\u5076\u8eab\u4f53\u5171\u75c5\uff08\u03b2=0.022\u20140.026\uff09\u3001\u6291\u90c1\uff08\u03b2=0.078\u20140.087\uff09'  # CLPM揭示了配偶身体共病（β=0.022—0.026）、抑郁（β=0.078—0.087）
    '\u548c\u591a\u7ef4\u5171\u75c5\uff08\u03b2=0.075\u20140.078\uff09\u5747\u5b58\u5728\u663e\u8457\u7684\u53cc\u5411\u4ea4\u53c9\u6ede\u540e\u6548\u5e94\uff08\u5747P<0.001\uff09\uff0c'  # 和多维共病（β=0.075—0.078）均存在显著的双向交叉滞后效应（均P<0.001），
    '\u5176\u4e2d\u6291\u90c1\u7684\u4f20\u67d3\u6548\u5e94\u7ea6\u4e3a\u8eab\u4f53\u75be\u75c5\u7684\u56db\u500d\uff1b'  # 其中抑郁的传染效应约为身体疾病的四倍；
    'APIM\u8868\u660e\u914d\u5076\u6bcf\u589e\u52a0\u4e00\u79cd\u6162\u6027\u75be\u75c5\uff0c\u4e2a\u4f53\u6291\u90c1\u5f97\u5206\u589e\u52a00.30\u5206\uff08P<0.001\uff09\uff0c'  # APIM表明配偶每增加一种慢性疾病，个体抑郁得分增加0.30分（P<0.001），
    '\u4e14\u5973\u6027\u53d7\u914d\u5076\u5171\u75c5\u5f71\u54cd\u7684\u7a0b\u5ea6\uff08\u03b2=0.41\uff09\u7ea6\u4e3a\u7537\u6027\uff08\u03b2=0.20\uff09\u7684\u4e24\u500d\u3002'  # 且女性受配偶共病影响的程度（β=0.41）约为男性（β=0.20）的两倍。
    '\u4e0a\u8ff0\u7ed3\u8bba\u5728\u56db\u9879\u654f\u611f\u6027\u5206\u6790\u4e2d\u5747\u4fdd\u6301\u7a33\u5065\u3002'  # 上述结论在四项敏感性分析中均保持稳健。
    '\u672c\u7814\u7a76\u9996\u6b21\u4ece\u592b\u59bb\u4e8c\u5143\u4f53\u89c6\u89d2\u63ed\u793a\u4e86\u5171\u75c5\u8f68\u8ff9\u7684\u8026\u5408\u73b0\u8c61\u4e0e\u914d\u5076\u5065\u5eb7\u6ea2\u51fa\u6548\u5e94\uff0c'  # 本研究首次从夫妻二元体视角揭示了共病轨迹的耦合现象与配偶健康溢出效应，
    '\u4e3a\u6162\u6027\u75c5\u9632\u63a7\u4e2d\u5f15\u5165\u201c\u592b\u59bb\u8054\u5408\u5e72\u9884\u201d\u7b56\u7565\u63d0\u4f9b\u4e86\u5b9a\u91cf\u4f9d\u636e\u3002'  # 为慢性病防控中引入"夫妻联合干预"策略提供了定量依据。
)
replacements[2] = new_abstract
replacements[3] = ""
replacements[4] = ""
replacements[5] = ""

# ---- Fix keywords ----
replacements[6] = "\u5173\u952e\u8bcd\uff1a\u5171\u75c5\uff1b\u592b\u59bb\u4e8c\u5143\u4f53\uff1b\u7eb5\u5411\u8f68\u8ff9\uff1b\u7ec4\u57fa\u8f68\u8ff9\u6a21\u578b\uff1b\u4ea4\u53c9\u6ede\u540e\u9762\u677f\u6a21\u578b\uff1b\u884c\u52a8\u8005-\u4f19\u4f34\u4e92\u4f9d\u6a21\u578b\uff1bCHARLS"
# 关键词：共病；夫妻二元体；纵向轨迹；组基轨迹模型；交叉滞后面板模型；行动者-伙伴互依模型；CHARLS

# ---- Tighten introduction 1.1 (para 10) ----
replacements[10] = (
    "\u968f\u7740\u4eba\u53e3\u8001\u9f84\u5316\u7684\u52a0\u901f\u63a8\u8fdb\uff0c"  # 随着人口老龄化的加速推进，
    "\u5171\u75c5\u2014\u2014\u5373\u4e2a\u4f53\u540c\u65f6\u60a3\u6709\u4e24\u79cd\u53ca\u4ee5\u4e0a\u6162\u6027\u75be\u75c5\u2014\u2014"  # 共病——即个体同时患有两种及以上慢性疾病——
    "\u5df2\u6210\u4e3a\u5168\u7403\u516c\u5171\u536b\u751f\u9886\u57df\u9762\u4e34\u7684\u91cd\u5927\u6311\u6218\u3002"  # 已成为全球公共卫生领域面临的重大挑战。
    "\u4e2d\u56fd\u662f\u4e16\u754c\u4e0a\u8001\u9f84\u4eba\u53e3\u6700\u591a\u7684\u56fd\u5bb6\uff0c"  # 中国是世界上老龄人口最多的国家，
    "\u57fa\u4e8eCHARLS\u7684\u7814\u7a76\u53d1\u73b0\uff0c2011\u81f32016\u5e74\u95f4\u5fc3\u8840\u7ba1\u4ee3\u8c22\u6027\u5171\u75c5\u7684\u60a3\u75c5\u7387\u4ece2.4%\u4e0a\u5347\u81f35.9%\uff0c"  # 基于CHARLS的研究发现，2011至2016年间心血管代谢性共病的患病率从2.4%上升至5.9%，
    "\u8001\u5e74\u7fa4\u4f53\u66f4\u662f\u9ad8\u8fbe11.6%\u3002"  # 老年群体更是高达11.6%。
    "\u5171\u75c5\u4e0d\u4ec5\u5bfc\u81f4\u5168\u56e0\u6b7b\u4ea1\u98ce\u9669\u663e\u8457\u589e\u52a0\u3001\u9884\u671f\u5bff\u547d\u7f29\u77ed\uff0c"  # 共病不仅导致全因死亡风险显著增加、预期寿命缩短，
    "\u8fd8\u5e26\u6765\u6c89\u91cd\u7684\u533b\u7597\u7ecf\u6d4e\u8d1f\u62c5\u548c\u751f\u6d3b\u8d28\u91cf\u4e0b\u964d\u3002"  # 还带来沉重的医疗经济负担和生活质量下降。
    "\u300a\u201c\u5065\u5eb7\u4e2d\u56fd2030\u201d\u89c4\u5212\u7eb2\u8981\u300b\u660e\u786e\u5c06\u6162\u6027\u75c5\u9632\u63a7\u5217\u4e3a\u4f18\u5148\u4e8b\u9879\uff0c"  # 《"健康中国2030"规划纲要》明确将慢性病防控列为优先事项，
    "\u800c\u5171\u75c5\u4f5c\u4e3a\u6162\u6027\u75c5\u7684\u201c\u590d\u6742\u53e0\u52a0\u6001\u201d\uff0c\u5176\u9632\u63a7\u96be\u5ea6\u8fdc\u8d85\u5355\u4e00\u75be\u75c5\u3002"  # 而共病作为慢性病的"复杂叠加态"，其防控难度远超单一疾病。
)

# ---- Apply replacements ----
for idx, new_text in replacements.items():
    if idx < len(doc.paragraphs):
        para = doc.paragraphs[idx]
        if new_text == "":
            for run in para.runs:
                run.text = ""
        else:
            if para.runs:
                first_run = para.runs[0]
                for run in para.runs:
                    run.text = ""
                first_run.text = new_text
            else:
                para.text = new_text

# Save
doc.save(path)

# Verify
doc2 = Document(path)
ref_started = False
main_chars = 0
for para in doc2.paragraphs:
    text = para.text.strip()
    if '\u53c2\u8003\u6587\u732e' in text and len(text) < 20:  # 参考文献
        ref_started = True
    if not ref_started and text:
        main_chars += len(para.text)

table_chars = sum(len(cell.text) for table in doc2.tables for row in table.rows for cell in row.cells)

print(f'\u4fee\u6539\u540e\u6b63\u6587\u6bb5\u843d\u5b57\u7b26\u6570: {main_chars}')  # 修改后正文段落字符数
print(f'\u8868\u683c\u5b57\u7b26\u6570: {table_chars}')  # 表格字符数
print(f'\u6b63\u6587+\u8868\u683c\u603b\u8ba1: {main_chars + table_chars}')  # 正文+表格总计
print(f'\u8ddd16000\u4e0a\u9650: {16000 - main_chars - table_chars}')  # 距16000上限
print('\u4fee\u6539\u5b8c\u6210\uff01')  # 修改完成！
