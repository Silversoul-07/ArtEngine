from api.common import *
from api.ml import siglip_model, siglip_processor
from api.routes.images.models import Media

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_user_from_token(token: str=Depends(oauth2_scheme)):
    if token:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[algorithm])
        user_id = payload.get("sub")
        return user_id
    return None

async def generate_url(format: str) -> str:
    if format == "gif":
        return f"gifs/{uuid4().time}.{format}"
    return f"images/{uuid4().time}.{format}"
    
async def hash_image(image: Image) -> str:
    if image.format == 'GIF':
        # Hash the first and last frames of the GIF
        frames = list(ImageSequence.Iterator(image))
        if len(frames) > 1:
            first_frame_hash = await asyncio.to_thread(phash, frames[0].convert("RGB"))
            last_frame_hash = await asyncio.to_thread(phash, frames[-1].convert("RGB"))
            # Combine the hashes (e.g., concatenate)
            combined_hash = f"{first_frame_hash}{last_frame_hash}"
        else:
            frame_hash = await asyncio.to_thread(phash, frames[0].convert("RGB"))
            combined_hash = f"{frame_hash}{frame_hash}"
        return str(combined_hash)
    else:
        image_hash = await asyncio.to_thread(phash, image)
        return str(image_hash)

async def image_from_url(url: str):
    headers = {'User-Agent': UserAgent().random}
    async with aiohttp.ClientSession(headers=headers, connector=TCPConnector(verify_ssl=False)) as session:
        async with session.get(url) as response:
            image_bytes = await response.read()
            return image_bytes
        
async def text2vec(text: str):
    try:
        inputs = siglip_processor(text=[text], return_tensors="pt", padding="max_length", max_length=16, truncation=True)
        with torch.no_grad():
            text_features = siglip_model.get_text_features(**inputs)
        text_embedding = text_features.squeeze().cpu().numpy()        
        text_embedding = text_embedding / np.linalg.norm(text_embedding)    
        return text_embedding
    except Exception as e:
        raise e

async def img2vec(image: Image.Image):
    try:
        inputs = siglip_processor(images=image, return_tensors="pt")
        with torch.no_grad():
            outputs = siglip_model.get_image_features(**inputs)
        image_embedding = outputs.squeeze().cpu().numpy()
        image_embedding = image_embedding / np.linalg.norm(image_embedding)      
        return image_embedding
    except Exception as e:
        raise e

# Function to process images in a directory
async def sync_dir( db: Session, directory: str):
    data_file = os.path.join(directory, 'data.json')

    # Check if the JSON file exists
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"JSON file not found in directory: {directory}")
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"Directory not found: {directory}")

    # Read the JSON file
    with open(data_file, 'r') as json_file:
        image_data_list = json.load(json_file)

    for image_data in image_data_list:
        image_path = os.path.join(directory, image_data['filename'])
        try:
            # posting to endpoint might be better
            existing_image = db.query(Media).filter_by(url=image_data['url']).first()
            if existing_image:
                print(f"Image already exists in the database: {image_data['url']}")
                continue

            with Image.open(image_path) as image:
                image_url = await generate_url(image.format.lower())
                image_hash = await hash_image(image)
                image_embedding = await img2vec(image)

                # use data from credentials.json
                media = Media(
                    url=image_data['url'],
                    title=image_data['title'],
                    desc=image_data['desc'],
                    hash=image_hash,
                    is_nsfw=image_data.get('is_nsfw', False),
                    is_public=image_data.get('is_public', True),
                    user_id=image_data.get('user_id', 'admin'),
                    metadata_=image_data.get('metadata', {}),
                    created_at=datetime.utcnow(),
                    embedding=image_embedding.tolist()
                )
                db.add(media)
                db.commit()
                db.refresh(media)

                destination_folder = 'gifs' if image.format.lower() == 'gif' else 'images'
                destination_path = os.path.join(destination_folder, os.path.basename(image_url))
                shutil.move(image_path, destination_path)
                print(f"Processed and moved image: {image_path} to {destination_path}")

        except Exception as e:
            print(f"Error processing image {image_path}: {e}")
            os.remove(image_path)
            continue
