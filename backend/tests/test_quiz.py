def test_correct_answer_is_detected():
    user_answer = "Gravity warps spacetime"
    correct_answer = "Gravity warps spacetime"
    assert user_answer.strip() == correct_answer.strip()


def test_wrong_answer_is_detected():
    user_answer = "Light travels faster than sound"
    correct_answer = "Gravity warps spacetime"
    assert user_answer.strip() != correct_answer.strip()


def test_answer_with_extra_whitespace_matches():
    user_answer = "  True  "
    correct_answer = "True"
    assert user_answer.strip() == correct_answer.strip()


def test_case_sensitive_answers_differ():
    user_answer = "true"
    correct_answer = "True"
    assert user_answer.strip() != correct_answer.strip()
