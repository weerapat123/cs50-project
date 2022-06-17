import boto3


class AWSService:
    bucket = "monkey-market-bucket"

    def __init__(self):
        self.s3 = boto3.client("s3")

    def download_file(self, source, destination) -> None:
        """For `download_file`
        `source` is aws <key>
        `destination` is local path
        """
        self.s3.download_file(
            Bucket=self.bucket,
            Key=source,
            Filename=destination,
        )

    def upload_file(self, source, destination):
        """For `upload_file`
        `source` is local path
        `destination` is aws <key>
        """
        self.s3.upload_file(
            Filename=source,
            Bucket=self.bucket,
            Key=destination,
        )
