from api.common import *
import api.routes.images.schemas as schemas
from api.routes.images.utils import generate_url, hash_image, get_db, text2vec, img2vec, image_from_url, get_user_from_token
from api.routes.images.crud import add_media, get_image, similar_image_search, add_preference, add_view, recommend_media, random_images

router = APIRouter(prefix='/api')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

STORAGE_DIR = os.getenv("STORAGE_DIR", "media")

@router.post("/media", status_code=201, tags=['Media'])
async def create_image(
    db: Session = Depends(get_db),
    url: str = Form(None),
    image: UploadFile = File(None),
    title: str = Form(...),
    desc: str = Form(None),  # Allow desc to be None
    tags: str = Form(None),   # Allow tags to be None
    collections: str = Form(None), # Allow collections to be None
    is_public: bool = Form(True), 
    is_nsfw: bool = Form(False),
    metadata: str = Form(None),
    token: str = Depends(oauth2_scheme)
): 
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        if url:
            contents = await image_from_url(url)
        else:  
            contents = await image.read()    
        fp = Image.open(BytesIO(contents))
        format = fp.format
        if format != 'GIF' and fp.mode != 'RGB':
            fp = fp.convert("RGB")
        url = await generate_url(format.lower())
        mime_type = Image.MIME[format]
        path = os.path.join(STORAGE_DIR, url)
        
        tags = json.loads(tags) if tags else []
        collections = json.loads(collections) if collections else []
        hash = await hash_image(fp)
        metadata:dict = json.loads(metadata) if metadata else {}
        metadata["file_size"] = f"{len(contents) / 1024 / 1024:.2f} MB"
        metadata["dim"] = fp.size
        metadata["mime_type"] = mime_type
        metadata["likes"] = 0
        metadata["dislikes"] = 0
        if mime_type == "image/gif":
            metadata["duration"] = fp.info.get("duration")

        img_embed, text_embed = await asyncio.gather(
            img2vec(fp),
            text2vec(title)
        )

        kwargs = {
            "url": url,
            "title": title,
            "desc": desc or "",
            "hash": hash,
            "is_nsfw": is_nsfw,
            "is_public": is_public,
            "user_id": user_id,
            "metadata_": metadata
        }
        image_id = await add_media(db, **kwargs, tags=tags, collections=collections)
        client.insert("text_embeddings", data={ "id": image_id, "embed": text_embed })
        client.insert("image_embeddings", data={ "id": image_id, "embed": img_embed })
        async with aiofile.async_open(path, "wb") as outfile:
            await outfile.write(contents)
        return {"image_id": image_id}
    
    except Exception as e:
        raise HTTPException(400, e)


@router.get("/media/{id}", response_model=schemas.Image, tags=['Media'])
async def get_dbimage(id: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_from_token)):
    image = await get_image(db, id, user_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Image Not Found")
    return image

@router.post("/like", tags=['Images'])
async def post_like(
    media_id: int = Form(...),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[algorithm])
        user_id: str = payload.get("sub")
        kwargs = {
            "user_id": user_id,
            "media_id": media_id,
            "preference": "like"
        }
        status = await add_preference(db, **kwargs)
        return {"success": status}   
    except Exception as e:
        raise HTTPException(400, e)

@router.get("/random-images", tags=['Images'])
async def get_random_image(limit: int=100, db: Session = Depends(get_db)):
    image = await random_images(db, limit)
    if image is None:
        raise HTTPException(status_code=404, detail="No images found")
    return image

@router.post("/dislike", tags=['Images'])
async def post_dislike(
    media_id: int = Form(...),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):  
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[algorithm])
        user_id: str = payload.get("sub")
        kwargs = {
            "user_id": user_id,
            "media_id": media_id,
            "preference": "dislike"
        }
        status = await add_preference(db, **kwargs)
        return {"success": status}    

    except Exception as e:
        raise HTTPException(400, e)

@router.post("/view", tags=['Images'])
async def post_view(
    token: str = Depends(oauth2_scheme),
    media_id: int = Form(...),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[algorithm])
        user_id: str = payload.get("sub")
        kwargs = {
            "user_id": user_id,
            "media_id": media_id
        }
        status = await add_view(db, **kwargs)
        return {"success": status}   
    
    except Exception as e:
        raise HTTPException(400, e)
    
@router.get("/recommendations", response_model=List[schemas.Image], tags=['Recommendations'])
async def get_recommendations(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[algorithm])
    user_id: str = payload.get("sub")
    recommendations = await recommend_media(db, user_id)
    if not recommendations:
        raise HTTPException(status_code=404, detail="No recommendations found")
    return recommendations


@router.post("/search", response_model=List[schemas.Image], tags=['Search'])
async def query_dbimages(query: str, db: Session = Depends(get_db)):
    ''' future plans: compare with text_embeddings of Image title, description, tags '''
    query_embed = await text2vec(query)
    images = await similar_image_search(db, query_embed)
    return images
    

@router.post("/visual-search", response_model=List[schemas.Image], tags=['Search'])
async def visual_search(id: int = None, image: UploadFile = File(None), db: Session = Depends(get_db)):
    if id is not None:
        image = client.get("image_embeddings", id)
        embed = image[0]["embed"]
    else:
        contents = await image.read()
        with BytesIO(contents) as bio:
            img = Image.open(bio).convert("RGB")
        embed = await img2vec(img)
    
    if embed is None:
        raise HTTPException(status_code=500, detail='Embedding not found')

    similar_images = await similar_image_search(db, embed, 100)
    return similar_images

