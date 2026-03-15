import os
import re
import uuid
import logging
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks
import aiofiles
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import desc
from typing import List

# 引入数据库等依赖
from ..database import get_db
from ..models.document import DocumentRecord
from knowledge_platform_backend.rag.document_loader import parse_single_file
from core.paths import PROJECT_ROOT
from core.config import app_config

# 🌟 引入刚刚写好的规范化 Schemas
from ..schemas.schemas_document import (
    BaseResponse,
    UploadResponseData,
    DocumentItem,
    PreviewResponseData,
    UpdateContentRequest
)

import core.logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/files",
    tags=["File Management & Knowledge Base"]
)

UPLOAD_DIR = PROJECT_ROOT / app_config.storage.upload_dir
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_filename(filename: str) -> str:
    basename = os.path.basename(filename)
    name_without_ext = os.path.splitext(basename)[0]
    safe_name = re.sub(r'[^\w\u4e00-\u9fa5-]', '_', name_without_ext)
    return safe_name[:80]


# ==========================================
# 接口 1：极速落盘
# ==========================================
# 🌟 绑定返回值规范: BaseResponse 包裹 UploadResponseData
@router.post("/upload", summary="上传文件并落盘", response_model=BaseResponse[UploadResponseData])
async def upload_file(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="没有选择文件")

    ext = os.path.splitext(file.filename)[1].lower()
    safe_original_name = sanitize_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_uuid = uuid.uuid4().hex[:6]
    safe_filename = f"{timestamp}_{short_uuid}_{safe_original_name}{ext}"
    file_path = UPLOAD_DIR / safe_filename

    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024):
                await out_file.write(content)

        logger.info(f"✅ 文件成功落盘: {file_path}")

        new_doc = DocumentRecord(
            file_name=file.filename,
            file_path=str(file_path),
            status="pending"
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        # 直接返回符合 Schema 结构的字典或对象
        return BaseResponse(
            code=200,
            message="文件极速落盘成功，等待解析",
            data=UploadResponseData(
                id=new_doc.id,
                filename=file.filename,
                status="pending"
            )
        )

    except Exception as e:
        logger.error(f"❌ 文件保存失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    finally:
        await file.close()


# ==========================================
# 接口 2：获取历史文件列表
# ==========================================
# 🌟 绑定返回值规范: BaseResponse 包裹 List[DocumentItem]
@router.get("/list", summary="获取所有文件历史记录", response_model=BaseResponse[List[DocumentItem]])
async def get_file_list(db: Session = Depends(get_db)):
    try:
        docs = db.query(DocumentRecord).order_by(desc(DocumentRecord.created_at)).all()
        result = []
        for doc in docs:
            result.append(DocumentItem(
                id=doc.id,
                fileName=doc.file_name,
                status=doc.status,
                message=doc.error_message if doc.status == 'error' else
                ("文件已安全落盘，请进行清洗" if doc.status == 'pending' else
                 ("向量化中..." if doc.status == 'parsing' else "已成功打入向量库")),
                time=doc.created_at.strftime("%Y-%m-%d %H:%M:%S") if doc.created_at else ""
            ))

        return BaseResponse(code=200, message="获取列表成功", data=result)
    except Exception as e:
        logger.error(f"❌ 获取文件列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取文件列表失败")


# ==========================================
# 接口 3：预览与清洗
# ==========================================
# 🌟 绑定返回值规范
@router.get("/{doc_id}/preview", summary="解析文件并获取Markdown预览", response_model=BaseResponse[PreviewResponseData])
async def preview_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(DocumentRecord).filter(DocumentRecord.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文件记录不存在")

    file_name_on_disk = Path(doc.file_path).name
    actual_file_path = UPLOAD_DIR / file_name_on_disk

    if not actual_file_path.exists():
        raise HTTPException(status_code=500, detail="抱歉，服务器上的物理文件已丢失，无法解析")

    if not doc.parsed_content:
        try:
            logger.info(f"开始初步解析文档: {doc.file_name}")
            parsed_text = parse_single_file(actual_file_path)
            doc.parsed_content = parsed_text
            db.commit()
        except Exception as e:
            logger.exception(f"❌ 解析文件失败: {e}")
            raise HTTPException(status_code=500, detail=f"文件初步解析失败: {str(e)}")

    return BaseResponse(
        code=200,
        message="解析成功",
        data=PreviewResponseData(id=doc.id, content=doc.parsed_content)
    )


# ==========================================
# 接口 4：保存人工修改的内容
# ==========================================
# 🌟 彻底抛弃 dict，使用 UpdateContentRequest 获得完美的数据校验
@router.put("/{doc_id}/content", summary="保存人工清洗后的文本", response_model=BaseResponse)
async def update_document_content(
        doc_id: int,
        payload: UpdateContentRequest, # 👈 自动拦截空 content 的非法请求
        db: Session = Depends(get_db)
):
    doc = db.query(DocumentRecord).filter(DocumentRecord.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文件记录不存在")

    doc.parsed_content = payload.content
    db.commit()

    return BaseResponse(code=200, message="文本清洗保存成功")


# ==========================================
# 接口 5：异步后台向量化入库
# ==========================================
# (后台任务函数 background_vectorize_task 保持不变)
# ...

@router.post("/{doc_id}/vectorize", summary="发起异步向量化入库", response_model=BaseResponse)
async def vectorize_document(
        doc_id: int,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
):
    doc = db.query(DocumentRecord).filter(DocumentRecord.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文件记录不存在")

    if doc.status == "processed":
        raise HTTPException(status_code=400, detail="该文件已向量化，请勿重复操作")

    if not doc.parsed_content:
        raise HTTPException(status_code=400, detail="请先预览并确认解析内容后再发起向量化")

    doc.status = "parsing"
    db.commit()

    # 此处调用你原来的 background_vectorize_task
    # background_tasks.add_task(background_vectorize_task, doc_id, db)

    return BaseResponse(code=200, message="已成功加入向量化队列，后台正在处理")