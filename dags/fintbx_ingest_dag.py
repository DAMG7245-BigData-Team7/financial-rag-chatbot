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
    
    # Create Python script to run parser
    script = f"""
import sys
sys.path.insert(0, '/home/airflow/gcs/dags')

from utils.parser import parse_documents

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
    
    # CRITICAL: Upload JSONL to GCS so Task 4 can access it
    logger.info("📤 Uploading JSONL to GCS for next task...")
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET)
    
    # Upload JSONL
    local_jsonl = "/tmp/parsed/markdown_enhanced.jsonl"
    blob = bucket.blob("temp/markdown_enhanced.jsonl")
    blob.upload_from_filename(local_jsonl)
    
    # Pass GCS path via XCom
    gcs_path = f"gs://{GCS_BUCKET}/temp/markdown_enhanced.jsonl"
    context['task_instance'].xcom_push(key='jsonl_gcs_path', value=gcs_path)
    
    logger.info(f"✅ JSONL uploaded to: {gcs_path}")
    
    return output_dir


def upload_to_pinecone(**context):
    """Download JSONL from GCS and upload to Pinecone"""
    logger.info("📤 Preparing upload to Pinecone...")
    
    # Get GCS path from Task 3
    jsonl_gcs_path = context['task_instance'].xcom_pull(
        task_ids='parse_markdown_to_jsonl',
        key='jsonl_gcs_path'
    )
    
    logger.info(f"📥 Downloading JSONL from: {jsonl_gcs_path}")
    
    # Download from GCS
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET)
    blob = bucket.blob("temp/markdown_enhanced.jsonl")
    
    local_jsonl = "/tmp/markdown_enhanced.jsonl"
    blob.download_to_filename(local_jsonl)
    
    file_size = Path(local_jsonl).stat().st_size
    logger.info(f"✅ Downloaded JSONL ({file_size:,} bytes)")
    
    # Import and run the uploader
    logger.info("🚀 Running AURELIA upload pipeline...")
    import sys
    sys.path.insert(0, '/home/airflow/gcs/dags')
    
    from utils.uploader import upload_documents
    
    # This will convert JSONL → LangChain docs → Upload to Pinecone
    index = upload_documents(jsonl_path=local_jsonl)
    
    # Verify final count
    stats = index.describe_index_stats()
    
    logger.info(f"\n📊 Final Pinecone Stats:")
    logger.info(f"   Total vectors: {stats.total_vector_count:,}")
    logger.info(f"   Dimension: {stats.dimension}")
    logger.info("✅ Upload complete!")


def upload_artifacts_to_gcs(**context):
    """Upload processed artifacts back to GCS"""
    logger.info("💾 Uploading artifacts to GCS...")
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET)
    
    # Upload markdown files (sample - not all 3462)
    markdown_dir = Path("/tmp/markdown")
    md_files = list(markdown_dir.glob("*.md"))[:100]  # First 100 only
    
    for md_file in md_files:
        blob = bucket.blob(f"markdown/{md_file.name}")
        blob.upload_from_filename(str(md_file))
    
    logger.info(f"   Uploaded {len(md_files)} markdown files (sample)")
    
    # JSONL already uploaded in Task 3, just confirm
    logger.info(f"   JSONL already in GCS: temp/markdown_enhanced.jsonl")
    
    logger.info("✅ Artifacts uploaded to GCS")


# Define DAG
with DAG(
    dag_id='fintbx_ingest_dag',
    default_args=default_args,
    description='Ingest Financial Toolbox PDF into vector database',
    schedule_interval='@weekly',
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['ingestion', 'etl', 'pdf-processing'],
) as dag:
    
    download_task = PythonOperator(
        task_id='download_pdf_from_gcs',
        python_callable=download_pdf_from_gcs,
        provide_context=True,
    )
    
    convert_task = PythonOperator(
        task_id='convert_pdf_to_markdown',
        python_callable=convert_pdf_to_markdown,
        provide_context=True,
    )
    
    parse_task = PythonOperator(
        task_id='parse_markdown_to_jsonl',
        python_callable=parse_markdown_to_jsonl,
        provide_context=True,
    )
    
    upload_task = PythonOperator(
        task_id='upload_to_pinecone',
        python_callable=upload_to_pinecone,
        provide_context=True,
        execution_timeout=timedelta(hours=2),
    )
    
    artifacts_task = PythonOperator(
        task_id='upload_artifacts_to_gcs',
        python_callable=upload_artifacts_to_gcs,
        provide_context=True,
    )
    
    cleanup_task = BashOperator(
        task_id='cleanup_temp_files',
        bash_command='rm -rf /tmp/fintbx.pdf /tmp/markdown /tmp/parsed /tmp/markdown_enhanced.jsonl',
    )
    
    download_task >> convert_task >> parse_task >> upload_task >> artifacts_task >> cleanup_task