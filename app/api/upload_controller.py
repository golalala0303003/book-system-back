from fastapi import APIRouter, Depends, UploadFile, File, Form

from app.core.constants import SuccessMsg
from app.schemas.result import Result
from app.service.upload_service import UploadService

router = APIRouter(prefix="/upload", tags=["文件上传模块"])


@router.post("/image")
async def upload_image(
        file: UploadFile = File(...),
        folder: str = Form(default="others", description="OSS存储文件夹分类，例如: avatars, covers"),
        service: UploadService = Depends()
):
    """
    通用图片上传接口
    """
    public_url = await service.upload_image(file=file, folder=folder)
    return Result.success(data=public_url, message=SuccessMsg.IMAGE_UPLOAD_SUCCESS)