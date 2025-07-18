# AWS Lambda Deployment Guide

## Options Analytics API - Deployment Instructions

This guide provides step-by-step instructions to deploy the Options Analytics API to AWS Lambda using the Serverless Framework.

## Prerequisites

### 1. Required Software
- **Node.js** (v14 or later) - [Download here](https://nodejs.org/)
- **Python** (3.9) - [Download here](https://www.python.org/downloads/)
- **AWS CLI** - [Installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **Git** - [Download here](https://git-scm.com/downloads)

### 2. AWS Account Setup
- AWS Account with appropriate permissions
- AWS Access Key ID and Secret Access Key
- Recommended: Create an IAM user with Lambda deployment permissions

## Step 1: Clone and Setup Project

```bash
# Clone the repository
git clone https://github.com/haotianwudev/sophie-lambda-option.git
cd sophie-lambda-option

# Install Node.js dependencies (Serverless Framework)
npm install

# Install Python dependencies
pip install -r requirements.txt
```

## Step 2: Configure AWS Credentials

### Option A: AWS CLI Configuration (Recommended)
```bash
aws configure
```
Enter your:
- AWS Access Key ID
- AWS Secret Access Key  
- Default region (e.g., `us-east-1`)
- Default output format (e.g., `json`)

### Option B: Environment Variables
```bash
export AWS_ACCESS_KEY_ID=your_access_key_here
export AWS_SECRET_ACCESS_KEY=your_secret_key_here
export AWS_DEFAULT_REGION=us-east-1
```

### Option C: AWS Credentials File
Create `~/.aws/credentials`:
```ini
[default]
aws_access_key_id = your_access_key_here
aws_secret_access_key = your_secret_key_here
```

## Step 3: Install Serverless Framework

```bash
# Install globally
npm install -g serverless

# Verify installation
serverless --version
```

## Step 4: Configure Deployment Settings

### Review serverless.yml Configuration
The `serverless.yml` file is pre-configured with:
- **Service name**: `options-analytics-api`
- **Runtime**: Python 3.9
- **Memory**: 512MB
- **Timeout**: 30 seconds
- **Region**: us-east-1 (configurable)

### Optional: Customize Settings
Edit `serverless.yml` to modify:
```yaml
provider:
  name: aws
  runtime: python3.9
  region: us-east-1  # Change region if needed
  memorySize: 512    # Adjust memory allocation
  timeout: 30        # Adjust timeout
```

## Step 5: Deploy to AWS

### Quick Deployment (Using deploy script)
```bash
# Make deploy script executable (Linux/Mac)
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### Manual Deployment
```bash
# Deploy to default stage (dev)
serverless deploy

# Deploy to specific stage
serverless deploy --stage prod

# Deploy to specific region
serverless deploy --region us-west-2
```

### Deployment Output
After successful deployment, you'll see:
```
Service Information
service: options-analytics-api
stage: dev
region: us-east-1
stack: options-analytics-api-dev
resources: 11
api keys:
  None
endpoints:
  GET - https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/dev/options-analytics
functions:
  getOptionsAnalytics: options-analytics-api-dev-getOptionsAnalytics
```

**Save the endpoint URL** - you'll need it for testing!

## Step 6: Test Deployment

### Test with curl
```bash
# Test default (SPY)
curl "https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/options-analytics"

# Test with specific ticker
curl "https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/options-analytics?ticker=AAPL"
```

### Test with Integration Script
```bash
# Run integration tests
python scripts/integration_test.py --url https://your-api-id.execute-api.us-east-1.amazonaws.com/dev

# Run performance tests
python scripts/performance_test.py --url https://your-api-id.execute-api.us-east-1.amazonaws.com/dev
```

## Step 7: Monitor and Manage

### View Logs
```bash
# View recent logs
serverless logs -f getOptionsAnalytics

# Tail logs in real-time
serverless logs -f getOptionsAnalytics --tail
```

### View Function Info
```bash
serverless info
```

### Update Function
```bash
# Deploy only function code (faster)
serverless deploy function -f getOptionsAnalytics
```

## Environment-Specific Deployments

### Development Environment
```bash
serverless deploy --stage dev
```

### Production Environment
```bash
serverless deploy --stage prod
```

### Custom Configuration per Environment
Create `serverless.${stage}.yml` files for environment-specific settings.

## Troubleshooting

### Common Issues and Solutions

#### 1. Permission Errors
```
Error: User: arn:aws:iam::xxx:user/xxx is not authorized to perform: cloudformation:CreateStack
```
**Solution**: Ensure your AWS user has the following permissions:
- CloudFormation full access
- Lambda full access
- API Gateway full access
- IAM role creation permissions
- S3 bucket access (for deployment artifacts)

#### 2. Memory/Timeout Issues
```
Task timed out after 30.00 seconds
```
**Solution**: Increase timeout and memory in `serverless.yml`:
```yaml
provider:
  memorySize: 1024
  timeout: 60
```

#### 3. Package Size Too Large
```
Unzipped size must be smaller than 262144000 bytes
```
**Solution**: The current package should be well under the limit, but if needed:
- Remove unnecessary files
- Use Lambda Layers for large dependencies
- Optimize package contents

#### 4. API Gateway CORS Issues
**Solution**: CORS is pre-configured in the handler. If issues persist:
```yaml
functions:
  getOptionsAnalytics:
    events:
      - http:
          path: options-analytics
          method: get
          cors: true
```

### Debugging Steps

1. **Check AWS Credentials**:
   ```bash
   aws sts get-caller-identity
   ```

2. **Verify Serverless Installation**:
   ```bash
   serverless --version
   ```

3. **Check Function Logs**:
   ```bash
   serverless logs -f getOptionsAnalytics --tail
   ```

4. **Test Locally** (if needed):
   ```bash
   python scripts/local_final_validation.py
   ```

## Cost Optimization

### Lambda Pricing Factors
- **Requests**: $0.20 per 1M requests
- **Duration**: $0.0000166667 per GB-second
- **Memory**: 512MB allocated

### Estimated Costs (Monthly)
- **1,000 requests**: ~$0.20
- **10,000 requests**: ~$2.00
- **100,000 requests**: ~$20.00

### Cost Optimization Tips
1. **Right-size memory allocation** - Monitor actual usage
2. **Optimize cold starts** - Keep functions warm if needed
3. **Use appropriate timeout** - Don't over-allocate
4. **Monitor with CloudWatch** - Track actual usage patterns

## Security Best Practices

### 1. IAM Permissions
- Use least-privilege principle
- Create specific IAM roles for Lambda
- Avoid using root AWS credentials

### 2. API Security
- Consider adding API keys for production
- Implement rate limiting if needed
- Monitor for unusual usage patterns

### 3. Environment Variables
- Store sensitive data in AWS Systems Manager Parameter Store
- Use encryption for sensitive environment variables

## Monitoring and Alerting

### CloudWatch Metrics
Monitor these key metrics:
- **Duration**: Function execution time
- **Errors**: Error count and rate
- **Throttles**: Concurrent execution limits
- **Memory Usage**: Actual memory consumption

### Set Up Alerts
```bash
# Example: Create CloudWatch alarm for errors
aws cloudwatch put-metric-alarm \
  --alarm-name "Lambda-Errors-OptionsAPI" \
  --alarm-description "Alert on Lambda errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

## Cleanup

### Remove Deployment
```bash
# Remove entire stack
serverless remove

# Remove specific stage
serverless remove --stage dev
```

## Support and Maintenance

### Regular Maintenance Tasks
1. **Monitor logs** for errors and performance issues
2. **Update dependencies** regularly for security
3. **Review costs** monthly
4. **Test functionality** after AWS service updates
5. **Backup configuration** and code regularly

### Getting Help
- **AWS Documentation**: [Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- **Serverless Framework**: [Documentation](https://www.serverless.com/framework/docs/)
- **GitHub Issues**: Report issues in the repository

## Next Steps

After successful deployment:

1. **Integrate with Frontend**: Use the API endpoint in your web application
2. **Set Up Monitoring**: Configure CloudWatch dashboards
3. **Implement Caching**: Consider adding CloudFront or API Gateway caching
4. **Scale Planning**: Monitor usage and plan for scaling needs
5. **Security Review**: Implement additional security measures for production

---

## Quick Reference Commands

```bash
# Deploy
serverless deploy

# View logs
serverless logs -f getOptionsAnalytics --tail

# Get service info
serverless info

# Test locally
python scripts/local_final_validation.py

# Test deployed API
python scripts/integration_test.py --url YOUR_API_URL

# Remove deployment
serverless remove
```

Your Options Analytics API is now ready for production use! 🚀