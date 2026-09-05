import io
from typing import Union
import aioboto3

from app.core.config import settings


class S3Service:
    def __init__(self) -> None:
        self.session = aioboto3.Session()
        self.endpoint_url = settings.MINIO_URL
        self.access_key = settings.MINIO_ROOT_USER
        self.secret_key = settings.MINIO_ROOT_PASSWORD
        self.bucket_name = settings.MINIO_BUCKET_NAME

    def _get_client(self):
        return self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

    async def init_bucket(self) -> None:
        async with self._get_client() as client:
            response = await client.list_buckets()
            buckets = [b["Name"] for b in response.get("Buckets", [])]
            if self.bucket_name not in buckets:
                await client.create_bucket(Bucket=self.bucket_name)

    async def upload_file(
        self,
        file_data: Union[bytes, io.BytesIO],
        object_name: str,
        content_type: str = "image/png",
    ) -> str:
        if isinstance(file_data, bytes):
            file_obj = io.BytesIO(file_data)
        else:
            file_obj = file_data
            file_obj.seek(0)

        async with self._get_client() as client:
            await client.upload_fileobj(
                Fileobj=file_obj,
                Bucket=self.bucket_name,
                Key=object_name,
                ExtraArgs={"ContentType": content_type},
            )
        return object_name

    async def get_file_bytes(self, object_name: str) -> bytes:
        async with self._get_client() as client:
            response = await client.get_object(
                Bucket=self.bucket_name,
                Key=object_name,
            )
            async with response["Body"] as stream:
                return await stream.read()

    async def delete_file(self, object_name: str) -> None:
        async with self._get_client() as client:
            await client.delete_object(
                Bucket=self.bucket_name,
                Key=object_name,
            )


    async def get_presigned_url(
            self, object_name: str, expires_in: int = 900
    ) -> str:
        async with self._get_client() as client:
            url = await client.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": object_name,
                },
                ExpiresIn=expires_in,
            )

            return url.replace(settings.MINIO_URL, settings.MINIO_PUBLIC_URL)


s3_service = S3Service()