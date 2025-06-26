import pytest
import redis
from src.store import Store
from src.scoring_service import get_score, get_interests



@pytest.fixture
def redis_store():
    store = Store(host='localhost', port=6379)
    yield store
    store._client.flushdb()


def test_score_caching(redis_store):
    score1 = get_score(redis_store, phone="79175002040", email="test@example.com")

    score2 = get_score(redis_store, phone="79175002040", email="test@example.com")

    assert score1 == score2

def test_interests_storage(redis_store):
    cid = 123
    interests = get_interests(redis_store, cid)

    stored = redis_store.get(f"i:{cid}")
    assert stored is not None
    assert set(stored.decode().split(",")) == set(interests)

def test_score_without_store():
    score = get_score(None, phone="79175002040", email="test@example.com")
    assert score == 3.0

def test_interests_without_store():
    with pytest.raises(ValueError):
        get_interests(None, 123)

def test_store_reconnection(redis_store, mocker):
    mocker.patch.object(redis_store._client, 'get', side_effect=redis.ConnectionError())

    assert redis_store.cache_get("test") is None

    with pytest.raises(redis.ConnectionError):
        redis_store.get("test")