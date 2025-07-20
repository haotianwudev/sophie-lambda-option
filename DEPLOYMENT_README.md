# Options Analytics API Deployment Guide

This guide provides instructions for deploying the enhanced Options Analytics API to AWS Lambda.

## Prerequisites

- AWS CLI configured with appropriate permissions
- Docker installed and running
- Node.js and npm (for Serverless Framework)
- Python 3.12
- Serverless Framework installed (`npm install -g serverless`)

## Deployment Options

There are two deployment scripts available:

1. **Standard Deployment (`deploy.ps1`)**: Deploys the standard version of the API
2. **Enhanced Deployment (`deploy_enhanced.ps1`)**: Deploys the enhanced version with all improvements

## Enhanced Deployment

The enhanced deployment includes:
- Stock and VIX previous close prices and percentage changes
- Filtered expiration dates (2w, 1m, 6w, 2m)
- Additional option fields (contractSymbol, lastTradeDate, volume, openInterest)
- Moneyness calculation and filtering
- Enhanced implied volatility calculations (bid, mid, ask)
- Performance optimizations

### Deployment Steps

1. **Run Tests (Optional but Recommended)**

   ```powershell
   python -m pytest tests/
   ```

2. **Deploy the Enhanced API**

   ```powershell
   ./deploy_enhanced.ps1 -Stage dev -Region us-east-1
   ```

   Parameters:
   - `-Stage`: Deployment stage (default: dev)
   - `-Region`: AWS region (default: us-east-1)
   - `-ImageTag`: Docker image tag (default: latest)
   - `-UseOptimized`: Use the optimized handler (default: true)
   - `-SkipTests`: Skip running tests before deployment (default: false)

   Example:
   ```powershell
   ./deploy_enhanced.ps1 -Stage prod -Region us-east-1 -ImageTag v1.0.0
   ```

3. **Verify Deployment**

   After deployment, the script will output the API endpoint URL. Test it with:

   ```bash
   curl -X GET https://[your-api-endpoint]/options-analytics?ticker=SPY
   ```

## Standard Deployment

If you need to deploy the standard version without enhancements:

```powershell
./deploy.ps1 -Stage dev -Region us-east-1
```

## Troubleshooting

### Docker Image Architecture Issues

If you see this error:
```
The image manifest, config or layer media type for the source image ... is not supported.
```

This means you have a multi-architecture image. The deployment scripts use the correct flags to ensure single architecture:
- `--platform linux/amd64`
- `--provenance=false`

### Deployment Failures

1. **Check AWS Credentials**
   ```powershell
   aws sts get-caller-identity
   ```

2. **Check ECR Repository**
   Ensure the ECR repository exists:
   ```powershell
   aws ecr describe-repositories --repository-names options-analytics-api-dev
   ```
   If it doesn't exist, create it:
   ```powershell
   aws ecr create-repository --repository-name options-analytics-api-dev
   ```

3. **Check Lambda Logs**
   ```powershell
   serverless logs -f optionsAnalytics --stage dev --region us-east-1 --tail
   ```

## Rollback

If you need to roll back to a previous version:

1. **List available images**
   ```powershell
   aws ecr describe-images --repository-name options-analytics-api-dev
   ```

2. **Update the serverless.yml file** with the previous image tag

3. **Redeploy**
   ```powershell
   serverless deploy --stage dev --region us-east-1
   ```

## Monitoring

After deployment, monitor the API performance:

1. **CloudWatch Logs**
   ```powershell
   serverless logs -f optionsAnalytics --stage dev --region us-east-1 --tail
   ```

2. **CloudWatch Metrics**
   - Check Lambda execution time
   - Check Lambda memory usage
   - Check API Gateway request count

## Security Considerations

- The API uses CORS headers that allow requests from any origin (`*`)
- Consider restricting CORS to specific origins in production
- Review IAM permissions to ensure least privilege