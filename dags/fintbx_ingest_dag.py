#!/usr/bin/env python3
"""
AURELIA Ingestion DAG
Processes Financial Toolbox PDF into Pinecone vectors
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from google.cloud import storage
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

# Configuration from environment
GCS_BUCKET = os.getenv("AURELIA_GCS_BUCKET")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Default arguments
default_args = {
    'owner': 'aurelia',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}


def download_pdf_from_gcs(**context):
    """Download PDF from GCS to local storage"""
    logger.info("📥 Downloading PDF from GCS...")
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET)
    blob = bucket.blob("raw/fintbx.pdf")
    
    local_path = "/tmp/fintbx.pdf"
    blob.download_to_filename(local_path)
    
    file_size = os.path.getsize(local_path) / (1024 * 1024)  # MB
    logger.info(f"✅ Downloaded PDF ({file_size:.1f} MB)")
    
    return local_path


def convert_pdf_to_markdown(**context):
    """Convert PDF to markdown using pymupdf"""
    logger.info("📄 Converting PDF to Markdown...")
    
    import fitz  # PyMuPDF
    
    pdf_path = "/tmp/fintbx.pdf"
    output_dir = Path("/tmp/markdown")
    output_dir.mkdir(exist_ok=True)
    
    # Open PDF
    doc = fitz.open(pdf_path)
    
    logger.info(f"Converting {len(doc)} pages...")
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        
        # Save to markdown
        md_file = output_dir / f"page_{page_num + 1:03d}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# Page {page_num + 1}\n\n")
            f.write("---\n\n")
            f.write(text)
        
        if (page_num + 1) % 50 == 0:
            logger.info(f"  Processed {page_num + 1}/{len(doc)} pages")
    
    logger.info(f"✅ Converted {len(doc)} pages to markdown")
    return str(output_dir)


def parse_markdown_to_jsonl(**context):
    """Run parser to extract structured elements"""
    logger.info("🔎 Parsing markdown files...")
    
    import subprocess
    
    markdown_dir = "/tmp/markdown"
    output_dir = "/tmp/parsed"
    
    # Create Python script to run the REAL parser via wrapper
    script = f"""
import sys
sys.path.insert(0, '/home/airflow/gcs/dags')

from utils.parser import parse_documents

# Call the wrapper (which now uses the real parser)
parse_documents('{markdown_dir}', '{output_dir}')
"""
    
    with open("/tmp/run_parser.py", "w") as f:
        f.write(script)
    
    result = subprocess.run(
        ["python", "/tmp/run_parser.py"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Parser failed: {result.stderr}")
        logger.error(f"Parser stdout: {result.stdout}")
        raise Exception("Parser failed")
    
    logger.info("✅ Parsing complete")
    logger.info(f"Parser output:\n{result.stdout}")
    
    return output_dir


def upload_to_pinecone(**context):
    """Generate embeddings and upload to Pinecone"""
    logger.info("📤 Uploading to Pinecone...")
    
    import subprocess
    
    # Create script to run the REAL uploader via wrapper
    script = """
import sys
sys.path.insert(0, '/home/airflow/gcs/dags')

from utils.uploader import upload_documents

# Call the wrapper (which now uses the real uploader)
upload_documents()
"""
    
    with open("/tmp/run_upload.py", "w") as f:
        f.write(script)
    
    result = subprocess.run(
        ["python", "/tmp/run_upload.py"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Upload failed: {result.stderr}")
        logger.error(f"Upload stdout: {result.stdout}")
        raise Exception("Upload failed")
    
    logger.info("✅ Upload to Pinecone complete")
    logger.info(f"Upload output:\n{result.stdout}")


def upload_artifacts_to_gcs(**context):
    """Upload processed artifacts back to GCS"""
    logger.info("💾 Uploading artifacts to GCS...")
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET)
    
    # Upload markdown files
    for md_file in Path("/tmp/markdown").glob("*.md"):
        blob = bucket.blob(f"markdown/{md_file.name}")
        blob.upload_from_filename(str(md_file))
    
    # Upload parsed files
    for parsed_file in Path("/tmp/parsed").glob("*"):
        blob = bucket.blob(f"parsed/{parsed_file.name}")
        blob.upload_from_filename(str(parsed_file))
    
    logger.info("✅ Artifacts uploaded to GCS")


# Define DAG
with DAG(
    dag_id='fintbx_ingest_dag',
    default_args=default_args,
    description='Ingest Financial Toolbox PDF into vector database',
    schedule_interval='@weekly',  # Run every Sunday
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['ingestion', 'etl', 'pdf-processing'],
) as dag:
    
    # Task 1: Download PDF
    download_task = PythonOperator(
        task_id='download_pdf_from_gcs',
        python_callable=download_pdf_from_gcs,
        provide_context=True,
    )
    
    # Task 2: Convert to Markdown
    convert_task = PythonOperator(
        task_id='convert_pdf_to_markdown',
        python_callable=convert_pdf_to_markdown,
        provide_context=True,
    )
    
    # Task 3: Parse Markdown
    parse_task = PythonOperator(
        task_id='parse_markdown_to_jsonl',
        python_callable=parse_markdown_to_jsonl,
        provide_context=True,
    )
    
    # Task 4: Upload to Pinecone
    upload_task = PythonOperator(
        task_id='upload_to_pinecone',
        python_callable=upload_to_pinecone,
        provide_context=True,
    )
    
    # Task 5: Upload artifacts to GCS
    artifacts_task = PythonOperator(
        task_id='upload_artifacts_to_gcs',
        python_callable=upload_artifacts_to_gcs,
        provide_context=True,
    )
    
    # Task 6: Cleanup
    cleanup_task = BashOperator(
        task_id='cleanup_temp_files',
        bash_command='rm -rf /tmp/fintbx.pdf /tmp/markdown /tmp/parsed',
    )
    