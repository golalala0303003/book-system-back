import oss2
from app.core.config import settings
from app.exceptions.file_exceptions import FileUploadException


class OSSClient:
    def __init__(self):
        # 验证
        self.auth = oss2.Auth(settings.ALIYUN_ACCESSKEY_ID, settings.ALIYUN_ACCESSKEY_SECRET)
        # bucket
        self.bucket = oss2.Bucket(
            self.auth,
            settings.ALIYUN_ENDPOINT,
            settings.ALIYUN_BUCKET_NAME
        )

        # 存储相关信息
        self.bucket_name = settings.ALIYUN_BUCKET_NAME
        self.endpoint = settings.ALIYUN_ENDPOINT

    # 上传文件接口
    def upload_file(self, object_name: str, file_data: bytes) -> str:
        try:
            self.bucket.put_object(object_name, file_data)

            # 拼接公共访问 URL
            public_url = f"https://{self.bucket_name}.{self.endpoint}/{object_name}"
            return public_url
        except oss2.exceptions.OssError as e:
            # 原始日志
            print(f"OSS 上传失败, 详细信息: {e}")
            raise FileUploadException()

_oss_client_instance = OSSClient()

def get_oss_client() -> OSSClient:
    return _oss_client_instance