import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import engine, get_db
from app.models import Base, Product
from app.storage import ensure_bucket, get_presigned_url, get_s3_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаём таблицы (для MVP; позже заменим на Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        ensure_bucket()
    except Exception as e:
        print(f"MinIO bucket check failed: {e}")
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(503, "Database unavailable")

    try:
        get_s3_client().head_bucket(Bucket=settings.minio_bucket)
    except Exception:
        raise HTTPException(503, "MinIO unavailable")

    return {"status": "ok", "db": "connected", "minio": "connected"}


@app.get("/api/products")
async def list_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).order_by(Product.created_at.desc()))
    products = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "title": p.title,
            # Генерируем временную ссылку на картинку
            "image_url": get_presigned_url(p.image_key),
            "created_at": p.created_at.isoformat(),
        }
        for p in products
    ]


@app.post("/api/products")
async def create_product(
    title: str = Form(...),
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    # 1. Генерируем уникальное имя файла (чтобы не перезаписывать друг друга)
    file_extension = image.filename.split(".")[-1] if "." in image.filename else "jpg"
    image_key = f"{uuid.uuid4()}.{file_extension}"

    # 2. Загружаем файл в MinIO (стримом, без сохранения на диск)
    s3_client = get_s3_client()
    try:
        # upload_fileobj принимает file-like объект (UploadFile.file)
        s3_client.upload_fileobj(
            image.file,
            settings.minio_bucket,
            image_key,
            ExtraArgs={"ContentType": image.content_type},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to S3: {str(e)}")

    # 3. Сохраняем запись в PostgreSQL
    new_product = Product(title=title, image_key=image_key)
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)

    return {
        "id": str(new_product.id),
        "title": new_product.title,
        "image_key": new_product.image_key,
    }
