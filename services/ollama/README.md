# Ollama - Local LLM Service

Run large language models locally on your Mac mini M4.

## Why Ollama?

- **No API costs**: Free inference vs $0.002-0.01 per 1K tokens
- **Privacy**: Data never leaves your machine
- **Speed**: ~25-35 tok/s for 7B models
- **Offline**: Works without internet

## Installation

### On Mac mini:
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

## Recommended Models (16GB RAM)

### Week 1 Testing Plan

Test these models to find your preference:

#### 1. Llama 3.2 3B (Fast, Basic)
```bash
ollama pull llama3.2:3b
ollama run llama3.2:3b
```
- **Speed**: ~50 tok/s
- **RAM**: ~4GB
- **Use**: Quick questions, simple tasks

#### 2. Qwen 2.5 7B (Balanced - Recommended)
```bash
ollama pull qwen2.5:7b
ollama run qwen2.5:7b
```
- **Speed**: ~28-35 tok/s
- **RAM**: ~6GB
- **Use**: Daily driver, coding, analysis

#### 3. Gemma 2 12B Q4 (Quality, Slower)
```bash
ollama pull gemma2:12b-instruct-q4_K_M
ollama run gemma2:12b-instruct-q4_K_M
```
- **Speed**: ~17 tok/s
- **RAM**: ~10GB
- **Use**: When quality > speed

### Performance Testing

For each model, test:
```bash
# Test 1: Code generation
ollama run <model> "Write a Python function to find prime numbers"

# Test 2: Analysis
ollama run <model> "Explain the difference between async/await and callbacks"

# Test 3: Complex reasoning
ollama run <model> "Design a database schema for a blog with users, posts, and comments"
```

Note:
- Tokens per second
- Subjective quality
- RAM usage (Activity Monitor)
- Feels responsive?

## Daily Usage

### Via API
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:7b",
  "prompt": "Your prompt here",
  "stream": false
}'
```

### From Claude Code
Create a skill that queries local LLM for specific tasks (e.g., code review, brainstorming).

### Remote Access (via Tailscale)
```bash
# On laptop (after Tailscale setup)
curl http://mac-mini-hostname:11434/api/generate -d '{
  "model": "qwen2.5:7b",
  "prompt": "Your prompt here"
}'
```

## Resource Usage

Monitor Ollama's impact:
```bash
# While running a model
../monitoring/resources.sh
```

Typical usage:
- **Idle**: 0 bytes RAM (not running)
- **Loaded**: 6-10GB RAM (model in memory)
- **Active**: +1-2GB during inference

## Cost Comparison

**Ollama (Local)**:
- Cost: $0 per query
- Latency: ~1-3s for 100 tokens
- Quality: Good (7B models)

**Claude API**:
- Cost: ~$0.001-0.01 per query
- Latency: ~500ms-2s
- Quality: Excellent

**ROI Calculation**:
If you make 100+ queries per day:
- API cost: ~$30-100/month
- Ollama cost: ~$2/month (electricity)
- Savings: ~$28-98/month
- **ROI**: Pays for Mac mini in ~6-12 months

## Models to Avoid (16GB)

❌ **Don't try these on 16GB**:
- Llama 3 70B (needs 64GB+)
- Mixtral 8x7B full precision (needs 32GB+)
- Qwen 2.5 32B (will swap heavily)

If you try a model and it swaps to disk (very slow), it's too big!

## Troubleshooting

### Model loads but is very slow
- Check Activity Monitor → Memory Pressure
- If red/yellow: Model too big for RAM
- Solution: Use smaller model or Q4 quantization

### "Connection refused" error
```bash
# Check if Ollama is running
pgrep ollama

# If not, start it
ollama serve &
```

### Running out of disk space
```bash
# List all models
ollama list

# Remove unused models
ollama rm <model-name>
```

## Week 1 Deliverables

By end of Week 1, document in `docs/week-1.md`:
- [ ] Which model performed best?
- [ ] Tokens per second for each model
- [ ] RAM usage patterns
- [ ] Quality assessment (subjective)
- [ ] Will you use this daily?
- [ ] Cost savings estimate

## Next Steps

- **Week 2**: Set up remote access via Tailscale
- **Week 3**: Create Claude Code skill that uses local LLM
- **Week 4**: Evaluate if local LLM is worth keeping running

---

**Status**: Not Started
**Model Choice**: TBD
**Daily Use**: TBD
