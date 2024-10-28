from ...common import *
from .models import Media, Tags, MediaTags, CollectionTags, Collections, CollectionMedia, Preferences, Activity, CollectionAccessList, CollectionAccessRequest
from ..users.models import Users

async def add_tags(db: Session, tags: list):
    tids = []
    for tag in tags:
        new_tag = Tags(name=tag)
        db.add(new_tag)
        tids.append(new_tag.tid)
    db.commit()
    return tids

async def add_collection(db: Session, **kwargs) -> int:
    user_id = kwargs.get('uid')
    tags_data = kwargs.pop('tags', [])
    user = db.query(Users).filter(Users.uid == user_id).first()
    
    if not user:
        raise ValueError("User not found.")

    collection = Collections(**kwargs)

    for tag_name in tags_data:
        tag = db.query(Tags).filter(Tags.name == tag_name).first()
        if not tag:
            tag = Tags(name=tag_name)
            db.add(tag) 
        collection.tags.append(tag)  
    user.collections.append(collection)
    
    db.add(collection)
    db.commit()
    db.refresh(collection)

    return collection.cid


async def get_collection_images(db: Session, cid: int, uid: int = None):
    collection = db.query(Collections).filter(Collections.cid == cid).options(
        joinedload(Collections.access_list)
    ).first()

    if not collection:
        return []

    priviledged = any([access.uid == uid for access in collection.access_list])
    if collection.scope == 'private' and not priviledged:
        return []

    images = db.query(CollectionMedia).filter(CollectionMedia.cid == cid).options(
        joinedload(CollectionMedia.media).options(joinedload(Media.tags), joinedload(Media.collections))
    ).all()

    return images

async def grant_access(db:Session, cid:int, uids:list):
    for uid in uids:
        # Check if user already has access
        isgranted =  db.query(CollectionAccessList).filter(CollectionAccessList.cid == cid, CollectionAccessList.uid == uid).first()
        if not isgranted:
            new_access = CollectionAccessList(cid=cid, uid=uid)
            db.add(new_access)
            # delete request
            db.query(CollectionAccessRequest).filter(CollectionAccessRequest.cid == cid, CollectionAccessRequest.uid == uid).delete()
    db.commit()

async def request_access(db:Session, cid:int, uid:str):
    new_request = CollectionAccessRequest(cid=cid, uid=uid)
    db.add(new_request)
    db.commit()

async def get_collection_info(db: Session, cid: int):
    collection = db.query(Collections).filter(Collections.cid == cid).first()
    if not collection:
        return None
    
    return collection

async def get_collections(db:Session) -> list:
    collections = db.query(Collections).options(
        joinedload(Collections.tags),
        joinedload(Collections.media)
    ).all()

    # return only public collections
    return [collection for collection in collections if collection.scope == 'public']

async def get_collections_by_user(db:Session, uid:str) -> list:
    collections = db.query(Collections).filter(Collections.uid == uid).options(
        joinedload(Collections.tags),
        joinedload(Collections.media)
    ).all()
    return [collection for collection in collections if collection.scope == 'public']

async def get_images(db: Session, mid: int, uid: str = None):
    # Fetch the media with its collections and tags
    image = db.query(Media).options(
        joinedload(Media.collections),
        joinedload(Media.tags)
    ).filter(Media.mid == mid).first()
    
    if image is None:
        return None

    # Check if the requesting user is the owner
    if uid != image.uid:
        # If not the owner, filter for public collections only
        image.collections = [col for col in image.collections if col.scope == 'public']
    
    # Return the image if it has collections or if the requester is the owner
    return image if image.collections or uid == image.uid else []

async def add_media(db: Session, **kwargs) -> int:
    user_id = kwargs.get('uid')
    tags_data = kwargs.pop('tags', [])
    collections_data = kwargs.pop('collections', [])

    user = db.query(Users).filter(Users.uid == user_id).first()
    if not user:
        raise ValueError("User not found.")
    
    media = Media(**kwargs)

    for tag_name in tags_data:
        tag = db.query(Tags).filter(Tags.name == tag_name).first()
        if not tag:
            raise Exception("Tag not found.")
        media.tags.append(tag)  # Use relationship to add tag to media

    for collection_data in collections_data:
        collection = db.query(Collections).filter(Collections.name == collection_data).options(
            joinedload(Collections.access_list.and_(CollectionAccessList.uid == user_id))
        ).first()
        if not collection:
            raise Exception("Collection not found.")
        if collection.scope == 'private' and not any([access.uid == user_id for access in collection.access_list]):
            raise Exception("User does not have access to this collection.")
        
        media.collections.append(collection)  # Use relationship to add collection to media

    user.media.append(media)  # Attach media to user

    db.add(media)
    db.commit()
    db.refresh(media)
    
    return media.mid

async def get_images(db:Session):
    images = db.query(Media).options(
        joinedload(Media.tags),
        joinedload(Media.collections.and_(Collections.scope == 'public'))
    ).all()
    return images


async def add_preference(db:Session, uid:str, mid:int, attr:str):
    new_preference = Preferences(uid=uid, mid=mid, attr=attr)
    db.add(new_preference)
    db.commit()

async def add_view(db:Session, uid:str, mid:int):
    new_view = Activity(uid=uid, mid=mid)
    db.add(new_view)
    db.commit()

async def is_duplicate_image(db:Session, hash:str):
    return db.query(Media).filter(Media.hash == hash).first()

async def update_tags_from_list(db)-> None:
    print("Task 0 started")
    return
    while True:
        try:
            tags = open('app/config/tags.txt').read().splitlines()
            tags = list(set(tags))
            await create_tags(db, tags)
            open('app/config/tags.txt', 'w').write('')
        except Exception as e:
            print(e)
        await asyncio.sleep(6 * 60 * 60)  # Sleep for 6 hours

async def classify_image(db:Session, image:bytes) -> list[str]:
    tags = await get_tags(db)
    r = await clip.arank([
            Document(
                blob=image,
                matches=[Document(text=tag.name) for tag in tags],
            )])

    results = [match.text for match in r[0].matches] #if match.scores['clip_score'].value > 0.5]
    return results[:7]

    
async def get_image_by_mid(db: Session, mid: str, uid: str = None):
    image = db.query(Media).options(
        joinedload(Media.tags),
        joinedload(Media.collections)
    ).filter(Media.mid == mid).first()

    if image is None:
        return None

    if uid != image.uid:
        image.collections = [col for col in image.collections if col.scope == 'public']

    return image if image.collections or uid == image.uid else []

# def get_user_preferences(db: Session, user_id: str):
#     return db.query(UserPreferences).filter(UserPreferences.user_id == user_id).all()

# Filter unseen media by recent 'created_at' to reduce processing load
# async def get_recent_unseen_media(db: Session, user_id: str, days_limit: int = 30):
#     viewed_media_ids = db.query(UserViewedMedia.media_id).filter(UserViewedMedia.user_id == user_id).subquery()
#     time_limit = datetime.datetime.now() - datetime.timedelta(days=days_limit)
#     return db.query(Media).filter(~Media.id.in_(viewed_media_ids), Media.created_at > time_limit).all()

# Fetch embeddings in batches to avoid overload
# async def get_media_embeddings(media_ids, batch_size=1000):
#     embeddings = {}
#     for i in range(0, len(media_ids), batch_size):
#         batch_ids = media_ids[i:i+batch_size]
#         results = client.get("embeddings", ids=batch_ids)
#         embeddings.update({result["id"]: result["embed"] for result in results})
#     return embeddings

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


# async def get_user_preferences(session: Session, user_id: str):
#     preferences = session.query(UserPreferences).filter_by(user_id=user_id).all()
#     likes = [p.image_id for p in preferences if p.like]
#     dislikes = [p.image_id for p in preferences if p.dislike]
#     return likes, dislikes


# async def get_user_activity(session: Session, user_id: str):
#     viewed_images = session.query(UserViewedMedia).filter_by(user_id=user_id).all()
#     return [vi.image_id for vi in viewed_images]

# async def get_recommendations(session: Session, user_id: str, top_k=10):
#     # Get user preferences
#     likes, dislikes = await get_user_preferences(session, user_id)
#     user_activity = await get_user_activity(session, user_id)
#     # Get all images
#     all_images = session.query(Media).limit(1000).all()
#     # Filter out images that the user has already seen
#     unseen_images = [image for image in all_images if image.id not in user_activity]
#     # Filter out images that the user has already liked or disliked
#     filtered_images = [image for image in unseen_images if image.id not in likes and image.id not in dislikes]
#     # Get embeddings for filtered images
#     image_embeddings = [image.embedding for image in filtered_images]
#     # Search for similar images
#     recommendations = []
#     for embed in image_embeddings:
#         results = await vector_search(session, embed, top_k=top_k)
#         recommendations.extend(results)
#     return recommendations

async def get_tags(session: Session):
    tags = session.query(Tags).all()
    return tags