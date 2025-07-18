#!/bin/bash

# Deployment script for Options Analytics API
# Usage: ./deploy.sh [stage] [region] [--verbose] [--dry-run]

set -e  # Exit on any error

# Default values
STAGE=${1:-dev}
REGION=${2:-us-east-1}
VERBOSE=false
DRY_RUN=false

# Parse additional arguments
for arg in "$@"; do
    case $arg in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            echo "Usage: ./deploy.sh [stage] [region] [--verbose] [--dry-run] [--help]"
            echo ""
            echo "Arguments:"
            echo "  stage     Deployment stage (default: dev)"
            echo "  region    AWS region (default: us-east-1)"
            echo ""
            echo "Options:"
            echo "  --verbose   Enable verbose output"
            echo "  --dry-run   Show what would be deployed without actually deploying"
            echo "  --help      Show this help message"
            exit 0
            ;;
    esac
done

echo "========================================="
echo "Options Analytics API Deployment Script"
echo "========================================="
echo "Stage: $STAGE"
echo "Region: $REGION"
echo "Verbose: $VERBOSE"
echo "Dry Run: $DRY_RUN"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI not configured or credentials invalid"
    echo "Please run 'aws configure' or set AWS environment variables"
    exit 1
fi

# Get AWS account info
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_USER=$(aws sts get-caller-identity --query Arn --output text)
echo "✅ AWS Account: $AWS_ACCOUNT"
echo "✅ AWS User: $AWS_USER"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js"
    exit 1
fi
echo "✅ Node.js version: $(node --version)"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.9+"
    exit 1
fi
echo "✅ Python version: $(python3 --version)"

# Check if serverless is installed
if ! command -v serverless &> /dev/null; then
    echo "⚠️  Serverless Framework not found. Installing..."
    npm install -g serverless
fi
echo "✅ Serverless version: $(serverless --version | head -1)"

# Install Node.js dependencies
echo ""
echo "Installing Node.js dependencies..."
if [ "$VERBOSE" = true ]; then
    npm install
else
    npm install --silent
fi

# Install Python dependencies (for local testing)
echo "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    if [ "$VERBOSE" = true ]; then
        pip3 install -r requirements.txt
    else
        pip3 install -r requirements.txt --quiet
    fi
fi

# Run tests before deployment
echo ""
echo "Running tests before deployment..."
if [ -d "tests" ]; then
    if [ "$VERBOSE" = true ]; then
        python3 -m pytest tests/ -v
    else
        python3 -m pytest tests/ --tb=short
    fi
    
    if [ $? -ne 0 ]; then
        echo "❌ Tests failed. Aborting deployment."
        exit 1
    fi
    echo "✅ All tests passed"
else
    echo "⚠️  No tests directory found, skipping tests"
fi

# Package information
echo ""
echo "Packaging information:"
serverless package --stage $STAGE --region $REGION

if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "🔍 DRY RUN MODE - Would deploy with the following configuration:"
    echo "Service: options-analytics-api"
    echo "Stage: $STAGE"
    echo "Region: $REGION"
    echo "Runtime: python3.9"
    echo "Memory: 512MB"
    echo "Timeout: 30s"
    echo ""
    echo "Functions:"
    echo "  - optionsAnalytics: handler.get_options_analytics"
    echo ""
    echo "Endpoints:"
    echo "  - GET /options-analytics"
    echo ""
    echo "To actually deploy, run without --dry-run flag"
    exit 0
fi

# Deploy the service
echo ""
echo "🚀 Deploying to AWS..."
echo "This may take a few minutes..."

if [ "$VERBOSE" = true ]; then
    serverless deploy --stage $STAGE --region $REGION --verbose
else
    serverless deploy --stage $STAGE --region $REGION
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "📊 Service Information:"
    serverless info --stage $STAGE --region $REGION
    
    echo ""
    echo "🔗 API Endpoint:"
    ENDPOINT=$(serverless info --stage $STAGE --region $REGION | grep "GET - " | awk '{print $3}')
    echo "$ENDPOINT"
    
    echo ""
    echo "🧪 Test the API:"
    echo "curl \"$ENDPOINT?ticker=SPY\""
    
    echo ""
    echo "📝 View logs:"
    echo "serverless logs -f optionsAnalytics --stage $STAGE --region $REGION --tail"
    
else
    echo ""
    echo "❌ Deployment failed!"
    echo "Check the error messages above for details"
    exit 1
fi