import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import json
import base64
import random
import coolname
import datetime
from pathlib import Path
import aiohttp
import aiofile
import re
import shutil

import logging
import torch
import numpy as np
from uuid import uuid4
from PIL import Image, ImageSequence
from io import BytesIO
import asyncio
from imagehash import phash
from pgvector.sqlalchemy import Vector
from pydantic import BaseModel
from typing import List, Tuple, Union, Dict, Any, Optional
from passlib.context import CryptContext
from fake_useragent import UserAgent
from aiohttp import TCPConnector
from deepface import DeepFace
from clip_client import Client
from docarray import Document


from fastapi.security import OAuth2PasswordBearer
import jwt

from sqlalchemy import Column, Integer, String, BigInteger, Boolean, ForeignKey, Text, Index, JSON, Enum, UniqueConstraint, DateTime, func, ARRAY, UUID, Table
from sqlalchemy.orm import relationship, backref, joinedload, Session   
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.dialects.postgresql import JSONB

from sklearn.decomposition import PCA
from scipy.spatial.distance import cosine
from scipy.spatial.distance import cdist

from fastapi import Depends, File, UploadFile, Form, APIRouter, HTTPException, Response, Security, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from .database import SessionLocal, Base, milvus_client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token",auto_error=False)

STORAGE_DIR = os.getenv("STORAGE_DIR")
SECRET_KEY = os.getenv("SECRET_KEY")
algorithm = 'HS256'

async def validate_user(token:str = Depends(oauth2_scheme)):
    if not token:
        raise Exception("Token not provided")

    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    uid =  payload.get("sub").get("uid")
    if uid is None:
        raise Exception("Invalid token")
    return uid

async def get_uid(token:str|None = Depends(oauth2_scheme)):
    try:
        if not token:
            return None

        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        uid =  payload.get("sub").get("uid")
        return uid
    except Exception as e:
        return None

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

    
async def encode_image(image:bytes):
    return base64.b64encode(image).decode('utf-8')

clip = Client('grpc://localhost:51000')
