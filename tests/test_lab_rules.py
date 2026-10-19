from src.lab.rules import deviation_pct, is_critical, judge_flag, severity


def test_judge_boundaries():
    assert judge_flag(428, 208, 428) == "normal"   # 等于上限算正常
    assert judge_flag(429, 208, 428) == "high"
    assert judge_flag(208, 208, 428) == "normal"
    assert judge_flag(207, 208, 428) == "low"


def test_judge_text_value():
    assert judge_flag("-", None, None) == "unknown"


def test_deviation():
    assert deviation_pct(480, 208, 428) == 12.1
    assert deviation_pct(300, 208, 428) is None


def test_severity():
    assert severity(None) == "正常"
    assert severity(5) == "轻度"
    assert severity(12.1) == "中度"
    assert severity(45) == "显著"


def test_critical():
    assert is_critical("葡萄糖", 2.5) is True
    assert is_critical("葡萄糖", 4.85) is False
