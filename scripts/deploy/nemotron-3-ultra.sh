#!/usr/bin/env bash
# =============================================================================
# NVIDIA Nemotron-3-Ultra-550B-A55B-BF16 — reference deployment blocks
# =============================================================================
# THIS IS A REFERENCE FILE, NOT A RUN-TOP-TO-BOTTOM SCRIPT.
# Pick ONE serving block (vLLM single-node, vLLM multi-node, SGLang, or
# TRT-LLM), copy it, and run it. The API-client and OpenCode sections at the
# bottom apply to whichever backend you launched.
#
# Baseline values are taken verbatim from the NVIDIA model card (authoritative).
# The only mechanical change applied everywhere is the trailing-whitespace fix
# after backslash line-continuations (the original had stray spaces after "\"
# on the --mamba-* lines, which breaks bash continuation).
#
# Inline "# DISCREPANCY:" comments mark spots where another NVIDIA source
# (vLLM blog / build.nvidia.com / advanced deployment guide / the TRT-LLM block
# in this same card) uses a different value. They are left at the card value;
# flip them deliberately if you hit the described symptom.
#
# Prereqs (all backends):
#   export MODEL_CKPT=/abs/path/to/checkpoint    # shared FS, IDENTICAL path on every node
#   ls "$MODEL_CKPT"/config.json "$MODEL_CKPT"/*.safetensors   # must resolve
# =============================================================================


# =============================================================================
# BLOCK 1 — vLLM, single node, 8x B200 (BF16)
# =============================================================================
docker run -d --name nemotron-ultra-vllm \
  --gpus all \
  --ipc=host \
  --network=host \
  --shm-size=16g \
  --ulimit memlock=-1 \
  --ulimit stack=67108864 \
  -v "$MODEL_CKPT":/model:ro \
  -e VLLM_WORKER_MULTIPROC_METHOD=spawn \
  -e SAFETENSORS_FAST_GPU=1 \
  -e NVIDIA_TF32_OVERRIDE=1 \
  -e VLLM_LOGGING_LEVEL=INFO \
  vllm/vllm-openai:v0.22.0 \
  /model \
  --host 0.0.0.0 \
  --port 8000 \
  --served-model-name nvidia/nemotron-3-ultra \
  --trust-remote-code \
  --tensor-parallel-size 8 \
  --enable-expert-parallel \
  --dtype bfloat16 \
  --max-model-len 262144 \
  --gpu-memory-utilization 0.90 \
  --max-num-seqs 16 \
  --max-num-batched-tokens 32768 \
  --enable-chunked-prefill \
  --enable-prefix-caching \
  --reasoning-parser nemotron_v3 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --mamba-ssm-cache-dtype float16 \
  --mamba-backend flashinfer \
  --enable-mamba-cache-stochastic-rounding \
  --mamba-cache-philox-rounds 5 \
  --speculative-config '{"method": "nemotron_h_mtp", "num_speculative_tokens": 5}' \
  --model-loader-extra-config '{"enable_multithread_load": true, "num_threads": 96}'
# DISCREPANCY (reasoning-parser): card uses "nemotron_v3" here; the GGUF card
#   uses "nemotron_3" and the TRT-LLM block below uses "nano-v3". If reasoning
#   traces don't separate from the final answer, this is the first thing to flip.
# DISCREPANCY (mamba-ssm-cache-dtype): card uses float16 + the two stochastic-
#   rounding flags below (a coherent pairing — rounding compensates for fp16).
#   NVIDIA's advanced deployment guide instead uses float32 for the SSM cache at
#   all precisions; if you switch to float32, DROP the two stochastic-rounding
#   flags (they exist only to make low-precision cache viable).
# NOTE (KV cache): this single-node block has no --kv-cache-dtype, so KV runs
#   BF16. The multi-node block below sets fp8 (≈halves KV memory). Intentional
#   asymmetry in the card — match them if you want parity.
# To use up to 1M context: add  -e VLLM_ALLOW_LONG_MAX_MODEL_LEN=1  and set
#   --max-model-len 1048576.


# =============================================================================
# BLOCK 2 — vLLM, multi-node via Ray (label: 2x 4xGB300)
# =============================================================================
# Bring up Ray FIRST (head on node 0, workers join), then run `vllm serve` on
# the HEAD node only.
#
# --- Ray head (node 0) ---
#   export RAY_HEAD_IP=<node0_ip>
#   export RAY_PORT=6379
#   ray start --head --port="$RAY_PORT"
#
# --- Ray worker (each other node) ---
#   export RAY_ADDRESS="$RAY_HEAD_IP:$RAY_PORT"
#   ray start --address="$RAY_ADDRESS" --block
#
# --- Verify on head BEFORE serving: GPU count must equal TP x PP (=8 here) ---
#   ray status
#
# Run on the Ray HEAD node only:
vllm serve "$MODEL_CKPT" \
  --host 0.0.0.0 \
  --port 8000 \
  --served-model-name nvidia/nemotron-3-ultra \
  --tensor-parallel-size 8 \
  --distributed-executor-backend ray \
  --trust-remote-code \
  --dtype bfloat16 \
  --gpu-memory-utilization 0.90 \
  --max-model-len 262144 \
  --max-num-seqs 256 \
  --max-num-batched-tokens 32768 \
  --enable-chunked-prefill \
  --enable-prefix-caching \
  --reasoning-parser nemotron_v3 \
  --mamba-ssm-cache-dtype float16 \
  --mamba-backend flashinfer \
  --enable-mamba-cache-stochastic-rounding \
  --mamba-cache-philox-rounds 5 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --speculative-config '{"method": "nemotron_h_mtp", "num_speculative_tokens": 5}' \
  --kv-cache-dtype fp8 \
  --model-loader-extra-config '{"enable_multithread_load": true, "num_threads": 96}' \
  --compilation-config '{"pass_config": {"fuse_allreduce_rms": false}}' \
  --distributed-timeout-seconds 3600
# SIZING (read before running): "2x 4xGB300" = 8 GPUs across 2 nodes, but this
#   command is flat --tensor-parallel-size 8 with NO pipeline parallelism, i.e.
#   TP=8 spanning both nodes. That is correct ONLY if the two nodes share one
#   NVLink domain (GB300 NVL). If the nodes are linked by InfiniBand, flat
#   cross-node TP=8 bottlenecks on every all-reduce — switch to:
#       --tensor-parallel-size 4 --pipeline-parallel-size 2
#   (TP=4 within each node, PP=2 across nodes).
# NOTE: GB300 is Blackwell, so the TRT-LLM path (Block 4) is available and is
#   often the throughput winner for this architecture — worth benchmarking.
# Useful env vars:
#   VLLM_FLASHINFER_ALLREDUCE_BACKEND=trtllm
#   VLLM_FLASHINFER_MOE_BACKEND=latency      # TRTLLM-Gen
#   VLLM_FLASHINFER_MOE_BACKEND=throughput   # CUTLASS
# 1M context: set VLLM_ALLOW_LONG_MAX_MODEL_LEN=1 and --max-model-len 1048576.


# =============================================================================
# BLOCK 3 — SGLang, single node, 8x B200 (BF16; chunked prefill + MTP on)
# =============================================================================
#   docker pull lmsysorg/sglang:v0.5.12.post1
docker run -d --name nemotron-ultra-sglang \
  --gpus all \
  --cap-add SYS_NICE \
  --ipc=host \
  --network=host \
  --shm-size=16g \
  --ulimit memlock=-1 \
  --ulimit stack=67108864 \
  -v "$MODEL_CKPT":/model:ro \
  -e SAFETENSORS_FAST_GPU=1 \
  -e NVIDIA_TF32_OVERRIDE=1 \
  -e SGLANG_DISABLE_DEEP_GEMM=1 \
  lmsysorg/sglang:v0.5.12.post1 \
  python3 -m sglang.launch_server \
  --model-path /model \
  --host 0.0.0.0 \
  --port 8000 \
  --served-model-name nvidia/nemotron-3-ultra \
  --tp-size 8 \
  --ep-size 8 \
  --context-length 262144 \
  --mem-fraction-static 0.85 \
  --chunked-prefill-size 32768 \
  --fp8-gemm-backend triton \
  --moe-runner-backend triton \
  --mamba-scheduler-strategy no_buffer \
  --disable-piecewise-cuda-graph \
  --reasoning-parser nemotron_v3 \
  --tool-call-parser qwen3_coder \
  --speculative-algorithm EAGLE \
  --speculative-num-steps 5 \
  --speculative-eagle-topk 1 \
  --speculative-num-draft-tokens 5 \
  --trust-remote-code \
  --log-level info
# 1M context: set SGLANG_ALLOW_OVERWRITE_LONGER_CONTEXT_LEN=1 and
#   --context-length 1048576.
# Tool calls + reasoning on SGLang REQUIRE explicit chat-template kwargs in the
#   request body: {"enable_thinking": true, "force_nonempty_content": true}
#   (see API CLIENT block below).


# =============================================================================
# BLOCK 4 — TensorRT-LLM, 8x B200 (Blackwell ONLY: B200/B300/GB200/GB300)
# =============================================================================
# Hopper (H100/H200) is NOT yet supported by TRT-LLM for this model.
#   docker pull nvcr.io/nvidia/tensorrt-llm/release:1.3.0rc17
#
# Step 1 — write the extra API config next to where you'll launch:
cat > ./extra-llm-api-config.yml << 'EOF'
backend: pytorch
trust_remote_code: true
tensor_parallel_size: 8
pipeline_parallel_size: 1
context_parallel_size: 1
gpus_per_node: 8
moe_expert_parallel_size: 1
disable_overlap_scheduler: false

cuda_graph_config:
  enable_padding: true
  max_batch_size: 256

enable_chunked_prefill: true
enable_attention_dp: false
max_batch_size: 256
max_seq_len: null
max_num_tokens: 32768
num_postprocess_workers: 4

kv_cache_config:
  enable_block_reuse: false
  max_tokens: null
  max_attention_window: null
  sink_token_length: null
  free_gpu_memory_fraction: 0.75
  host_cache_size: null
  cross_kv_cache_fraction: null
  secondary_offload_min_priority: null
  event_buffer_max_size: 0
  attention_dp_events_gather_period_ms: 5
  enable_partial_reuse: true
  copy_on_partial_reuse: true
  use_uvm: false
  max_gpu_total_bytes: 0
  iteration_stats_interval: 1
  dtype: fp8
  tokens_per_block: 32
  mamba_state_cache_interval: 256
  use_kv_cache_manager_v2: false
  max_util_for_resume: 0.95

moe_config:
  backend: TRTLLM
  max_num_tokens: null
  load_balancer: null
  disable_finalize_fusion: false
  use_low_precision_moe_combine: false
EOF
#
# Step 2 — serve. Replace <bf16_ckpt> with "$MODEL_CKPT" and set MODEL_DIR so
#   the chat template resolves:
#   export MODEL_DIR="$MODEL_CKPT"
TLLM_ALLOW_LONG_MAX_MODEL_LEN=1 trtllm-serve \
  "$MODEL_CKPT" \
  --max_batch_size 256 \
  --tp_size 8 --ep_size 1 \
  --max_num_tokens 32768 \
  --trust_remote_code \
  --reasoning_parser nano-v3 \
  --tool_parser qwen3_coder \
  --chat_template "$MODEL_DIR"/chat_template.jinja \
  --extra_llm_api_options extra-llm-api-config.yml
# DISCREPANCY (reasoning_parser): TRT-LLM uses "nano-v3" here vs "nemotron_v3"
#   in the vLLM/SGLang blocks. This is the card's own value for TRT-LLM — keep
#   it for this backend.
# Long context: TLLM_ALLOW_LONG_MAX_MODEL_LEN=1 is already set; add
#   --max_seq_len <seq_len> for the desired max context.
# MTP note: the speculative/MTP config carries over unchanged; on rc16
#   max_draft_len is authoritative and num_nextn_predict_layers is deprecated.


# =============================================================================
# API CLIENT (OpenAI-compatible) — works against any backend above
# =============================================================================
# CODING AGENTS: add  extra_body={"chat_template_kwargs": {"force_nonempty_content": True}}
# to the call, or agentic flows can receive empty content blocks.
#
# python3 - << 'PY'
# from openai import OpenAI
# client = OpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")
# MODEL = "nvidia/nemotron-3-ultra"
#
# # --- Reasoning ON (default) ---
# r = client.chat.completions.create(
#     model=MODEL,
#     messages=[{"role": "user", "content": "Write a haiku about GPUs"}],
#     max_tokens=16000, temperature=1.0, top_p=0.95,
#     extra_body={"chat_template_kwargs": {"enable_thinking": True}},
# )
# print(r.choices[0].message.content)
#
# # --- Reasoning OFF (fastest smoke test: confirms parser + chat template) ---
# r = client.chat.completions.create(
#     model=MODEL,
#     messages=[{"role": "user", "content": "What is the capital of Japan?"}],
#     max_tokens=16000, temperature=1.0, top_p=0.95,
#     extra_body={"chat_template_kwargs": {"enable_thinking": False}},
# )
# print(r.choices[0].message.content)
#
# # --- Medium-effort reasoning (fewer reasoning tokens than full thinking) ---
# r = client.chat.completions.create(
#     model=MODEL,
#     messages=[{"role": "user", "content": "What is the capital of Japan?"}],
#     max_tokens=16000, temperature=1.0, top_p=0.95,
#     extra_body={"chat_template_kwargs": {"enable_thinking": True, "medium_effort": True}},
# )
# print(r.choices[0].message.content)
#
# # --- Tool calling WITH reasoning (SGLang needs force_nonempty_content) ---
# r = client.chat.completions.create(
#     model=MODEL,
#     messages=[{"role": "user", "content": "What's the weather in New York?"}],
#     tools=[{
#         "type": "function",
#         "function": {
#             "name": "get_weather",
#             "description": "Get the current weather for a city.",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "city": {"type": "string"},
#                     "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
#                 },
#                 "required": ["city"],
#             },
#         },
#     }],
#     tool_choice="required",
#     max_tokens=256, temperature=1.0, top_p=0.95,
#     extra_body={"chat_template_kwargs": {"enable_thinking": True, "force_nonempty_content": True}},
# )
# print(r.choices[0].message.tool_calls)
# PY


# =============================================================================
# OpenCode — ~/.config/opencode/opencode.json (all backends default to :8000)
# =============================================================================
# {
#     "$schema": "https://opencode.ai/config.json",
#     "model": "local/nvidia-nemotron-3-ultra",
#     "provider": {
#         "local": {
#             "npm": "@ai-sdk/openai-compatible",
#             "name": "local_backend",
#             "options": {
#                 "baseURL": "http://localhost:8000/v1",
#                 "apiKey": "EMPTY"
#             },
#             "models": {
#                 "nvidia-nemotron-3-ultra": {
#                     "name": "nvidia/nemotron-3-ultra",
#                     "limit": { "context": 1000000, "output": 32768 }
#                 }
#             }
#         }
#     },
#     "agent": {
#         "build": { "temperature": 1.0, "top_p": 0.95, "max_tokens": 32000 },
#         "plan":  { "temperature": 1.0, "top_p": 0.95, "max_tokens": 32000 }
#     }
# }
# =============================================================================
