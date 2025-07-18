# Multi-stage build to ensure clean Linux image
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.12 as builder

# Copy requirements and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt -t ${LAMBDA_TASK_ROOT}

# Copy function code
COPY handler.py ${LAMBDA_TASK_ROOT}/
COPY src/ ${LAMBDA_TASK_ROOT}/src/

# Final stage - clean image
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.12

# Copy everything from builder
COPY --from=builder ${LAMBDA_TASK_ROOT} ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD ["handler.get_options_analytics"]