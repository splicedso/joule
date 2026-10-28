"""Give an exported GGUF the stock file's tensor layout: a separate output.weight (a copy of token_embd.weight) and the
stock tensor order (output, output_norm, token_embd, then blk.N in numeric order, names alphabetical inside a block).

convert_hf_to_gguf.py writes a tied model (Qwen2.5 1.5B has tie_word_embeddings) with token_embd.weight only, 338 tensors
in alphabetical order (blk.10 before blk.2). llama-quantize then has no output tensor to give Q6_K and quantizes the shared
token_embd at Q6_K; the stock Qwen2.5-1.5B-Instruct Q4_0 has output.weight at Q6_K and token_embd at Q4_0 (339 tensors) and
decodes about 25% faster on the Vulkan build (results/general-halo-rft-1.5b.md). This script rewrites the F16 so that
llama-quantize produces the stock layout (with --output-tensor-type Q6_K --token-embedding-type Q4_0).

    python experiments/rft/untie_export.py IN.gguf OUT.gguf [REFERENCE.gguf]

With a reference GGUF, the output follows the reference's tensor order exactly (tensors the reference lacks go last, in
the stock rule's order) and the script fails if any reference tensor other than output.weight is missing from the input.
Metadata is copied unchanged. Memory: the input is memory-mapped, the output streamed; nothing else is loaded.
"""
import re
import sys

import gguf  # vendor/llama.cpp/gguf-py (uv run --with ./vendor/llama.cpp/gguf-py)

OUTPUT, EMBD = "output.weight", "token_embd.weight"


def stock_key(name):
    """Stock order: non-block tensors first (alphabetical: output.weight, output_norm.weight, token_embd.weight), then
    blocks by number, names alphabetical inside a block."""
    m = re.match(r"blk\.(\d+)\.(.*)", name)
    return (1, int(m.group(1)), m.group(2)) if m else (0, 0, name)


def main(src, dst, ref=None):
    reader = gguf.GGUFReader(src)
    tensors = {t.name: t for t in reader.tensors}
    if OUTPUT in tensors:
        sys.exit(f"{src} already has {OUTPUT}; nothing to untie")
    if EMBD not in tensors:
        sys.exit(f"{src} has no {EMBD}")
    names = list(tensors) + [OUTPUT]
    if ref:
        ref_names = [t.name for t in gguf.GGUFReader(ref).tensors]
        missing = [n for n in ref_names if n not in names]
        if missing:
            sys.exit(f"reference tensors missing from {src}: {missing[:5]}{'...' if len(missing) > 5 else ''}")
        extra = sorted((n for n in names if n not in ref_names), key=stock_key)
        if extra:
            print(f"not in the reference, appended: {extra}")
        order = ref_names + extra
    else:
        order = sorted(names, key=stock_key)

    arch = reader.fields[gguf.Keys.General.ARCHITECTURE].contents()
    writer = gguf.GGUFWriter(dst, arch=arch, endianess=reader.endianess)
    for field in reader.fields.values():
        if field.name == gguf.Keys.General.ARCHITECTURE or field.name.startswith("GGUF."):
            continue
        val_type = field.types[0]
        sub_type = field.types[-1] if val_type == gguf.GGUFValueType.ARRAY else None
        writer.add_key_value(field.name, field.contents(), val_type, sub_type=sub_type)

    def tensor_of(name):
        return tensors[EMBD if name == OUTPUT else name]

    for name in order:
        t = tensor_of(name)
        writer.add_tensor_info(name, t.data.shape, t.data.dtype, t.data.nbytes, t.tensor_type)
    writer.write_header_to_file()
    writer.write_kv_data_to_file()
    writer.write_ti_data_to_file()
    for name in order:
        writer.write_tensor_data(tensor_of(name).data, tensor_endianess=reader.endianess)
    writer.close()
    print(f"{dst}: {len(order)} tensors ({len(tensors)} in, {OUTPUT} added as a copy of {EMBD}, "
          f"{'reference order' if ref else 'stock order'})")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    main(*sys.argv[1:])
