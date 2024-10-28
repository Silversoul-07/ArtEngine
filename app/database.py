from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pymilvus import MilvusClient, DataType
from typing import Optional
from dataclasses import dataclass
import asyncio
from numpy import ndarray

@dataclass
class MilvusConfig:
    dimension: int = 1024
    index_type: str = "IVF_FLAT"
    metric_type: str = "COSINE"
    nlist: int = 128
    collection_name: str = "embeddings"

class MilvusSetup:
    def __init__(self, uri: Optional[str] = None):
        self.uri = uri or os.getenv("MILVUS_URI")
        if not self.uri:
            raise ValueError("Milvus URI not provided")
        
        self.client = MilvusClient(uri=self.uri)
        self.config = MilvusConfig()

    def create_schema(self):
        schema = self.client.create_schema(
            auto_id=False,
            enable_dynamic_field=True,
        )
        schema.add_field(field_name="id", datatype=DataType.VARCHAR, max_length=255, is_primary=True)
        schema.add_field(
            field_name="image_embed", 
            datatype=DataType.FLOAT_VECTOR, 
            dim=self.config.dimension
        )
        schema.add_field(
            field_name="text_embed", 
            datatype=DataType.FLOAT_VECTOR, 
            dim=self.config.dimension
        )        
        return schema

    def create_index_params(self):
        index_params = MilvusClient.prepare_index_params()
        
        # Add indices for both vector fields
        for field_name in ["image_embed", "text_embed"]:
            index_params.add_index(
                field_name=field_name,
                metric_type=self.config.metric_type,
                index_type=self.config.index_type,
                index_name=f"{field_name}_index",
                params={"nlist": self.config.nlist}
            )
        
        return index_params

    def create_collection(self):
        try:
            schema = self.create_schema()
            index_params = self.create_index_params()
            
            self.client.create_collection(
                collection_name=self.config.collection_name,
                schema=schema,
                index_params=index_params
            )
            print(f"Collection '{self.config.collection_name}' created successfully")
            self.client.load_collection(self.config.collection_name)
            
        except Exception as e:
            print(f"Failed to create collection: {str(e)}")
            raise

    def setup_collection(self):
        try:
            if self.config.collection_name in self.client.list_collections():
                print(f"Collection '{self.config.collection_name}' exists. Loading...")
                self.client.load_collection(self.config.collection_name)
            else:
                print(f"Creating new collection '{self.config.collection_name}'...")
                self.create_collection()
                
        except Exception as e:
            print(f"Collection setup failed: {str(e)}")
            raise

    async def insert_data(self, id: int, image_embed: list, text_embed: list):
        try:
            data = [{
                    "id": id,
                    "image_embed": image_embed,
                    "text_embed": text_embed
                }]
            await asyncio.to_thread(
                self.client.insert,
                collection_name=self.config.collection_name,
                data=data
            )
            print(f"Data inserted successfully")
        except Exception as e:
            print(f"Failed to insert data: {str(e)}")
            raise

    async def search(self, image_embed: list=None, text_embed: list=None, limit: int = 128) -> dict:
        try:
            if isinstance(image_embed, ndarray):
                embedding = image_embed
                field = "image_embed"
            else:
                embedding = text_embed
                field = "text_embed"

            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 32},  # Increased nprobe for better accuracy
            }

            search_results = await asyncio.to_thread(
                self.client.search,
                collection_name=self.config.collection_name,
                data=[embedding],
                limit=limit,
                search_params=search_params,
                anns_field=field
            )
            mids = []
            identical = []
            for hit in search_results[0]:
                if hit["distance"] < 0.01:  # Threshold for identical images
                    identical.append(hit['id'])
                else:
                    mids.append(hit['id'])
            if mids:
                mids.pop(0)  # pop the first result as it is the query image

            if field == "image_embed":
                return {"similar": mids, "identical": identical}
            
            mids.extend(identical)
            return {"similar": mids}

        except Exception as e:
            print(f"Failed to search data: {str(e)}")
            raise

    async def get_embedding(self, id: int):
        try:
            result = await asyncio.to_thread(
                self.client.get_entity_by_id,
                collection_name=self.config.collection_name,
                ids=[id]
            )
            return result[0]["image_embed"]
        except Exception as e:
            print(f"Failed to get embedding: {str(e)}")
            raise

# Milvus setup
milvus_client = MilvusSetup()
milvus_client.setup_collection()

# Database setup
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("Database URL not provided")

# Create database engine and session
engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

