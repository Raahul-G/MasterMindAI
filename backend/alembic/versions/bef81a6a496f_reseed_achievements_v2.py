"""reseed_achievements_v2

Revision ID: bef81a6a496f
Revises: a2d5f8c91e30
Create Date: 2026-03-31

Replaces the original 8 achievement slugs with:
  - 5 mastery bar milestones (Lv.1): mastery_seed_lv1 → mastery_forest_lv1
  - 5 badge locker items: badge_first_leaf, badge_deep_root, badge_wildwood,
                          badge_planter, badge_explorer
  - 14 streak milestones: streak_dew_3 → streak_aurora_365
"""
from typing import Sequence, Union

from alembic import op

revision: str = "bef81a6a496f"
down_revision: Union[str, Sequence[str], None] = "a2d5f8c91e30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_ACHIEVEMENTS = [
    # Mastery bar — Level 1 (higher levels created dynamically by achievement_service)
    ("mastery_seed_lv1",   "Seed",       "Your first concept mastered",               "🌱"),
    ("mastery_sprout_lv1", "Sprout",     "25 concepts mastered",                      "🌿"),
    ("mastery_leaf_lv1",   "Leaf",       "50 concepts mastered",                      "🍃"),
    ("mastery_tree_lv1",   "Tree",       "75 concepts mastered",                      "🌳"),
    ("mastery_forest_lv1", "Forest",     "100 concepts mastered",                     "🌲"),
    # Badge locker
    ("badge_first_leaf",   "First Leaf", "Your very first concept mastered",          "🍀"),
    ("badge_deep_root",    "Deep Root",  "Complete 10 concepts in one module",        "🌾"),
    ("badge_wildwood",     "Wildwood",   "Complete 25 concepts in one module",        "🌿"),
    ("badge_planter",      "Planter",    "3 modules each with at least 1 concept",    "🪴"),
    ("badge_explorer",     "Explorer",   "10 concepts across 3 different modules",    "🗺️"),
    # Streak milestones
    ("streak_dew_3",       "Dew",        "3-day streak",    "💧"),
    ("streak_mist_7",      "Mist",       "7-day streak",    "🌫️"),
    ("streak_rain_14",     "Rain",       "14-day streak",   "🌧️"),
    ("streak_sun_21",      "Sun",        "21-day streak",   "☀️"),
    ("streak_moon_30",     "Moon",       "30-day streak",   "🌙"),
    ("streak_star_60",     "Star",       "60-day streak",   "⭐"),
    ("streak_cloud_90",    "Cloud",      "90-day streak",   "☁️"),
    ("streak_peak_100",    "Peak",       "100-day streak",  "🏔️"),
    ("streak_ridge_150",   "Ridge",      "150-day streak",  "🏔️"),
    ("streak_river_200",   "River",      "200-day streak",  "🌊"),
    ("streak_meadow_250",  "Meadow",     "250-day streak",  "🌾"),
    ("streak_valley_300",  "Valley",     "300-day streak",  "🏞️"),
    ("streak_summit_350",  "Summit",     "350-day streak",  "🗻"),
    ("streak_aurora_365",  "Aurora",     "365-day streak",  "🌌"),
]

_OLD_ACHIEVEMENTS = [
    ("first_steps",      "First Steps",   "Complete your first module",         "👣"),
    ("knowledge_seeker", "Speed Learner", "Complete 5 modules",                 "⚡"),
    ("scholar",          "Curious Mind",  "Complete 10 modules",                "🔭"),
    ("clean_sweep",      "First Try",     "Pass without remediation",           "🥇"),
    ("comeback_kid",     "Comeback Kid",  "Pass after using remediation",       "💪"),
    ("streak_starter",   "On a Roll",     "3-day streak",                       "🎯"),
    ("hot_streak",       "Week Warrior",  "7-day streak",                       "⚔️"),
    ("dedicated",        "Dedicated",     "14-day streak",                      "🏆"),
]


def _insert_achievements(rows: list[tuple]) -> None:
    for slug, name, description, icon_emoji in rows:
        s = slug.replace("'", "''")
        n = name.replace("'", "''")
        d = description.replace("'", "''")
        e = icon_emoji.replace("'", "''")
        op.execute(
            f"INSERT INTO achievements (id, slug, name, description, icon_emoji, created_at) "
            f"VALUES (gen_random_uuid(), '{s}', '{n}', '{d}', '{e}', now())"
        )


def upgrade() -> None:
    # Cascades to user_achievements via FK ondelete=CASCADE
    op.execute("DELETE FROM achievements")
    _insert_achievements(_NEW_ACHIEVEMENTS)


def downgrade() -> None:
    op.execute("DELETE FROM achievements")
    _insert_achievements(_OLD_ACHIEVEMENTS)
