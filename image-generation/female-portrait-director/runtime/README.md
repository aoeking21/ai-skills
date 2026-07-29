# female-portrait-director Runtime

This directory turns the Markdown Skill into a small executable pipeline:

```text
knowledge base
  -> prompt builder
  -> identity-lock contract validator
  -> image-model adapter
  -> generation pipeline
  -> image/prompt artifact + manifest
```

## Components

- `prompt_builder.py`: reads the Route and Overlay registries, selects one implemented Route, loads the relevant rule paths, and builds a model-ready positive/negative prompt package.
- `identity_lock.py`: validates authorization, reference-file integrity, identity-lock prompt propagation, and output-file integrity. It does **not** perform biometric identification; final facial similarity is marked for manual review.
- `adapters.py`: includes a dependency-free dry-run adapter and an optional OpenAI Responses image adapter.
- `pipeline.py`: executes the full sequence and writes a JSON manifest containing the request, selected Route/Overlay, loaded rules, validation reports, adapter metadata, and output location.

## 1. Safe dry run

```bash
cd image-generation/female-portrait-director/runtime
python -m venv .venv
source .venv/bin/activate
pip install -e .

fpd-runtime generate \
  --request examples/beach_identity_request.json \
  --adapter dry-run
```

The dry run does not contact any external service. It writes:

```text
examples/outputs/beach-identity.prompt.json
examples/outputs/beach-identity.manifest.json
```

Before running the example, copy an authorized adult reference photo to:

```text
examples/reference.jpg
```

## 2. Real image generation through OpenAI

Install the optional SDK and provide an API key through the environment. Never commit API keys.

```bash
pip install -e ".[openai]"
export OPENAI_API_KEY="..."

fpd-runtime generate \
  --request examples/beach_identity_request.json \
  --adapter openai
```

Optional environment settings:

```bash
export OPENAI_RESPONSE_MODEL="gpt-5"
export OPENAI_IMAGE_MODEL="gpt-image-1"
export OPENAI_IMAGE_SIZE="1024x1536"
export OPENAI_IMAGE_QUALITY="high"
```

The API adapter sends the authorized reference image as a high-detail input image, requests high input fidelity, decodes the returned `image_generation_call`, and writes the PNG plus the manifest.

## Request format

```json
{
  "task": "海边日系明艳生活方式摄影",
  "requirements": ["9:16", "完整全身", "动态抓拍", "真实摄影"],
  "aspect_ratio": "9:16",
  "identity_reference": "reference.jpg",
  "identity_authorized": true,
  "output_dir": "outputs",
  "output_name": "beach-identity"
}
```

`identity_authorized` must be `true` whenever `identity_reference` is supplied. The validator fails closed if the reference is missing, empty, unsupported, or not explicitly authorized.

## Tests

```bash
python -m unittest discover -s tests -v
```

The CI test suite uses only the dry-run adapter. It never consumes image credits and never requires secrets.

## Current boundary

This runtime verifies the **identity-lock contract**, not biometric identity. It guarantees that the reference is authorized and propagated through the prompt and adapter request, and that the output is present and auditable. A person must still visually approve identity similarity before publication.
