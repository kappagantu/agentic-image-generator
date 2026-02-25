# Terraform Infrastructure: API Gateway + Lambda + S3 + Bedrock

This Terraform module provisions:

- S3 bucket for generated images.
- Lambda function that:
  - Accepts requests from API Gateway.
  - Calls Amazon Bedrock Stable Diffusion model.
  - Writes generated images to S3.
- API Gateway HTTP API endpoint (`POST /generate-image`) to invoke Lambda.
- IAM role/policies for Lambda logging, S3 write access, and Bedrock model invocation.

## Prerequisites

- Terraform `>= 1.5.0`
- AWS credentials configured
- Bedrock model access enabled in the target region for the configured model id

## Usage

```bash
cd infra
terraform init
cp terraform.tfvars.example terraform.tfvars
terraform plan
terraform apply
```

## Test the endpoint

After apply, use the `generate_image_endpoint` output:

```bash
curl -X POST "<generate_image_endpoint>" \
  -H "content-type: application/json" \
  -d '{
    "prompt": "A cinematic poster of a futuristic city skyline at sunset",
    "negative_prompt": "blurry, distorted",
    "height": 1024,
    "width": 1024,
    "cfg_scale": 10,
    "steps": 30
  }'
```

The Lambda response includes S3 location for the generated image.
It also includes `presigned_url`; opening that URL returns the image directly until expiry.

## Notes

- Default Bedrock model is `amazon.titan-image-generator-v2:0`. Change via `bedrock_model_id` if needed.
- S3 bucket name is auto-generated unless `s3_bucket_name` is set.
