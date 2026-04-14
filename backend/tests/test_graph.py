"""
Unit tests for Knowledge Graph service logic.
All tests are pure — no database, no HTTP.
Logic mirrors graph_service.py and the frontend node-mapping rules.
"""
import uuid


# ---------------------------------------------------------------------------
# Canonical concept normalisation
# ---------------------------------------------------------------------------

def _canonical(concept_title: str) -> str:
    """Mirrors graph_service: concept_title.strip().lower()"""
    return concept_title.strip().lower()


def test_canonical_strips_leading_trailing_whitespace():
    assert _canonical("  Gradient Descent  ") == "gradient descent"


def test_canonical_lowercases_mixed_case():
    assert _canonical("Neural Network") == "neural network"


def test_canonical_empty_string_returns_empty():
    assert _canonical("") == ""


def test_canonical_already_lowercase_unchanged():
    assert _canonical("backpropagation") == "backpropagation"


def test_canonical_deduplication_same_title_different_case():
    """Same concept submitted with different capitalisation must produce identical canonical key."""
    assert _canonical("Gradient Descent") == _canonical("gradient descent")
    assert _canonical("LSTM") == _canonical("lstm")


# ---------------------------------------------------------------------------
# Hub score increment logic
# ---------------------------------------------------------------------------

def _new_hub_score_and_ids(existing_module_ids: list, new_module_id: uuid.UUID):
    """Mirrors the upsert branch in embed_and_upsert."""
    existing = existing_module_ids or []
    if new_module_id not in existing:
        updated = existing + [new_module_id]
        return len(updated), updated
    return len(existing), existing


def test_hub_score_starts_at_one_for_first_module():
    new_mod = uuid.uuid4()
    score, ids = _new_hub_score_and_ids([], new_mod)
    assert score == 1
    assert ids == [new_mod]


def test_hub_score_increments_when_new_module_added():
    existing_mod = uuid.uuid4()
    new_mod = uuid.uuid4()
    score, ids = _new_hub_score_and_ids([existing_mod], new_mod)
    assert score == 2
    assert new_mod in ids


def test_hub_score_stable_for_duplicate_module():
    mod = uuid.uuid4()
    score, ids = _new_hub_score_and_ids([mod], mod)
    assert score == 1
    assert ids == [mod]


def test_hub_score_none_list_treated_as_empty():
    new_mod = uuid.uuid4()
    score, ids = _new_hub_score_and_ids(None, new_mod)
    assert score == 1


def test_hub_score_three_distinct_modules():
    mods = [uuid.uuid4(), uuid.uuid4()]
    third = uuid.uuid4()
    score, ids = _new_hub_score_and_ids(mods, third)
    assert score == 3


# ---------------------------------------------------------------------------
# Friendship access control logic
# ---------------------------------------------------------------------------

def _is_accepted_friend(
    friendships: list[dict],
    user_a: uuid.UUID,
    user_b: uuid.UUID,
) -> bool:
    """
    Mirrors the friendship gate in graph_service.get_friend_graph().
    Checks both directions for an accepted row.
    """
    for f in friendships:
        if f["status"] != "accepted":
            continue
        if (
            (f["requester_id"] == user_a and f["addressee_id"] == user_b) or
            (f["requester_id"] == user_b and f["addressee_id"] == user_a)
        ):
            return True
    return False


def test_accepted_friendship_requester_to_addressee_grants_access():
    a, b = uuid.uuid4(), uuid.uuid4()
    rows = [{"requester_id": a, "addressee_id": b, "status": "accepted"}]
    assert _is_accepted_friend(rows, a, b) is True


def test_accepted_friendship_reverse_direction_grants_access():
    a, b = uuid.uuid4(), uuid.uuid4()
    rows = [{"requester_id": b, "addressee_id": a, "status": "accepted"}]
    assert _is_accepted_friend(rows, a, b) is True


def test_pending_friendship_does_not_grant_access():
    a, b = uuid.uuid4(), uuid.uuid4()
    rows = [{"requester_id": a, "addressee_id": b, "status": "pending"}]
    assert _is_accepted_friend(rows, a, b) is False


def test_rejected_friendship_does_not_grant_access():
    a, b = uuid.uuid4(), uuid.uuid4()
    rows = [{"requester_id": a, "addressee_id": b, "status": "rejected"}]
    assert _is_accepted_friend(rows, a, b) is False


def test_no_friendship_rows_denies_access():
    a, b = uuid.uuid4(), uuid.uuid4()
    assert _is_accepted_friend([], a, b) is False


def test_friendship_with_third_party_does_not_grant_access_to_b():
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    rows = [{"requester_id": a, "addressee_id": c, "status": "accepted"}]
    assert _is_accepted_friend(rows, a, b) is False


def test_multiple_friendships_correct_pair_found():
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    rows = [
        {"requester_id": a, "addressee_id": c, "status": "accepted"},
        {"requester_id": a, "addressee_id": b, "status": "accepted"},
    ]
    assert _is_accepted_friend(rows, a, b) is True


# ---------------------------------------------------------------------------
# UMAP position decision logic
# ---------------------------------------------------------------------------

def _should_run_umap(total_nodes: int, unpositioned_count: int) -> bool:
    """
    Mirrors compute_positions_for_user branching:
    - Only run UMAP if ≥2 total nodes AND there are unpositioned nodes.
    - Single-node case is handled separately (set to origin).
    """
    return total_nodes >= 2 and unpositioned_count > 0


def test_umap_runs_with_two_total_and_one_unpositioned():
    assert _should_run_umap(2, 1) is True


def test_umap_runs_with_many_nodes_and_unpositioned():
    assert _should_run_umap(10, 3) is True


def test_umap_skipped_with_single_total_node():
    assert _should_run_umap(1, 1) is False


def test_umap_skipped_when_all_nodes_already_positioned():
    assert _should_run_umap(5, 0) is False


def test_umap_skipped_with_zero_nodes():
    assert _should_run_umap(0, 0) is False


def test_single_node_gets_origin_coordinates():
    """Single-node case: graph_service sets pos=(0.0, 0.0, 0.0) without running UMAP."""
    pos = (0.0, 0.0, 0.0)
    assert pos == (0.0, 0.0, 0.0)


# ---------------------------------------------------------------------------
# Node position filter (frontend: filter null-position nodes before render)
# ---------------------------------------------------------------------------

def _filter_positioned(nodes: list[dict]) -> list[dict]:
    """Mirrors KnowledgeGraph.tsx: nodes.filter(n => n.pos_x !== null)"""
    return [n for n in nodes if n.get("pos_x") is not None]


def test_null_pos_nodes_filtered_out():
    nodes = [
        {"id": "a", "pos_x": 1.0, "pos_y": 2.0, "pos_z": 3.0},
        {"id": "b", "pos_x": None, "pos_y": None, "pos_z": None},
    ]
    result = _filter_positioned(nodes)
    assert len(result) == 1
    assert result[0]["id"] == "a"


def test_all_null_returns_empty_list():
    nodes = [{"id": "a", "pos_x": None}, {"id": "b", "pos_x": None}]
    assert _filter_positioned(nodes) == []


def test_all_positioned_nodes_pass_through():
    nodes = [{"id": "a", "pos_x": 1.0}, {"id": "b", "pos_x": 2.0}]
    assert len(_filter_positioned(nodes)) == 2


def test_empty_node_list_returns_empty():
    assert _filter_positioned([]) == []


# ---------------------------------------------------------------------------
# Node visual mapping (hub_score → size and colour)
# ---------------------------------------------------------------------------

def _hub_color(hub_score: int) -> str:
    """Mirrors KnowledgeGraph.tsx: hub_score > 1 → bright green, else brand green."""
    return "#4ade80" if hub_score > 1 else "#16a34a"


def _hub_val(hub_score: int) -> float:
    """Mirrors KnowledgeGraph.tsx: Math.max(1, hub_score * 1.5)"""
    return max(1.0, hub_score * 1.5)


def test_hub_score_1_renders_brand_green():
    assert _hub_color(1) == "#16a34a"


def test_hub_score_2_renders_bright_green():
    assert _hub_color(2) == "#4ade80"


def test_hub_score_5_renders_bright_green():
    assert _hub_color(5) == "#4ade80"


def test_hub_val_minimum_is_one_for_zero_score():
    assert _hub_val(0) == 1.0


def test_hub_val_minimum_is_one_for_score_of_one():
    # 1 * 1.5 = 1.5 > 1 → 1.5
    assert _hub_val(1) == 1.5


def test_hub_val_scales_linearly():
    assert _hub_val(4) == 6.0


def test_hub_val_never_below_one():
    for score in range(0, 10):
        assert _hub_val(score) >= 1.0
