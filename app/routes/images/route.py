from ...common import *
from . import schemas
from .utils import generate_url, hash_image, get_db, save_image, analyse_image
from .crud import add_media, get_image_by_mid, add_preference, add_view, recommend_media, get_tags, is_duplicate_image, add_tags, classify_image, add_collection, get_collection_images, get_collections, get_collections_by_user, grant_access, request_access, get_collection_info, get_images

router = APIRouter(prefix='/api')

# Media Route
@router.post("/upload", status_code=201, tags=['Media'])
async def create_image(
    db: Session = Depends(get_db),
    image: UploadFile = File(...),
    title: str = Form(...),
    desc: str = Form(None),
    tags: str = Form(None),
    src: str = Form(None),
    collections: str = Form(...),
    is_nsfw: bool = Form(False),
    uid: str = Depends(validate_user)
): 
    try:
        contents = await image.read()
        fp = Image.open(BytesIO(contents))
        
        # Run independent operations concurrently
        url, hash, encoded = await asyncio.gather(
            generate_url(fp.format.lower()),
            hash_image(fp),
            encode_image(contents)
        )
        
        # Check for duplicate early
        if await is_duplicate_image(db, hash):
            raise HTTPException(status_code=400, detail="Duplicate Image")

        # Process collections
        collections = [name.strip() for name in collections.split(',')]
        
        # Process tags and get embeddings concurrently
        tags = tags.split(',') if tags else await classify_image(db, contents)
        text_input = title + (desc or "") + ' '.join(tags)
        
        embedding_tasks = asyncio.gather(
            clip.aencode([encoded, text_input]),
            analyse_image(contents)
        )
        
        # Prepare kwargs while waiting for embeddings
        kwargs = {
            "url": url,
            "title": title,
            "desc": desc,
            "hash": hash,
            "tags": tags,
            "collections": collections,
            "uid": uid,
        }
        
        if is_nsfw:
            kwargs["isNSFW"] = is_nsfw
        if fp.format == "GIF":
            kwargs["span"] = fp.info.get("duration") * 1000
        if src:
            kwargs["src"] = src

        # Get results from embedding tasks
        (img_embed, text_embed), (score, color) = await embedding_tasks
        kwargs.update({"score": score, "color": color})

        # Database operations
        mid = await add_media(db, **kwargs)
        
        # Run storage operations concurrently
        await asyncio.gather(
            milvus_client.insert_data(mid, img_embed, text_embed),
            save_image(contents, os.path.join(STORAGE_DIR, url))
        )
        
        return {"message": "Upload successful", "media_id": mid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/media", tags=['Media'])
async def list_dbimages(db: Session = Depends(get_db)):
    images = await get_images(db)
    return images

@router.get("/media/{mid}", tags=['Media'])
async def get_dbimage(
    mid: str, 
    uid: str = Depends(get_uid), 
    db: Session = Depends(get_db)
):
    image = await get_image_by_mid(db, mid, uid)
    if image is None:
        raise HTTPException(status_code=404, detail="Image Not Found")
    return image

@router.post("/preference", tags=['Media'])
async def post_preference(
    mid: int = Form(...),
    attr: str = Form(...),
    uid: str = Depends(validate_user),
    db: Session = Depends(get_db)
):
    if attr not in ["like", "dislike"]:
        raise HTTPException(400, "Invalid preference value")
    
    try:
        await add_preference(db, uid, mid, attr)
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/view", tags=['Media'])
async def post_view(
    mid: int = Form(...),
    uid: str = Depends(validate_user),
    db: Session = Depends(get_db)
):
    try:
        await add_view(db, uid, mid)
    except Exception as e:
        raise HTTPException(400, e)
    
# Search and Recommendations Route
@router.get("/recommend", response_model=List[schemas.Image], tags=['Recommendations'])
async def get_recommendations(db: Session = Depends(get_db), uid: str = Depends(validate_user)):
    try:
        results = await recommend_media(db, uid)
        if not results:
            raise Exception("No recommendations found")
        return results
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/search", tags=['Search'])
async def query_dbimages(query: str, db: Session = Depends(get_db), uid: str = Depends(get_uid)):
    ''' future plans: compare with text_embeddings of Image title, description, tags '''
    query_embed = await clip.aencode([query])
    result = await milvus_client.search(text_embed=query_embed[0])
    return [await get_image_by_mid(db, mid, uid) for mid in result['similar']]
    
@router.post("/visual-search", tags=['Search'])
async def visual_search(image: UploadFile|int = File(None), db: Session = Depends(get_db), uid: str = Depends(get_uid)):
    try:
        if isinstance(image, int):
            mid = image
            image = await get_image_by_mid(db, mid)
            if image is None:
                raise Exception("Image not found")
            image_embed = await milvus_client.get_embedding(mid) # do it
        else:
            contents = await image.read()
            encoded = await encode_image(contents)
            image_embed = await clip.aencode([encoded])
        result = await milvus_client.search(image_embed=image_embed[0])
        result['identical'] = [await get_image_by_mid(db, mid, uid) for mid in result['identical']]
        result['similar'] = [await get_image_by_mid(db, mid, uid) for mid in result['similar']]
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

# Tags Route
@router.get("/tags", response_model=List[schemas.Tags], tags=['tags'])
async def list_tags(db: Session = Depends(get_db)):
    # future plan send tags with count
    tags = await get_tags(db)
    return tags

@router.post("/tags" , tags=['tags'])
async def add_new_tags(tags: str, db: Session = Depends(get_db)):
    try:
        if '[' in tags or ']' in tags:
            raise Exception("Invalid tags")
        tags = [tname.strip() for tname in tags.split(',')]
        await add_tags(db, tags)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/classify", tags=['tags'], response_model=dict)
async def get_classifications(image: UploadFile = File(...), db: Session = Depends(get_db)):
    contents = await image.read()
    tags = await classify_image(db, contents)
    return {"tags": tags}


# Collections Route
@router.get("/collections", tags=['Collections'])
async def get_all_collections(user_id:str|None=None, db: Session = Depends(get_db)):
    ''' future plan: add pagination and ranking'''
    if user_id is None:
        collections = await get_collections(db)
    else:
        collections = await get_collections_by_user(db, user_id)
    return collections

@router.get("/collections/{cid}", tags=['Collections'])
async def get_collection(cid: int, db: Session = Depends(get_db), uid: str = Depends(get_uid)):
    collection = await get_collection_images(db, cid)
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection Not Found")
    return collection

@router.post("/collection_access", tags=['Collections'])
async def add_collection_access(
    cid: int = Form(...),
    uids: str = Form(...),
    auth_uid: str = Depends(validate_user), #arthur
    db: Session = Depends(get_db)
):
    try:
        collection_info = await get_collection_info(db, cid)
        if collection_info is None:
            raise Exception("Collection not found")
        if collection_info.uid != auth_uid:
            raise Exception("Unauthorized")
        if any(uid == auth_uid for uid in uids):
            raise Exception("Cannot grant access to owner")
        uids = [uid.strip() for uid in uids.split(',')]
        await grant_access(db, cid, uids)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/collection_request", tags=['Collections'])
async def request_collection_access(
    cid: int = Form(...),
    uid: str = Depends(validate_user),
    db: Session = Depends(get_db)
):
    try:
        collection_info = await get_collection_info(db, cid)
        if collection_info is None:
            raise Exception("Collection not found")
        if collection_info.uid == uid:
            raise Exception("Cannot request access to owned collection")
        await request_access(db, cid, uid)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/collections", tags=['Collections'])
async def create_collection(
    name: str = Form(...),
    desc: str = Form(...),
    tags: str = Form(...),
    scope: str = Form(None),
    uid: str = Depends(validate_user),
    db: Session = Depends(get_db)
):
    try:
        tags = [tag.strip() for tag in tags.split(',')]
        kwargs = {
            "name": name,
            "desc": desc,
            "tags": tags,
            "uid": uid,
        }
        if scope:
            kwargs["scope"] = scope
        await add_collection(db, **kwargs)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
