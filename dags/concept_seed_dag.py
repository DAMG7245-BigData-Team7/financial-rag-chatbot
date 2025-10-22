#!/usr/bin/env python3
"""
AURELIA Concept Seeding DAG
Pre-generates concept notes and caches them in PostgreSQL
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import requests
import os
import logging

logger = logging.getLogger(__name__)

# Predefined concept list
CONCEPT_LIST = [
    "Duration",
    "Sharpe Ratio",
    "Black-Scholes Model",
    "Internal Rate of Return",
    "Net Present Value",
    "Portfolio Optimization",
    "Yield Curve",
    "Option Greeks",
    "Monte Carlo Simulation",
    "Value at Risk",
    "Efficient Frontier",
    "Capital Asset Pricing Model",
    "Bond Convexity",
    "Modified Duration",
]

# Default arguments
default_args = {
    'owner': 'aurelia',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}


def get_fastapi_url():
    """Get FastAPI service URL from Cloud Run"""
    import subprocess
    
    result = subprocess.run(
        ["gcloud", "run", "services", "describe", "aurelia-api",
         "--region", "us-east1",
         "--format", "value(status.url)"],
        capture_output=True,
        text=True
    )
    
    url = result.stdout.strip()
    if not url:
        raise Exception("FastAPI service not found")
    
    return url


def validate_api_connection(**context):
    """Check if FastAPI is healthy"""
    logger.info("🔍 Validating FastAPI connection...")
    
    fastapi_url = get_fastapi_url()
    
    response = requests.get(f"{fastapi_url}/health", timeout=30)
    response.raise_for_status()
    
    health_data = response.json()
    
    if health_data.get("status") != "healthy":
        raise Exception(f"FastAPI unhealthy: {health_data}")
    
    logger.info(f"✅ FastAPI healthy at {fastapi_url}")
    return fastapi_url


def call_seed_endpoint(**context):
    """Call FastAPI /seed endpoint with concept list"""
    logger.info(f"🌱 Seeding {len(CONCEPT_LIST)} concepts...")
    
    fastapi_url = context['task_instance'].xcom_pull(task_ids='validate_api_connection')
    
    # Call seed endpoint
    response = requests.post(
        f"{fastapi_url}/seed",
        json={
            "concepts": CONCEPT_LIST,
            "batch_size": 5,
            "overwrite": False
        },
        timeout=600  # 10 minutes
    )
    
    response.raise_for_status()
    result = response.json()
    
    logger.info(f"✅ Seeding complete!")
    logger.info(f"   Total: {result['total']}")
    logger.info(f"   Seeded: {result['seeded']}")
    logger.info(f"   Skipped: {result['skipped']}")
    logger.info(f"   Failed: {result['failed']}")
    logger.info(f"   Duration: {result['duration_seconds']:.1f}s")
    
    # Store results for next task
    context['task_instance'].xcom_push(key='seed_results', value=result)
    
    return result


def verify_seeding(**context):
    """Verify seeding results"""
    logger.info("✅ Verifying seeding results...")
    
    fastapi_url = context['task_instance'].xcom_pull(task_ids='validate_api_connection')
    seed_results = context['task_instance'].xcom_pull(task_ids='call_seed_endpoint', key='seed_results')
    
    # Get stats from API
    response = requests.get(f"{fastapi_url}/stats", timeout=30)
    response.raise_for_status()
    
    stats = response.json()
    
    logger.info(f"📊 Database Statistics:")
    logger.info(f"   Total cached: {stats['total_cached_concepts']}")
    logger.info(f"   From fintbx: {stats['source_breakdown'].get('fintbx', 0)}")
    logger.info(f"   From Wikipedia: {stats['source_breakdown'].get('wikipedia', 0)}")
    
    success_rate = (seed_results['seeded'] / seed_results['total'] * 100) if seed_results['total'] > 0 else 0
    logger.info(f"✅ Seeding success rate: {success_rate:.1f}%")
    
    return stats


# Define DAG
with DAG(
    dag_id='concept_seed_dag',
    default_args=default_args,
    description='Pre-generate and cache financial concept notes',
    schedule_interval=None,  # Manual trigger only
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['seeding', 'cache', 'concepts'],
) as dag:
    
    # Task 1: Validate API
    validate_task = PythonOperator(
        task_id='validate_api_connection',
        python_callable=validate_api_connection,
        provide_context=True,
    )
    
    # Task 2: Call seed endpoint
    seed_task = PythonOperator(
        task_id='call_seed_endpoint',
        python_callable=call_seed_endpoint,
        provide_context=True,
    )
    
    # Task 3: Verify results
    verify_task = PythonOperator(
        task_id='verify_seeding_results',
        python_callable=verify_seeding,
        provide_context=True,
    )
    
    # Define task dependencies
    validate_task >> seed_task >> verify_task