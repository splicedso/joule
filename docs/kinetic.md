# Kinetic: a small model shaped by energy

Plan, 25 October 2026. Starts after Trace v1.

## Question

At a fixed parameter budget, which shape (width, depth, vocabulary) gives the lowest joules per correct answer on real hardware? Notes 6 and 12 found that small models pay more energy per weight, but the models measured differ in width, depth and vocabulary at once. Kinetic separates them by training the shapes ourselves.

## Prediction

At about 50M parameters, a wider and shallower model costs less energy per token than a deep narrow one at equal parameters, because decode on these machines is bound by memory reads and launch overhead per layer, not arithmetic. The quality cost of fewer layers is smaller than the energy saved, so the wide shape wins on joules per correct answer.

## Design

- **Four shapes at about 50M non-embedding parameters**, one vocabulary (Qwen2.5's, so tokenization is shared with our other models):
  - deep: 24 layers × 512 wide
  - base: 12 layers × 768 wide
  - wide: 6 layers × 1024 wide
  - widest: 4 layers × 1280 wide
- **Data:** the same 1B tokens for each, from FineWeb-Edu (ODC-BY), one epoch, identical order.
- **Training:** the Strix Halo, PyTorch on ROCm. At about 13 effective TFLOPS bf16, 50M parameters × 1B tokens × 6 is about 3e17 FLOPs, or roughly 6.5 hours per shape.
- **Quality:** held-out perplexity on FineWeb-Edu, plus a small task the models can learn (a held-out split of a synthetic arithmetic set), so "correct answer" is defined.
- **Energy:** each shape converted to GGUF (F16 and Q4_0) and measured with Phase, with the warm-up, on the M5 Pro and the Strix Halo. Decode mJ per token at batch 1 and 8.
- **Result:** joules per correct answer for each shape on each machine. The winning shape is Kinetic v1.

## Bar

Kinetic v1 beats the same-size `base` shape on joules per correct answer by at least 15% on both machines, with held-out perplexity within 5%.

## Limits known in advance

50M parameters is far below useful-assistant size; the result is about shape, measured where training is affordable. Whether it holds at 1B needs a second run.
