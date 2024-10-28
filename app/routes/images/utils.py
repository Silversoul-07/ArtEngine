from ...common import *
from .crud import add_media


async def generate_url(format: str):
    if format == "gif":
        return f"gifs/{uuid4().time}.{format}"
    return f"images/{uuid4().time}.{format}"
    
async def hash_image(image: Image):
    if image.format == 'GIF':
        frames = list(ImageSequence.Iterator(image))
        if len(frames) > 1:
            first_frame_hash = await asyncio.to_thread(phash, frames[0].convert("RGB"))
            last_frame_hash = await asyncio.to_thread(phash, frames[-1].convert("RGB"))
            combined_hash = f"{first_frame_hash}{last_frame_hash}"
        else:
            frame_hash = await asyncio.to_thread(phash, frames[0].convert("RGB"))
            combined_hash = f"{frame_hash}{frame_hash}"
        return str(combined_hash)
    else:
        image_hash = await asyncio.to_thread(phash, image)
        return str(image_hash)
    
async def save_image(contents: bytes, path: str = None):
    async with aiofile.async_open(path, "wb") as outfile:
            await outfile.write(contents)

async def analyse_image(contents: bytes):
    return 0.5, "#FFFFFF"

async def sync_dir( db: Session, dir: str):
    data = json.loads(open('dir/data.json').read())
    for root, _, files in os.walk(dir):
        for file in files:
            path = os.path.join(root, file)
            if path.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                with open(path, "rb") as f:
                    contents = f.read()
                    fp = Image.open(BytesIO(contents))
                    url = await generate_url(fp.format.lower())
                    hash = await hash_image(fp)
                    tags = await analyse_image(contents)
                    kwargs = {
                        "url": url,
                        "title": data['title'],
                        "desc": data['desc'],
                        "tags": tags,
                        "hash": hash,
                        "uid": data['uid'],
                    }
                    if await detect_nsfw(contents):
                        kwargs["isNSFW"] = True
                    if fp.format == "GIF":
                        kwargs["span"] = fp.info.get("duration") * 1000
                    await add_media(db, 1, **kwargs)
                    path = os.path.join(STORAGE_DIR, url)
                    await save_image(contents, path)
    await asyncio.sleep(6 * 60 * 60)
