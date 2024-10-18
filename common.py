import json
import os
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
from typing import List, Tuple, Union, Dict, Any
from passlib.context import CryptContext
from fake_useragent import UserAgent
from aiohttp import TCPConnector


from fastapi.security import OAuth2PasswordBearer
import jwt

from sqlalchemy import Column, Integer, String, BigInteger, Boolean, ForeignKey, Text, Index, JSON, Enum, UniqueConstraint, DateTime, func, ARRAY, UUID, Table
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.dialects.postgresql import JSONB

from sklearn.decomposition import PCA
from scipy.spatial.distance import cosine
from scipy.spatial.distance import cdist

from fastapi import Depends, File, UploadFile, Form, APIRouter, HTTPException, Response, Security, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from api.database import SessionLocal, Base, client

# Initialize logger
logger = logging.getLogger(__name__)
SECRET_KEY = os.getenv("SECRET_KEY")
algorithm = "HS256"