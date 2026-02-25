output "api_gateway_invoke_url" {
  description = "HTTP API invoke URL"
  value       = aws_apigatewayv2_api.http_api.api_endpoint
}

output "generate_image_endpoint" {
  description = "POST endpoint to trigger image generation"
  value       = "${aws_apigatewayv2_api.http_api.api_endpoint}/generate-image"
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.image_generator.function_name
}

output "images_bucket_name" {
  description = "S3 bucket storing generated images"
  value       = aws_s3_bucket.images.bucket
}
