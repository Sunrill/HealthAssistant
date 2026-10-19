from src.lab.parser import parse_text

SAMPLE = """
血常规
检查项目
检查结果
标志
参考值
单位
*白细胞计数
7.73
3.5-9.5
×10^9/L
淋巴细胞绝对值
3.82
↑
1.1-3.2
×10^9/L
血小板计数
171
125-350
×10^9/L
肾功能3 项
检查者:某医生
检查项目
检查结果
标志
参考值
单位
*尿酸
480
↑
208-428
μmol/L
糖化血红蛋白
检查者:某医生
检查项目
检查结果
糖化血红蛋白
5.4
4.0-6.0
%
尿常规
检查者:某医生
检查项目
检查结果
标志
参考值
单位
*尿胆红素
-
-
尿比重
1.025
1.003-1.030
·尿酸升高
·超重
"""


def test_item_count():
    # 白细胞 / 淋巴细胞 / 血小板 / 尿酸 / 糖化 / 尿胆红素 / 尿比重 = 7
    assert len(parse_text(SAMPLE, "2026-10-01").items) == 7


def test_flag_high():
    items = parse_text(SAMPLE, "2026-10-01").items
    uric = [i for i in items if i.name == "尿酸"][0]
    assert uric.flag == "high"
    assert uric.ref_high == 428
    assert uric.unit == "μmol/L"


def test_text_value():
    items = parse_text(SAMPLE, "2026-10-01").items
    bil = [i for i in items if i.name == "尿胆红素"][0]
    assert bil.value == "-"


def test_panel_assignment():
    items = parse_text(SAMPLE, "2026-10-01").items
    assert {i.panel for i in items} == {"血常规", "肾功能", "糖化", "尿常规"}


def test_same_name_panel_and_item():
    """糖化血红蛋白 既是面板标题也是指标名，不能被吞掉。"""
    items = parse_text(SAMPLE, "2026-10-01").items
    hits = [i for i in items if i.name == "糖化血红蛋白"]
    assert len(hits) == 1
    assert hits[0].value == 5.4
    assert hits[0].panel == "糖化"


def test_conclusions():
    assert parse_text(SAMPLE, "2026-10-01").conclusions == ["尿酸升高", "超重"]
