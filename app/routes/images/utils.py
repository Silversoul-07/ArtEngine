from PIL import Image
import hashlib
# import torch
from app.database import SessionLocal
# from transformers import CLIPProcessor, CLIPModel


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_image(img: Image):
    img_hash = hashlib.sha256()
    img_hash.update(img.tobytes())
    return img_hash.hexdigest()

# # Initialize the CLIP model and processor
# model_name = "openai/clip-vit-large-patch14"
# clip_model = CLIPModel.from_pretrained(model_name)
# clip_processor = CLIPProcessor.from_pretrained(model_name)

# # Function to generate text embeddings
# async def generate_text_embedding(text: str):
#     # Tokenize and preprocess the text
#     inputs = clip_processor(text=text, return_tensors="pt", padding=True, truncation=True)
    
#     # Generate text embeddings
#     with torch.no_grad():
#         outputs = clip_model.get_text_features(**inputs)
    
#     # Extract and return the embeddings
#     text_embedding = outputs.squeeze().detach().numpy()
#     print(len(text_embedding))
#     return text_embedding

# # Function to generate image embeddings
# async def generate_image_embedding(image: Image):
#     # Preprocess the image
#     inputs = clip_processor(images=image, return_tensors="pt")
    
#     # Generate image embeddings
#     with torch.no_grad():
#         outputs = clip_model.get_image_features(**inputs)
    
#     # Flatten the embedding
#     image_embedding_flat = outputs.squeeze().detach().numpy()
    
#     return image_embedding_flat

# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import base64
# import os
# from uuid import uuid4
# import time

# options = webdriver.EdgeOptions()
# options.add_argument("headless")
# driver = webdriver.Edge(options=options)
# driver.get("https://runware.ai/")

# def generate_image(prompt):
#     textarea = WebDriverWait(driver, 10).until(
#         EC.presence_of_element_located((By.ID, "heroMessage"))
#     )
#     textarea.clear()
#     textarea.send_keys(prompt)
#     submit_button = driver.find_element(By.ID, "submit-btn-5dt")
#     submit_button.click()
#     time.sleep(5)
#     img_element = driver.find_element(By.CSS_SELECTOR,'#image-container-4rk')

#     img_src = img_element.get_attribute('src')
#     base64_str = img_src.split(',')[1]

#     img_data = base64.b64decode(base64_str)
#     filename = f'{uuid4().time}.webp'
#     dir = os.getenv('STORAGE_DIR')

#     with open(f'{dir}/{filename}', 'wb') as f:
#         f.write(img_data)

#     return filename
