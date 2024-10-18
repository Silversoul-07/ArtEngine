from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pymilvus import MilvusClient, DataType
import logging

os.makedirs("media/avatar", exist_ok=True)
os.makedirs("media/images", exist_ok=True)
os.makedirs("media/gifs", exist_ok=True)

logger = logging.getLogger(__name__)
database_url = os.getenv("DATABASE_URL")
engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

client = MilvusClient(
    uri=os.getenv("MILVUS_URI"),
)

def create_collection():
    schema = client.create_schema(
        auto_id=False,
        enable_dynamic_field=True,
    )

    schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
    schema.add_field(field_name="embed", datatype=DataType.FLOAT_VECTOR, dim=1152)

    index_params = MilvusClient.prepare_index_params()

    index_params.add_index(
        field_name="embed",
        metric_type="COSINE",
        index_type="IVF_FLAT",
        index_name="vector_index",
        params={ "nlist": 128 }
        )
    
    client.create_collection(
        collection_name="image_embeddings",
        schema=schema,
        index_params=index_params
    )

    client.create_collection(
        collection_name="text_embeddings",
        schema=schema,
        index_params=index_params
    )

# Check if the collection exists
if "image_embeddings" in client.list_collections():
    logger.info("Collection 'embeddings' exists. Loading collection...")
    client.load_collection(collection_name="image_embeddings")
    client.load_collection(collection_name="text_embeddings")
else:
    logger.info("Collection 'embeddings' does not exist. Creating collection...")
    create_collection()