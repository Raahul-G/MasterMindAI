"""
Unit tests for streak and achievement logic.
All tests are pure — no database, no HTTP. Logic is extracted and tested directly.
"""
from datetime import date


# ---------------------------------------------------------------------------
# Streak logic helpers (mirroring streak_service logic without DB)
# ---------------------------------------------------------------------------

def _simulate_streak_update(current_streak, longest_streak, last_activity_date, today):
    """Pure reimplementation of streak update logic for unit testing."""
    if last_activity_date is None:
        return 1, 1, today

    if last_activity_date == today:
        return current_streak, longest_streak, last_activity_date

    yesterday = date.fromordinal(today.toordinal() - 1)
    if last_activity_date == yesterday:
        new_streak = current_streak + 1
    else:
        new_streak = 1

    new_longest = max(new_streak, longest_streak)
    return new_streak, new_longest, today


# ---------------------------------------------------------------------------
# Streak tests
# ---------------------------------------------------------------------------

def test_first_activity_starts_streak_at_one():
    today = date(2026, 3, 18)
    current, longest, last = _simulate_streak_update(0, 0, None, today)
    assert current == 1
    assert longest == 1
    assert last == today


def test_consecutive_day_increments_streak():
    today = date(2026, 3, 18)
    yesterday = date(2026, 3, 17)
    current, longest, last = _simulate_streak_update(3, 3, yesterday, today)
    assert current == 4
    assert longest == 4
    assert last == today


def test_same_day_activity_does_not_change_streak():
    today = date(2026, 3, 18)
    current, longest, last = _simulate_streak_update(5, 7, today, today)
    assert current == 5
    assert longest == 7
    assert last == today


def test_missed_day_resets_streak_to_one():
    today = date(2026, 3, 18)
    two_days_ago = date(2026, 3, 16)
    current, longest, last = _simulate_streak_update(10, 10, two_days_ago, today)
    assert current == 1
    assert last == today


def test_longest_streak_preserved_after_reset():
    today = date(2026, 3, 18)
    two_days_ago = date(2026, 3, 16)
    current, longest, last = _simulate_streak_update(10, 10, two_days_ago, today)
    assert longest == 10  # longest should not drop


def test_longest_streak_updates_on_new_record():
    today = date(2026, 3, 18)
    yesterday = date(2026, 3, 17)
    current, longest, last = _simulate_streak_update(7, 7, yesterday, today)
    assert current == 8
    assert longest == 8


def test_longest_streak_not_reduced_when_lower():
    today = date(2026, 3, 18)
    yesterday = date(2026, 3, 17)
    # current is 3, longest is already 14 — should stay 14
    current, longest, last = _simulate_streak_update(3, 14, yesterday, today)
    assert current == 4
    assert longest == 14


# ---------------------------------------------------------------------------
# Achievement condition helpers (mirroring check_and_award_achievements logic)
# ---------------------------------------------------------------------------

def _evaluate_conditions(completed_count, streak_count, used_remediation, first_attempt_perfect):
    """Returns which achievement slugs would be awarded."""
    checks = [
        (completed_count >= 1, "first_steps"),
        (completed_count >= 5, "knowledge_seeker"),
        (completed_count >= 10, "scholar"),
        (first_attempt_perfect, "clean_sweep"),
        (used_remediation, "comeback_kid"),
        (streak_count >= 3, "streak_starter"),
        (streak_count >= 7, "hot_streak"),
        (streak_count >= 14, "dedicated"),
    ]
    return [slug for condition, slug in checks if condition]


# ---------------------------------------------------------------------------
# Achievement tests
# ---------------------------------------------------------------------------

def test_first_module_earns_first_steps():
    slugs = _evaluate_conditions(1, 1, False, False)
    assert "first_steps" in slugs


def test_five_modules_earns_knowledge_seeker():
    slugs = _evaluate_conditions(5, 1, False, False)
    assert "knowledge_seeker" in slugs
    assert "first_steps" in slugs


def test_ten_modules_earns_scholar():
    slugs = _evaluate_conditions(10, 1, False, False)
    assert "scholar" in slugs


def test_perfect_first_attempt_earns_clean_sweep():
    slugs = _evaluate_conditions(1, 1, False, True)
    assert "clean_sweep" in slugs


def test_remediation_used_earns_comeback_kid():
    slugs = _evaluate_conditions(1, 1, True, False)
    assert "comeback_kid" in slugs


def test_three_day_streak_earns_streak_starter():
    slugs = _evaluate_conditions(1, 3, False, False)
    assert "streak_starter" in slugs


def test_seven_day_streak_earns_hot_streak_and_streak_starter():
    slugs = _evaluate_conditions(1, 7, False, False)
    assert "streak_starter" in slugs
    assert "hot_streak" in slugs


def test_fourteen_day_streak_earns_dedicated():
    slugs = _evaluate_conditions(1, 14, False, False)
    assert "dedicated" in slugs
    assert "hot_streak" in slugs
    assert "streak_starter" in slugs


def test_no_achievements_for_zero_activity():
    slugs = _evaluate_conditions(0, 0, False, False)
    assert slugs == []


def test_four_modules_does_not_earn_knowledge_seeker():
    slugs = _evaluate_conditions(4, 1, False, False)
    assert "knowledge_seeker" not in slugs


def test_two_day_streak_does_not_earn_streak_starter():
    slugs = _evaluate_conditions(1, 2, False, False)
    assert "streak_starter" not in slugs
