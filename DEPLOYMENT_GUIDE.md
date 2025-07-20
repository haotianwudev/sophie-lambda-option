# Deployment Guide for Options Analytics API

This guide provides step-by-step instructions for deploying the Options Analytics API to AWS Lambda.

## Prerequisites

1. Docker Desktop installed and running
2. AWS CLI configured with appropriate credentials
3. Serverless Framework installed (`npm install -g serverless`)
4. PowerShell (for Windows) or Bash (for macOS/Linux)

## Deployment Steps

### 1. Verify Docker is Running

```powershell
docker ps
```

You should see a list of running containers (or an empty list if no containers are running). If you see an error, make sure Docker Desktop is running.

### 2. Deploy Using Standard Script

For deploying with the standard handler (with our fixes for ^SPX ticker symbol):

```powershell
.\deploy.ps1
```

This will:
- Build a Docker image with the standard handler.py
- Push the image to Amazon ECR
- Deploy the Lambda function using Serverless Framework

### 3. Deploy Using Enhanced Script

For deploying with the optimized handler:

```powershell
.\deploy_enhanced.ps1 -UseOptimized $true
```

For deploying with the standard handler but using the enhanced deployment process:

```powershell
.\deploy_enhanced.ps1 -UseOptimized $false
```

### 4. Verify Deployment

After deployment, you should see the API endpoint URL in the output. You can test it with:

```
curl -X GET https://[your-api-endpoint]/options-analytics?ticker=SPY
```

Or with the ^SPX ticker (which we fixed):

```
curl -X GET https://[your-api-endpoint]/options-analytics?ticker=^SPX
```

## Troubleshooting

### Docker Issues

If you encounter Docker-related issues:

1. Make sure Docker Desktop is running
2. Restart Docker Desktop
3. Check Docker logs for any errors

### AWS Authentication Issues

If you encounter AWS authentication issues:

1. Verify your AWS credentials are configured correctly:
   ```
   aws sts get-caller-identity
   ```
2. Make sure you have the necessary permissions to push to ECR and deploy Lambda functions

### Serverless Framework Issues

If you encounter issues with the Serverless Framework:

1. Make sure you have the latest version installed:
   ```
   npm update -g serverless
   ```
2. Check the serverless.yml file for any configuration errors

## Manual Deployment Steps

If the deployment scripts are not working, you can deploy manually:

1. Build the Docker image:
   ```
   docker build -t options-analytics-api .
   ```

2. Tag the image for ECR:
   ```
   docker tag options-analytics-api:latest [aws-account-id].dkr.ecr.[region].amazonaws.com/options-analytics-api-dev:latest
   ```

3. Log in to ECR:
   ```
   aws ecr get-login-password --region [region] | docker login --username AWS --password-stdin [aws-account-id].dkr.ecr.[region].amazonaws.com
   ```

4. Push the image to ECR:
   ```
   docker push [aws-account-id].dkr.ecr.[region].amazonaws.com/options-analytics-api-dev:latest
   ```

5. Deploy using Serverless Framework:
   ```
   serverless deploy
   ```

## Summary of Changes

We made the following changes to fix the ^SPX ticker symbol issue:

1. Updated the ticker symbol validation in `src/utils/data_formatter.py` to allow the caret (^) character
2. Updated the ticker symbol validation in `src/services/options_data_fetcher.py` to allow the caret character
3. Added a custom JSON encoder to handle datetime and pandas Timestamp objects in `handler.py`
4. Added a check for the `total_options` variable in the log statement in `handler.py`

These changes ensure that the API can handle index symbols like ^SPX and ^VIX correctly.