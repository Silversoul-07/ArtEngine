import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from transformers import AutoProcessor, AutoModel

# Initialize the SIGLIP model and processor
model_name = "google/siglip-so400m-patch14-224"
siglip_model = AutoModel.from_pretrained(model_name)
siglip_processor = AutoProcessor.from_pretrained(model_name)