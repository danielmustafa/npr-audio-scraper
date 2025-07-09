from google.cloud import storage
import os

def get(bucket_name: str, blob_path: str) -> bytes:
    """
    Download a file from Google Cloud Storage.
    Args:
        bucket_name: Name of the GCS bucket.
        file_path: Path to the file in the bucket.
    Returns:
        The file contents as bytes.
    Raises:
        FileNotFoundError if the file does not exist.
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    if not blob.exists():
        raise FileNotFoundError(f"File {blob_path} not found in bucket {bucket_name}")
    return blob.download_as_bytes()

def save(file_path: str, bucket_name: str, destination_blob_name: str) -> tuple:
    """
    Uploads a file to the specified Google Cloud Storage bucket.
    Args:
        file_path: Local path to the file to upload.
        bucket_name: Name of the GCS bucket.
        destination_blob_name: Path in the bucket to store the file.
    Returns:
        The public URL of the uploaded file.
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(file_path)
    print(f"Uploaded {file_path} to gs://{bucket_name}/{destination_blob_name}")
    return f"gs://{bucket_name}/{destination_blob_name}", blob.public_url

def delete(bucket_name: str, blob_name: str) -> bool:
    """
    Deletes a file from the specified Google Cloud Storage bucket.
    Args:
        bucket_name: Name of the GCS bucket.
        blob_name: Path in the bucket to the file to delete.
    Returns:
        True if the file was deleted, False otherwise.
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    try:
        blob.delete()
        print(f"Deleted gs://{bucket_name}/{blob_name}")
        return True
    except Exception as e:
        print(f"Failed to delete gs://{bucket_name}/{blob_name}: {e}")
        return False