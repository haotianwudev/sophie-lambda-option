# Docker Deployment Troubleshooting

## 🚨 Critical Issue: Multi-Architecture Images

### The Problem
AWS Lambda does NOT support multi-architecture (fat) Docker images. If you build an image without specifying the platform, Docker creates a multi-arch image that Lambda cannot use.

### Error Message
```
The image manifest, config or layer media type for the source image ... is not supported.
```

### ❌ Wrong Commands
```bash
# These create multi-architecture images
docker build -t image:tag .
docker buildx build -t image:tag .
docker buildx build --platform linux/amd64 -t image:tag .
```

### ✅ Correct Command
```bash
docker buildx build --platform linux/amd64 --provenance=false -t image:tag . --push
```

### Required Flags Explained
- `--platform linux/amd64`: Ensures single architecture
- `--provenance=false`: Prevents multi-arch manifest creation
- `--push`: Pushes directly to registry (required for buildx)

### Verification
```bash
# Check image architecture
docker manifest inspect your-image:tag
```

**✅ Correct Output** (Single Architecture):
```json
{
  "schemaVersion": 2,
  "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
  "config": { ... },
  "layers": [ ... ]
}
```

**❌ Wrong Output** (Multi-Architecture):
```json
{
  "schemaVersion": 2,
  "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
  "manifests": [
    { "platform": { "architecture": "amd64", "os": "linux" } },
    { "platform": { "architecture": "arm64", "os": "linux" } }
  ]
}
```

## 🔧 Dependencies Issue

### Problem
```
ModuleNotFoundError: No module named 'yfinance'
```

### Solution
Ensure dependencies are installed to the Lambda task root:

```dockerfile
# Builder stage
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.12 as builder
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt -t ${LAMBDA_TASK_ROOT}

# Final stage
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.12
COPY --from=builder ${LAMBDA_TASK_ROOT} ${LAMBDA_TASK_ROOT}
```

**Key Points**:
- Use `${LAMBDA_TASK_ROOT}` (not `/var/task`)
- Use `-t ${LAMBDA_TASK_ROOT}` flag with pip install
- Multi-stage build ensures clean final image

## 🚀 Quick Fix Commands

### If you have a multi-arch image:
```bash
# 1. Delete the problematic image
aws ecr batch-delete-image --repository-name your-repo --image-ids imageTag=latest

# 2. Rebuild with correct flags
docker buildx build --platform linux/amd64 --provenance=false -t your-image:latest . --push

# 3. Verify
docker manifest inspect your-image:latest

# 4. Deploy
serverless deploy
```

### Complete cleanup and rebuild:
```bash
# 1. Remove Lambda function
serverless remove

# 2. Delete ECR repository
aws ecr delete-repository --repository-name your-repo --force

# 3. Recreate repository
aws ecr create-repository --repository-name your-repo

# 4. Build and deploy
./deploy.ps1
```

## 📋 Checklist

Before deploying, ensure:
- [ ] Using `--platform linux/amd64` flag
- [ ] Using `--provenance=false` flag
- [ ] Using `--push` flag with buildx
- [ ] Dependencies installed to `${LAMBDA_TASK_ROOT}`
- [ ] Image verified as single architecture
- [ ] No `manifests` array in manifest inspect output 