import io
import base64
from typing import List, Optional
from PIL import Image

import torch
from diffusers import AutoPipelineForImage2Image, AutoPipelineForText2Image

from galadriel_node.config import config
from galadriel_node.sdk.entities import SdkError


# pylint: disable=too-few-public-methods
class Diffusers:
    def __init__(self, model: str):
        try:
            self.pipeline_img2img = AutoPipelineForImage2Image.from_pretrained(
                model, torch_dtype=torch.float16, use_safetensors=True
            )
            self.pipeline_txt2img = AutoPipelineForText2Image.from_pipe(
                self.pipeline_img2img
            )
            if torch.cuda.is_available():
                self.pipeline_img2img.to("cuda")
                self.pipeline_txt2img.to("cuda")
            elif (
                config.GALADRIEL_ENVIRONMENT != "production"
                and torch.backends.mps.is_available()
            ):
                # Local test with Apple Silicon
                self.pipeline_img2img.to("mps")
                self.pipeline_txt2img.to("mps")
                # Warm up the pipeline for CPU device usage
                _ = self.pipeline_txt2img(
                    "a photo of the first snow in Tallinn", num_inference_steps=1
                )
            else:
                raise SdkError("CUDA is not available")
        except Exception as e:
            raise SdkError(f"Failed to initialize Diffusion pipeline: {e}")

    def generate_images(
        self, prompt: str, image: Optional[str] = None, n: int = 1
    ) -> List[str]:
        generated_images: List[Image.Image]
        try:
            if image is not None:
                pil_image = _decode_image_from_base64(image)
                generated_images = self.pipeline_img2img(
                    prompt=prompt,
                    num_images_per_prompt=n,
                    image=pil_image,
                    strength=0.4,
                ).images
            else:
                generated_images = self.pipeline_txt2img(
                    prompt=prompt, num_images_per_prompt=n
                ).images
            return [_encode_image_to_base64(image) for image in generated_images]
        except Exception as e:
            raise SdkError(f"Failed to generate images: {e}")


def _encode_image_to_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _decode_image_from_base64(image: str) -> Image.Image:
    return Image.open(io.BytesIO(base64.b64decode(image)))
