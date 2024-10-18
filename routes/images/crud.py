from api.common import *
from api.routes.images.models import Media, Tag, MediaTags, UserCollection, CollectionMedia, UserPreferences, UserViewedMedia

async def add_media(db: Session, url: str, title: str, desc: str, hash: str, is_nsfw: bool, is_public: bool, user_id: str, metadata_: dict, tags: list, collections: list):
    try:
        # Insert Media
        media = Media(
            url=url,
            title=title,
            desc=desc,
            hash=hash,
            is_nsfw=is_nsfw,
            is_public=is_public,
            user_id=user_id,
            metadata_=metadata_,
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.add(media)
        db.commit()
        db.refresh(media)

        # Insert Tags and MediaTags
        for tag_name in tags:
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                db.commit()
                db.refresh(tag)
            media_tag = MediaTags(media_id=media.id, tag_id=tag.id)
            db.add(media_tag)

        # Insert Collections and CollectionMedia
        for collection_name in collections:
            collection = db.query(UserCollection).filter(UserCollection.name == collection_name, UserCollection.user_id == user_id).first()
            if not collection:
                collection = UserCollection(name=collection_name, user_id=user_id)
                db.add(collection)
                db.commit()
                db.refresh(collection)
            collection_media = CollectionMedia(collection_id=collection.id, media_id=media.id)
            db.add(collection_media)

        db.commit()
        return media.id
    except IntegrityError as e:
        db.rollback()
        raise e

    
async def add_preference(db:Session, **kwargs) -> int:
    try:
        new_preference = UserPreferences(**kwargs)
        db.add(new_preference)
        db.commit()
        return True
    except Exception as e:
        print(e)
        return False

async def add_view(db:Session, **kwargs) -> int:
    try:
        new_view = UserViewedMedia(**kwargs)
        db.add(new_view)
        db.commit()
        return True
    except Exception as e:
        print(e)
        return False
    
async def get_image(db: Session, id: int, user_id: str = None):
    image = db.query(Media).filter(Media.id == id).first()
    
    if image is None:
        return None
    
    if image.is_public or image.user_id == user_id:
        # Join collections and tags
        collections = db.query(UserCollection).join(CollectionMedia).filter(CollectionMedia.media_id == id).all()
        tags = db.query(Tag).join(MediaTags).filter(MediaTags.media_id == id).all()
        image.collections = collections
        image.tags = tags
        
        return image
    
    return None




def get_user_preferences(db: Session, user_id: str):
    return db.query(UserPreferences).filter(UserPreferences.user_id == user_id).all()

# Filter unseen media by recent 'created_at' to reduce processing load
async def get_recent_unseen_media(db: Session, user_id: str, days_limit: int = 30):
    viewed_media_ids = db.query(UserViewedMedia.media_id).filter(UserViewedMedia.user_id == user_id).subquery()
    time_limit = datetime.datetime.now() - datetime.timedelta(days=days_limit)
    return db.query(Media).filter(~Media.id.in_(viewed_media_ids), Media.created_at > time_limit).all()

# Fetch embeddings in batches to avoid overload
async def get_media_embeddings(media_ids, batch_size=1000):
    embeddings = {}
    for i in range(0, len(media_ids), batch_size):
        batch_ids = media_ids[i:i+batch_size]
        results = client.get("embeddings", ids=batch_ids)
        embeddings.update({result["id"]: result["embed"] for result in results})
    return embeddings

async def recommend_media(db: Session, user_id: str, days_limit: int = 30):
    # Retrieve user preferences
    preferences = get_user_preferences(db, user_id)
    liked_media_ids = [pref.media_id for pref in preferences if pref.preference == 'like']
    disliked_media_ids = [pref.media_id for pref in preferences if pref.preference == 'dislike']

    # Get unseen media filtered by created_at (last 30 days by default)
    unseen_media = get_recent_unseen_media(db, user_id, days_limit)
    unseen_media_ids = [media.id for media in unseen_media]

    # Fetch embeddings in optimized batches
    liked_embeddings = get_media_embeddings(liked_media_ids) if liked_media_ids else {}
    disliked_embeddings = get_media_embeddings(disliked_media_ids) if disliked_media_ids else {}
    unseen_embeddings = get_media_embeddings(unseen_media_ids)

    recommendations = []
    for media_id, embedding in unseen_embeddings.items():
        like_similarity = np.mean([np.dot(embedding, liked_embeddings[liked_id]) for liked_id in liked_media_ids]) if liked_media_ids else 0
        dislike_similarity = np.mean([np.dot(embedding, disliked_embeddings[disliked_id]) for disliked_id in disliked_media_ids]) if disliked_media_ids else 0
        
        # Final score: similarity to liked media minus similarity to disliked media
        final_score = like_similarity - dislike_similarity
        recommendations.append((media_id, final_score))

    # Sort recommendations by final score
    recommendations.sort(key=lambda x: x[1], reverse=True)
    recommended_media_ids = [media_id for media_id, _ in recommendations]
    return db.query(Media).filter(Media.id.in_(recommended_media_ids)).all()

async def random_images(db:Session, limit=10):
    images = db.query(Media).order_by(func.random()).limit(limit).all()
    return images

async def similar_image_search(db:Session, embed, top_k=100):
    # Search for similar images
    search_params = {
        "metric_type": "COSINE",
        "params": {"nprobe": 16},
    }
    search_results = client.search(
        collection_name="image_embeddings",
        data=[embed],
        limit=top_k,
        search_params=search_params,
    )
    results = []
    for hit in search_results[0]:
        image = await get_image(db, hit['id'])
        results.append(image)
    # pop the first result as it is the query image
    results.pop(0)
    return results

async def get_user_preferences(session: Session, user_id: str):
    preferences = session.query(UserPreferences).filter_by(user_id=user_id).all()
    likes = [p.image_id for p in preferences if p.like]
    dislikes = [p.image_id for p in preferences if p.dislike]
    return likes, dislikes


async def get_user_activity(session: Session, user_id: str):
    viewed_images = session.query(UserViewedMedia).filter_by(user_id=user_id).all()
    return [vi.image_id for vi in viewed_images]

async def get_recommendations(session: Session, user_id: str, top_k=10):
    # Get user preferences
    likes, dislikes = await get_user_preferences(session, user_id)
    user_activity = await get_user_activity(session, user_id)
    # Get all images
    all_images = session.query(Media).limit(1000).all()
    # Filter out images that the user has already seen
    unseen_images = [image for image in all_images if image.id not in user_activity]
    # Filter out images that the user has already liked or disliked
    filtered_images = [image for image in unseen_images if image.id not in likes and image.id not in dislikes]
    # Get embeddings for filtered images
    image_embeddings = [image.embedding for image in filtered_images]
    # Search for similar images
    recommendations = []
    for embed in image_embeddings:
        results = await vector_search(session, embed, top_k=top_k)
        recommendations.extend(results)
    return recommendations