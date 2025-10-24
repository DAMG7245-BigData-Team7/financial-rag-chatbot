# In fintbx_ingest_dag.py

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
        raise Exception("Parser failed")
    
    logger.info("✅ Parsing complete")
    
    # Return path to JSONL for next task
    jsonl_path = f"{output_dir}/markdown_enhanced.jsonl"  # Adjust to actual output name
    context['task_instance'].xcom_push(key='jsonl_path', value=jsonl_path)
    
    return output_dir


def upload_to_pinecone(**context):
    """Generate embeddings and upload to Pinecone"""
    logger.info("📤 Uploading to Pinecone...")
    
    import subprocess
    
    # Get JSONL path from previous task
    jsonl_path = context['task_instance'].xcom_pull(
        task_ids='parse_markdown_to_jsonl',
        key='jsonl_path'
    ) or "/tmp/parsed/markdown_enhanced.jsonl"
    
    # Create script to run the REAL uploader via wrapper
    script = f"""
import sys
sys.path.insert(0, '/home/airflow/gcs/dags')

from utils.uploader import upload_documents

# Call the wrapper (which now uses the real uploader)
upload_documents('{jsonl_path}')
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
        raise Exception("Upload failed")
    
    logger.info("✅ Upload to Pinecone complete")