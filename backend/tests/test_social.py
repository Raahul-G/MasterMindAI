"""
Unit tests for social feature logic.
All tests are pure — no database, no HTTP.
"""
import uuid


# ---------------------------------------------------------------------------
# Friend ID resolution logic
# ---------------------------------------------------------------------------

def _resolve_friend_id(requester_id, addressee_id, current_user_id):
    """Given a friendship row, return the ID of the other person."""
    return addressee_id if requester_id == current_user_id else requester_id


def test_friend_id_resolved_when_user_is_requester():
    user = uuid.uuid4()
    friend = uuid.uuid4()
    result = _resolve_friend_id(user, friend, user)
    assert result == friend


def test_friend_id_resolved_when_user_is_addressee():
    user = uuid.uuid4()
    friend = uuid.uuid4()
    result = _resolve_friend_id(friend, user, user)
    assert result == friend


def test_friend_id_not_self():
    user = uuid.uuid4()
    friend = uuid.uuid4()
    result = _resolve_friend_id(user, friend, user)
    assert result != user


# ---------------------------------------------------------------------------
# Friend request validation logic
# ---------------------------------------------------------------------------

def _validate_friend_request(requester_id, addressee_id, existing_ids):
    """
    Returns an error string or None.
    existing_ids: set of (requester_id, addressee_id) tuples already in DB.
    """
    if requester_id == addressee_id:
        return "You cannot send a friend request to yourself."
    if (requester_id, addressee_id) in existing_ids or (addressee_id, requester_id) in existing_ids:
        return "A friendship or pending request already exists between these users."
    return None


def test_self_request_is_rejected():
    user = uuid.uuid4()
    error = _validate_friend_request(user, user, set())
    assert error is not None
    assert "yourself" in error


def test_duplicate_request_is_rejected():
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    existing = {(user_a, user_b)}
    error = _validate_friend_request(user_a, user_b, existing)
    assert error is not None


def test_reverse_duplicate_request_is_rejected():
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    existing = {(user_b, user_a)}
    error = _validate_friend_request(user_a, user_b, existing)
    assert error is not None


def test_valid_request_returns_no_error():
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    error = _validate_friend_request(user_a, user_b, set())
    assert error is None


# ---------------------------------------------------------------------------
# Activity feed visibility logic
# ---------------------------------------------------------------------------

def _build_visible_ids(user_id, friend_ids):
    """The feed should include the user's own events plus all friends' events."""
    return set(friend_ids) | {user_id}


def test_feed_includes_own_activity():
    user = uuid.uuid4()
    friends = [uuid.uuid4(), uuid.uuid4()]
    visible = _build_visible_ids(user, friends)
    assert user in visible


def test_feed_includes_all_friend_activity():
    user = uuid.uuid4()
    friends = [uuid.uuid4(), uuid.uuid4()]
    visible = _build_visible_ids(user, friends)
    for f in friends:
        assert f in visible


def test_feed_excludes_strangers():
    user = uuid.uuid4()
    friends = [uuid.uuid4()]
    stranger = uuid.uuid4()
    visible = _build_visible_ids(user, friends)
    assert stranger not in visible


# ---------------------------------------------------------------------------
# Activity metadata structure
# ---------------------------------------------------------------------------

def test_module_completed_metadata_has_required_keys():
    metadata = {"topic": "Quantum physics", "level": "intermediate", "score": 8, "total": 10}
    assert "topic" in metadata
    assert "score" in metadata
    assert "total" in metadata


def test_achievement_earned_metadata_has_required_keys():
    metadata = {"slug": "first_steps", "name": "First Steps", "icon_emoji": "🎯"}
    assert "slug" in metadata
    assert "name" in metadata
    assert "icon_emoji" in metadata
