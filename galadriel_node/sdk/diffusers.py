import io
import base64
from typing import List, Optional
from diffusers import DiffusionPipeline
from PIL import Image
import torch

from galadriel_node.config import config
from galadriel_node.sdk.entities import SdkError

DIFFUSION_MODEL = "stabilityai/stable-diffusion-3.5-medium"


# pylint: disable=too-few-public-methods
class Diffusers:
    def __init__(self, model: str):
        try:
            self.pipeline = DiffusionPipeline.from_pretrained(
                model, torch_dtype=torch.float16
            )
            if torch.cuda.is_available():
                self.pipeline.to("cuda")
            elif (
                config.GALADRIEL_ENVIRONMENT != "production"
                and torch.backends.mps.is_available()
            ):
                # Local test with Apple Silicon
                self.pipeline.to("mps")
                # Warm up the pipeline for CPU device usage
                _ = self.pipeline(
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
                generated_images = self.pipeline(
                    prompt=prompt, num_images_per_prompt=n, image=pil_image
                ).images
            else:
                generated_images = self.pipeline(
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
