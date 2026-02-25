variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for naming AWS resources"
  type        = string
  default     = "poster-generation"
}

variable "environment" {
  description = "Environment tag (e.g., dev, prod)"
  type        = string
  default     = "dev"
}

variable "s3_bucket_name" {
  description = "Optional explicit S3 bucket name. Leave empty to auto-generate one."
  type        = string
  default     = ""
}

variable "bedrock_model_id" {
  description = "Bedrock model ID for image generation"
  type        = string
  default     = "amazon.titan-image-generator-v2:0"
}

variable "image_prefix" {
  description = "Prefix for generated image object keys in S3"
  type        = string
  default     = "generated"
}
