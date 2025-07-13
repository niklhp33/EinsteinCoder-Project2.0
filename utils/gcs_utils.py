import logging
import os
import io
from typing import Optional, List, Dict, Any, Tuple
from google.cloud import storage

from config import GLOBAL_CONFIG

logger = logging.getLogger(__name__)

def get_gcs_client():
    """
    Initializes and returns a Google Cloud Storage client.
    """
    try:
        if 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ:
            sa_key_path = GLOBAL_CONFIG['gcp']['service_account_key_path']
            if os.path.exists(sa_key_path) and os.path.isfile(sa_key_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = sa_key_path
                logger.info(f"GOOGLE_APPLICATION_CREDENTIALS set from config: {sa_key_path}")
            else:
                logger.warning(f"Service account key not found at {sa_key_path}. GCS client might use default credentials.")
        
        client = storage.Client()
        logger.info("Google Cloud Storage client initialized.")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Google Cloud Storage client: {e}", exc_info=True)
        return None

def upload_to_gcs(source_file_name: str, destination_blob_name: str, bucket_name: str) -> bool:
    """Uploads a file to the GCS bucket."""
    client = get_gcs_client()
    if not client:
        return False
    
    if not os.path.exists(source_file_name):
        logger.error(f"Source file for GCS upload not found: {source_file_name}")
        return False

    try:
        bucket = client.get_bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        logger.info(f"File {source_file_name} uploaded to gs://{bucket_name}/{destination_blob_name}.")
        return True
    except Exception as e:
        logger.error(f"Failed to upload {source_file_name} to GCS bucket {bucket_name}/{destination_blob_name}: {e}", exc_info=True)
        return False

def download_from_gcs(source_blob_name: str, destination_file_name: str, bucket_name: str) -> bool:
    """Downloads a blob from the GCS bucket."""
    client = get_gcs_client()
    if not client:
        return False

    try:
        bucket = client.get_bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        
        os.makedirs(os.path.dirname(destination_file_name), exist_ok=True)
        
        blob.download_to_filename(destination_file_name)
        logger.info(f"Blob gs://{bucket_name}/{source_blob_name} downloaded to {destination_file_name}.")
        return True
    except Exception as e:
        logger.error(f"Failed to download {source_blob_name} from GCS bucket {bucket_name}: {e}", exc_info=True)
        return False

def list_blobs(bucket_name: str, prefix: Optional[str] = None) -> List[str]:
    """Lists all the blobs in the bucket that begin with the prefix."""
    client = get_gcs_client()
    if not client:
        return []

    blobs_list = []
    try:
        bucket = client.get_bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=prefix)
        for blob in blobs:
            blobs_list.append(blob.name)
        logger.info(f"Listed {len(blobs_list)} blobs in bucket {bucket_name} with prefix {prefix}.")
        return blobs_list
    except Exception as e:
        logger.error(f"Failed to list blobs in bucket {bucket_name} with prefix {prefix}: {e}", exc_info=True)
        return []

def delete_blob(blob_name: str, bucket_name: str) -> bool:
    """Deletes a blob from the GCS bucket."""
    client = get_gcs_client()
    if not client:
        return False

    try:
        bucket = client.get_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()
        logger.info(f"Blob {blob_name} deleted from bucket {bucket_name}.")
        return True
    except Exception as e:
        logger.error(f"Failed to delete blob {blob_name} from bucket {bucket_name}: {e}", exc_info=True)
        return False
