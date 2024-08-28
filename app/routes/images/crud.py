from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import numpy as np
from app.routes.images.models import Images, Embeddings
import app.routes.images.schemas as schemas
from scipy.spatial.distance import cosine
from typing import List
from sqlalchemy.sql import func
from sqlalchemy.exc import IntegrityError

async def create_image(db: Session, url:str, title:str, hash:str, user_id:str):
    try:
        while True:
            new_image = Images(url=url, title=title, hash=hash, user_id=user_id)
            if not db.query(Images).filter_by(id=new_image.id).first():
                break

        db.add(new_image)
        db.commit()
        db.refresh(new_image)
        return new_image
    except IntegrityError as e:
        print("Image already exists")
        return None
    except Exception as e:
        print("Failed to insert image")
        print(f"Exception: {e}")
        return None
    
async def create_embedding(db: Session, image_id:int, embed: List[float]):
    try:
        new_embed = Embeddings(embed=embed, image_id=image_id)
        db.add(new_embed)
        db.commit()
        db.refresh(new_embed)
        return new_embed
    except Exception as e:
        print("Failed to insert embedding")
        print(f"Exception: {e}")
        return None

async def get_image(db:Session, id:int):
    image = db.query(Images).filter(Images.id == id).first()
    return image

async def get_random_images(db: Session, limit: int):
    images = db.query(Images).order_by(func.random()).limit(limit).all()
    return images

async def get_embed_by_id(db:Session, id:int):
    image = db.query(Images).filter(Images.id == id).first()
    return image

async def is_duplicate(db:Session, hash_value):
    # Query to check if the hash already exists
    existing_image = db.query(Images).filter(Images.hash == hash_value).first()
    return existing_image is not None    

async def deleteImage(db: Session, id: int):
    db.query(Images).filter(Images.id == id).delete()
    db.commit()

async def vectorSearch(db: Session, embedding: np.ndarray, top_k: int = 1) -> List[schemas.Image]:
    try:
        # Fetch only necessary columns
        results = db.query(Images.id, Images.url, Images.title, Embeddings.embed)\
            .join(Embeddings, Images.id == Embeddings.image_id)\
            .all()

        if not results:
            return []

        # Ensure embeddings are properly shaped
        embeddings = np.array([np.frombuffer(r[3], dtype=np.float32) for r in results])
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(-1, embedding.shape[0])

        # Calculate cosine similarity for all embeddings
        similarities = 1 - np.apply_along_axis(lambda e: cosine(e, embedding), 1, embeddings)

        # Create a list of tuples with (id, url, title, similarity)
        similarity_results = [(r[0], r[1], r[2], s) for r, s in zip(results, similarities)]

        # Sort results by similarity in descending order and get top_k
        top_results = sorted(similarity_results, key=lambda x: x[3], reverse=True)[:top_k]

        # Convert to schema objects
        return [schemas.Image(id=r[0], url=r[1], title=r[2]) for r in top_results]

    except SQLAlchemyError as e:
        print(f"Failed to query database for embeddings: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []