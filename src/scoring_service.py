import random
import logging

def get_score(store, phone=None, email=None, birthday=None,
              gender=None, first_name=None, last_name=None):
    score = 0
    cache_key_parts = [
        phone or "",
        email or "",
        f"{birthday.strftime('%Y%m%d')}" if birthday else "",
        str(gender) if gender is not None else "",
        first_name or "",
        last_name or ""
    ]
    cache_key = "uid:" + ":".join(cache_key_parts)

    if store:
        try:
            cached_score = store.cache_get(cache_key)
            if cached_score:
                return float(cached_score)
        except Exception as e:
            logging.error(f"Cache get failed: {str(e)}")


    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender:
        score += 1.5
    if first_name and last_name:
        score += 0.5

    if store:
        try:
            store.cache_set(cache_key, score, 60 * 60)  # cache for 1 hour
        except Exception as e:
            logging.error(f"Cache set failed: {str(e)}")

    return score

def get_interests(store, cid):
    if not store:
        raise ValueError("Store is required for get_interests")

    try:
        interests = store.get(f"i:{cid}")
        if interests:
            return interests.decode().split(",")
    except Exception as e:
        logging.error(f"Failed to get interests from store: {str(e)}")
        raise

    default_interests = ["cars", "pets", "travel", "hi-tech",
                         "sport", "music", "books", "tv",
                         "cinema", "geek", "otus"]
    interests = random.sample(default_interests, 2)

    try:
        store.set(f"i:{cid}", ",".join(interests))
    except Exception as e:
        logging.error(f"Failed to save interests to store: {str(e)}")

    return interests