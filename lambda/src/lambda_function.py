import base64
import json
import os
import time
import uuid

import boto3
from botocore.exceptions import ClientError

s3 = boto3.client("s3")
bedrock = boto3.client("bedrock-runtime")

IMAGE_BUCKET = os.environ["IMAGE_BUCKET"]
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "amazon.titan-image-generator-v2:0")
IMAGE_PREFIX = os.environ.get("IMAGE_PREFIX", "generated")
DEFAULT_URL_EXPIRY_SECONDS = int(os.environ.get("PRESIGNED_URL_EXPIRY_SECONDS", "3600"))


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _build_model_payload(prompt: str, negative_prompt: str, height: int, width: int, cfg_scale: float, steps: int, seed: int) -> dict:
    if MODEL_ID.startswith("amazon.titan-image-generator"):
        payload = {
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {"text": prompt},
            "imageGenerationConfig": {
                "numberOfImages": 1,
                "quality": "standard",
                "cfgScale": cfg_scale,
                "height": height,
                "width": width,
                "seed": seed,
            },
        }
        if negative_prompt:
            payload["textToImageParams"]["negativeText"] = negative_prompt
        return payload

    # Backward compatibility for Stability model payloads.
    text_prompts = [{"text": prompt}]
    if negative_prompt:
        text_prompts.append({"text": negative_prompt, "weight": -1})
    return {
        "text_prompts": text_prompts,
        "height": height,
        "width": width,
        "cfg_scale": cfg_scale,
        "steps": steps,
        "seed": seed,
    }


def _extract_image_base64(model_response: dict) -> str:
    # Titan responses typically return base64 images in an "images" array.
    images = model_response.get("images", [])
    if images and isinstance(images, list):
        return images[0]

    # Backward compatibility for Stability response schema.
    artifacts = model_response.get("artifacts", [])
    if artifacts and isinstance(artifacts, list) and "base64" in artifacts[0]:
        return artifacts[0]["base64"]

    raise ValueError("No image payload found in Bedrock response")


def lambda_handler(event, context):
    body = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON body"})

    prompt = payload.get("prompt")
    if not prompt:
        return _response(400, {"error": "'prompt' is required"})

    negative_prompt = payload.get("negative_prompt")
    height = int(payload.get("height", 1024))
    width = int(payload.get("width", 1024))
    cfg_scale = float(payload.get("cfg_scale", 10))
    steps = int(payload.get("steps", 30))
    seed = int(payload.get("seed", int(time.time()) % 4294967295))
    expires_in = int(payload.get("url_expires_in", DEFAULT_URL_EXPIRY_SECONDS))

    request_payload = _build_model_payload(
        prompt=prompt,
        negative_prompt=negative_prompt,
        height=height,
        width=width,
        cfg_scale=cfg_scale,
        steps=steps,
        seed=seed,
    )

    try:
        model_resp = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(request_payload),
            contentType="application/json",
            accept="application/json",
        )

        response_body = json.loads(model_resp["body"].read())
        image_b64 = _extract_image_base64(response_body)
        image_bytes = base64.b64decode(image_b64)

        key = f"{IMAGE_PREFIX}/{uuid.uuid4()}.png"
        s3.put_object(
            Bucket=IMAGE_BUCKET,
            Key=key,
            Body=image_bytes,
            ContentType="image/png",
        )
        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": IMAGE_BUCKET, "Key": key},
            ExpiresIn=expires_in,
        )

        return _response(
            200,
            {
                "message": "Image generated and stored",
                "model_id": MODEL_ID,
                "bucket": IMAGE_BUCKET,
                "key": key,
                "s3_uri": f"s3://{IMAGE_BUCKET}/{key}",
                "presigned_url": presigned_url,
                "url_expires_in": expires_in,
            },
        )
    except (ClientError, ValueError) as exc:
        return _response(500, {"error": str(exc)})
