# Simple deployment script for Options Analytics API
# This script builds and deploys the Docker container to AWS Lambda

param(
    [string]$Stage = "dev",
    [string]$Region = "us-east-1",
    [string]$ImageTag = "latest"
)

Write-Host "========================================="
Write-Host "Options Analytics API Deployment"
Write-Host "========================================="
Write-Host "Stage: $Stage"
Write-Host "Region: $Region"
Write-Host "Image Tag: $ImageTag"
Write-Host ""

# Get AWS account ID
$awsAccount = (aws sts get-caller-identity --query Account --output text)
Write-Host "AWS Account: $awsAccount"

# ECR repository URI
$ecrUri = "$awsAccount.dkr.ecr.$Region.amazonaws.com/options-analytics-api-$Stage"

Write-Host "Building and pushing Docker image..."
docker buildx build --platform linux/amd64 --provenance=false -t $ecrUri`:$ImageTag . --push

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed!"
    exit 1
}

Write-Host "✅ Docker image built and pushed successfully!"

Write-Host "Deploying to AWS Lambda..."
serverless deploy --stage $Stage --region $Region

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deployment failed!"
    exit 1
}

Write-Host "✅ Deployment completed successfully!"

# Get the API endpoint
Write-Host ""
Write-Host "API Information:"
serverless info --stage $Stage --region $Region

Write-Host ""
Write-Host "🎉 Deployment complete! Your API is ready to use." 