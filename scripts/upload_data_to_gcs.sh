#!/bin/bash
set -e

echo "📤 AURELIA Data Upload Script"
echo "======================================"

# Configuration
BUCKET_NAME="aurelia-aurelia-rag-pipeline-data"
PROJECT_ID="aurelia-rag-pipeline"

# Check if fintbx.pdf exists in Data/raw/
if [ -f "Data/raw/fintbx.pdf" ]; then
    PDF_PATH="Data/raw/fintbx.pdf"
elif [ -f "Data/raw/fintbx_full.pdf" ]; then
    PDF_PATH="Data/raw/fintbx_full.pdf"
else
    echo "❌ Error: fintbx.pdf not found in Data/raw/"
    echo ""
    echo "Please place your Financial Toolbox PDF in Data/raw/"
    echo "Expected location:"
    echo "  Data/raw/fintbx.pdf"
    exit 1
fi

echo "📄 Found PDF: $PDF_PATH"

# Check if bucket exists
if ! gsutil ls "gs://$BUCKET_NAME" &> /dev/null; then
    echo "❌ Error: Bucket $BUCKET_NAME does not exist"
    echo "Run 'terraform apply' first to create infrastructure"
    exit 1
fi

echo "✅ Bucket exists: $BUCKET_NAME"

# Upload PDF
echo ""
echo "📤 Uploading PDF to GCS..."
gsutil cp "$PDF_PATH" "gs://$BUCKET_NAME/raw/fintbx.pdf"

# Set metadata
gsutil setmeta \
  -h "Content-Type:application/pdf" \
  -h "Cache-Control:public, max-age=3600" \
  "gs://$BUCKET_NAME/raw/fintbx.pdf"

# Verify upload
echo ""
echo "✅ Upload complete!"
echo ""
echo "📊 Verification:"
gsutil ls -lh "gs://$BUCKET_NAME/raw/fintbx.pdf"

echo ""
echo "======================================"
echo "✅ Data upload successful!"
echo ""
echo "📋 Next steps:"
echo "  1. Go to Airflow UI"
echo "  2. Trigger 'fintbx_ingest_dag'"
echo "  3. Watch the pipeline process your PDF!"
echo "======================================"
