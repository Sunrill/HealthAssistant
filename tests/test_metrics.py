from src.metrics import bmi, bmi_category, bmr, bp_category, sleep_assessment, water_target


def test_bmi_boundaries():
    assert bmi_category(18.4) == "偏瘦"
    assert bmi_category(18.5) == "正常"
    assert bmi_category(24.0) == "超重"
    assert bmi_category(28.0) == "肥胖"


def test_bmi_value():
    assert bmi(70, 175) == 22.9


def test_bmr_male():
    # 10*70 + 6.25*175 - 5*24 + 5
    assert bmr("male", 70, 175, 24) == 1679


def test_bp_urgent():
    cat, urgent = bp_category(185, 112)
    assert cat == "3级高血压" and urgent is True


def test_bp_normal():
    cat, urgent = bp_category(115, 75)
    assert cat == "正常" and urgent is False


def test_sleep():
    assert sleep_assessment(5.5) == "睡眠不足"
    assert sleep_assessment(8) == "达标"
    assert sleep_assessment(9.5) == "睡眠偏长"


def test_water_target():
    assert water_target(70) == 2100
    assert water_target(200) == 3500
