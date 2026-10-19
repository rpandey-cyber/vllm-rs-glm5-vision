# vllm-rs-glm5-vision

A patched `vllm-rs` (vLLM's Rust frontend) that accepts `image_url` content for
GLM-5.3 (`model_type: glm5_next`), for example `nvidia/GLM-5.3-Flash-NVFP4`.

Stock `vllm-rs` has no `glm5_next` entry in `llm-multimodal`'s model registry, so with
`VLLM_USE_RUST_FRONTEND=1` image requests fail with HTTP 400
`unsupported multimodal content: image_url` (ESC-27064).

## What is in here

| File | What it is |
|------|-----------|
| `vllm-rs` (release v0.1.0) | Linux x86_64 binary for vLLM `385dce36b` (0.28.1rc1.dev580, the `glm53-flash` image). |
| `llm-multimodal-glm5_next.patch` | Its patch, against `smg-project/llm-multimodal` at `74f64753e040ade87c9d7f4bb0ad2f4dd7764652`. |
| `vllm-rs-0.32.0` (release v0.2.0) | Linux x86_64 binary for vLLM **v0.32.0** (`vllm/vllm-openai:v0.32.0`). sha256 `a240f0a28d4b0b852d11041811f3f3b9550b98fb21de36d2099b80fa520f86ae`. |
| `llm-multimodal-glm5_next-vllm-0.32.0.patch` | Its patch, against `llm-multimodal` at `f0985ef65967615db2c79279aa07818499301bfd` (the revision vLLM v0.32.0 pins). |

The patch is based on [llm-multimodal PR #14](https://github.com/smg-project/llm-multimodal/pull/14)
(by thuanpham582002), re-anchored to the pinned revision, with a compile fix, and with
`<|begin_of_image|>` / `<|end_of_image|>` emitted around each image's tokens so the prompt
matches the Python frontend.

## Use

Replace the binary in the image, or point vLLM at it:

```sh
curl -fL -o /tmp/vllm-rs <release asset URL>
echo "<sha256>  /tmp/vllm-rs" | sha256sum -c -
chmod +x /tmp/vllm-rs
export VLLM_USE_RUST_FRONTEND=1
export VLLM_RUST_FRONTEND_PATH=/tmp/vllm-rs
```

Each binary is only valid for the vLLM build listed above. For other vLLM versions, rebuild with the patch.

## Rebuild

```sh
git clone https://github.com/vllm-project/vllm && git -C vllm checkout 385dce36b
git clone https://github.com/smg-project/llm-multimodal
git -C llm-multimodal checkout 74f64753e040ade87c9d7f4bb0ad2f4dd7764652
git -C llm-multimodal apply ../llm-multimodal-glm5_next.patch
printf '\n[patch."https://github.com/smg-project/llm-multimodal"]\nllm-multimodal = { path = "../llm-multimodal" }\n' >> vllm/rust/Cargo.toml
cd vllm/rust && VLLM_RS_BUILD_VERSION=0.28.1rc1.dev580+g385dce36b \
  cargo build --release --bin vllm-rs --manifest-path src/cmd/Cargo.toml --features native-tls-vendored
```

## Known gap

The Python frontend adds one newline token after each image; this build does not
(1 token per image). Output quality is unaffected in testing.

## License

Apache-2.0, same as vLLM and llm-multimodal.
