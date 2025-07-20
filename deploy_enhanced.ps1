# Enhanced deployment script for Options Analytics API with optimizations
# This script builds and deploys the Docker container to AWS Lambda with the enhanced handler

param(
    [string]$Stage = "dev",
    [string]$Region = "us-east-1",
    [string]$ImageTag = "latest",
    [switch]$UseOptimized = $true,
    [switch]$SkipTests = $false
)

Write-Host "========================================="
Write-Host "Enhanced Options Analytics API Deployment"
Write-Host "========================================="
Write-Host "Stage: $Stage"
Write-Host "Region: $Region"
Write-Host "Image Tag: $ImageTag"
Write-Host "Using Optimized Handler: $UseOptimized"
Write-Host "Skip Tests: $SkipTests"
Write-Host ""

# Run tests before deployment if not skipped
if (-not $SkipTests) {
    Write-Host "Running tests before deployment..."
    python -m pytest tests/
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Tests failed! Fix the issues before deploying."
        exit 1
    }
    
    Write-Host "✅ All tests passed!"
}

# Get AWS account ID
$awsAccount = (aws sts get-caller-identity --query Account --output text)
Write-Host "AWS Account: $awsAccount"

# ECR repository URI
$ecrUri = "$awsAccount.dkr.ecr.$Region.amazonaws.com/options-analytics-api-$Stage"

# Create a temporary Dockerfile for the enhanced version
$dockerfilePath = "Dockerfile.enhanced"
$handlerFile = if ($UseOptimized) { "optimized_handler.py" } else { "handler.py" }

Write-Host "Creating enhanced Dockerfile using $handlerFile as the main handler..."

@"
# Multi-stage build to ensure clean Linux image
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.12 as builder

# Copy requirements and install dependencies
COPY requirements.txt `${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r `${LAMBDA_TASK_ROOT}/requirements.txt -t `${LAMBDA_TASK_ROOT}

# Copy function code
COPY $handlerFile `${LAMBDA_TASK_ROOT}/handler.py
COPY src/ `${LAMBDA_TASK_ROOT}/src/
COPY scripts/ `${LAMBDA_TASK_ROOT}/scripts/
COPY tests/ `${LAMBDA_TASK_ROOT}/tests/

# Final stage - clean image
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.12

# Copy everything from builder
COPY --from=builder `${LAMBDA_TASK_ROOT} `${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD ["handler.get_options_analytics"]
"@ | Out-File -FilePath $dockerfilePath -Encoding utf8

Write-Host "Building and pushing Docker image..."
docker buildx build --platform linux/amd64 --provenance=false -t $ecrUri`:$ImageTag -f $dockerfilePath . --push

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed!"
    Remove-Item -Path $dockerfilePath
    exit 1
}

Write-Host "✅ Docker image built and pushed successfully!"

# Clean up temporary Dockerfile
Remove-Item -Path $dockerfilePath
Write-Host "Temporary Dockerfile removed."

# Verify the image architecture
Write-Host "Verifying image architecture..."
$manifest = docker manifest inspect $ecrUri`:$ImageTag 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to inspect image manifest!"
    exit 1
}

if ($manifest -match '"manifests"') {
    Write-Host "❌ WARNING: Multi-architecture image detected! This will cause Lambda deployment issues."
    Write-Host "   The image should be single architecture (linux/amd64 only)."
    Write-Host "   Check the README for correct build commands."
    exit 1
} else {
    Write-Host "✅ Image verified as single architecture (linux/amd64)"
}

# Create a temporary serverless.yml file for the enhanced version
$serverlessPath = "serverless.enhanced.yml"

Write-Host "Creating enhanced serverless.yml configuration..."

@"
service: options-analytics-api
frameworkVersion: '3'

provider:
  name: aws
  region: `${opt:region, '$Region'}
  stage: `${opt:stage, '$Stage'}
  timeout: 30
  memorySize: 2048
  architecture: x86_64
  ecr:
    images:
      options-analytics:
        path: ./
        file: Dockerfile
        platform: linux/amd64
  environment:
    PYTHONPATH: "`${PYTHONPATH}:`${AWS_LAMBDA_RUNTIME_API}"
    STAGE: `${self:provider.stage}
  httpApi:
    cors:
      allowedOrigins:
        - '*'
      allowedHeaders:
        - Content-Type
        - X-Amz-Date
        - Authorization
        - X-Api-Key
        - X-Amz-Security-Token
        - X-Amz-User-Agent
      allowedMethods:
        - GET
        - OPTIONS
  iam:
    role:
      statements:
        - Effect: Allow
          Action:
            - logs:CreateLogGroup
            - logs:CreateLogStream
            - logs:PutLogEvents
          Resource: 
            - 'arn:aws:logs:`${aws:region}:`${aws:accountId}:log-group:/aws/lambda/*:*:*'

functions:
  optionsAnalytics:
    image:
      uri: $ecrUri`:$ImageTag
    description: 'Enhanced Options Analytics API with improved data and calculations'
    events:
      - httpApi:
          path: /options-analytics
          method: get
    environment:
      LOG_LEVEL: `${opt:log-level, 'INFO'}
"@ | Out-File -FilePath $serverlessPath -Encoding utf8

Write-Host "Deploying to AWS Lambda..."
serverless deploy --stage $Stage --region $Region --config $serverlessPath

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deployment failed!"
    Remove-Item -Path $serverlessPath
    exit 1
}

Write-Host "✅ Deployment completed successfully!"

# Clean up temporary serverless file
Remove-Item -Path $serverlessPath
Write-Host "Temporary serverless configuration removed."

# Get the API endpoint
Write-Host ""
Write-Host "API Information:"
serverless info --stage $Stage --region $Region

Write-Host ""
Write-Host "🎉 Enhanced deployment complete! Your API is ready to use."
Write-Host ""
Write-Host "Test your API with:"
Write-Host "curl -X GET https://[your-api-endpoint]/options-analytics?ticker=SPY"