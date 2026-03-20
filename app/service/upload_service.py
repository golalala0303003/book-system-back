import os
import uuid
from fastapi import Depends, UploadFile

from app.core.oss_client import OSSClient, get_oss_client
from app.exceptions.file_exceptions import InvalidFileTypeException, FileTooLargeException

class UploadService:
    def __init__(self, oss_client: OSSClient = Depends(get_oss_client)):
        # 依赖注入OSSClient 单例
        self.oss_client = oss_client

        # 规则配置
        self.MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
        self.ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

    async def upload_image(self, file: UploadFile, folder: str) -> str:
        """
        处理图片上传业务逻辑
        """
        # 校验文件格式
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in self.ALLOWED_IMAGE_EXTS:
            raise InvalidFileTypeException()

        # 读取文件内容到内存
        file_data = await file.read()

        # 校验文件大小
        if len(file_data) > self.MAX_IMAGE_SIZE:
            raise FileTooLargeException()

        # 生成唯一文件名 UUID 防止重名且按文件夹归类
        # 生成的 object_name 例: images/avatars/4f8b9a...123.jpg
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        object_name = f"images/{folder}/{unique_filename}"

        # 调用OSSClient 执行上传
        public_url = self.oss_client.upload_file(object_name, file_data)

        return public_url