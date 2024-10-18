import os
import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from models import Media
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to scrape image URLs
def scrape_image_urls(url: str) -> list:
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    image_urls = [img['src'] for img in soup.find_all('img') if 'src' in img.attrs]
    return image_urls

# Function to download an image
def download_image(url: str, folder: str) -> str:
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        filename = os.path.join(folder, os.path.basename(url))
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        return filename
    else:
        raise Exception(f"Failed to download image: {url}")

# Function to add image metadata to the database
def add_image_to_db(db: Session, url: str, filepath: str):
    media = Media(
        url=url,
        title=os.path.basename(filepath),
        desc='',
        hash='',
        is_nsfw=False,
        is_public=True,
        user_id='admin',
        metadata_={},
        created_at=datetime.utcnow()
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media.id

# Main function to scrape, download, and add images to the database
def scrape_and_add_images(db: Session, scrape_url: str, download_folder: str):
    image_urls = scrape_image_urls(scrape_url)
    for url in image_urls:
        try:
            # Check if the image URL already exists in the database
            existing_image = db.query(Media).filter_by(url=url).first()
            if existing_image:
                logger.info(f"Image already exists in the database: {url}")
                continue

            # Download the image
            filepath = download_image(url, download_folder)
            logger.info(f"Downloaded image: {filepath}")

            # Add image metadata to the database
            add_image_to_db(db, url, filepath)
            logger.info(f"Added image to database: {url}")

        except Exception as e:
            logger.error(f"Error processing image {url}: {e}")
            continue

# Example usage
if __name__ == "__main__":
    from database import SessionLocal

    # Create a new database session
    db: Session = SessionLocal()

    # URL to scrape images from
    scrape_url = 'https://example.com'

    # Folder to download images to
    download_folder = 'public/images'

    # Ensure the download folder exists
    os.makedirs(download_folder, exist_ok=True)

    # Scrape, download, and add images to the database
    scrape_and_add_images(db, scrape_url, download_folder)