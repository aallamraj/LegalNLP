# Legal NLP 
#
# zero_shot_label.py

import argparse
import os
import re
import sys
import csv
import nltk
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from file_utils import read_file

# Legal sentence labels for zero-shot classification
LABELS = [
    "Fact",
    "Issues",
    "Argument Petitioner",
    "Argument Respondent",
    "Statute",
    "Dissent",
    "Ruling by Lower Court",
    "Ratio of Decision",
    "Ruling by Present",
    "Court",
    "None",
]
LABELS_STR = ", ".join(LABELS)


def get_sentences(text: str):
    """
    Split text into sentences
    :param text: Text to convert to sentences
    :return: List of sentences
    """
    text = text.strip()
    if not text:
        return []

    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt", quiet=True)
    return nltk.sent_tokenize(text)


def get_sentences_regex(text: str):
    """
    Not used but in case needed
    Split text into sentences using regex.
    :param text: Text to convert to sentences
    :return: List of sentences
    """
    pattern = r"(?<=[.!?])\s+(?=[A-Z])"
    parts = re.split(pattern, text)
    return [s.strip() for s in parts if s.strip()]


def normalize_label(raw: str) -> str:
    """
    Map model output to one of the allowed labels (case-insensitive, strip).
    :param raw: raw label to normalize
    """
    raw = raw.strip()
    if not raw:
        return "None"
    raw_lower = raw.lower()
    for label in LABELS:
        if label.lower() == raw_lower or label.lower() in raw_lower:
            return label
    if "ruling by present" in raw_lower:
        return "Ruling by Present"
    if "ratio of decision" in raw_lower or "ratio" in raw_lower:
        return "Ratio of Decision"
    if "argument petitioner" in raw_lower:
        return "Argument Petitioner"
    if "argument respondent" in raw_lower:
        return "Argument Respondent"
    if "ruling by lower" in raw_lower:
        return "Ruling by Lower Court"
    return "None"


def build_chat_prompt(tokenizer, sentence: str) -> str:
    """
    Build a single chat-formatted prompt for one sentence.
    :param tokenizer:
    :param sentence:
    :return: a single sentence-formatted prompt
    """
    prompt = (
        "You are a legal document annotator. Classify the following sentence from a legal judgment "
        "into exactly one of these labels: " + LABELS_STR + ".\n\n"
        "Reply with only the label, nothing else.\n\n"
        f"Sentence: {sentence}\n\nLabel:"
    )

    messages = [{"role": "user", "content": prompt}]
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )


def run_zero_shot_single_transformers(model, tokenizer, sentence: str, device: str, max_new_tokens: int = 16):
    """
    Transformers fallback without vLLM (slower than vLLM, but works on CPU/MPS). Used for testing
    :param model:
    :param tokenizer:
    :param sentence:
    :param device:
    :param max_new_tokens:
    """
    text = build_chat_prompt(tokenizer, sentence)
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=1024).to(device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
    )

    new_tokens = outputs[0][inputs["input_ids"].shape[1] :]
    reply = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
    return normalize_label(reply)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("input_file", nargs="?", default="./data/bench=hcaurdb/text/HCBM030000012025_1_2025-02-04.txt", help="Debud input file path")
    parser.add_argument("-o", "--output", default=None, help="Optional output path")  # Used only for debug
    # parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct", help="Hugging Face model name")
    parser.add_argument("--model", default="Qwen/Qwen3.5-4B", help="Hugging Face model name")
    parser.add_argument("--max-new-tokens", type=int, default=16, help="Max tokens to generate for label")
    parser.add_argument("--max-sentences", type=int, default=None, help="Process only first N sentences")
    parser.add_argument("--no-nltk", action="store_true", help="Use regex splitting instead of NLTK")
    args = parser.parse_args()

    if args.input_file is None:
        # TODO traverse directory and read all the files
        data_root = os.path.join(os.path.dirname(__file__), "data")
        for root, _dirs, files in os.walk(data_root):
            for f in sorted(files):
                if f.endswith(".txt") and "regions" not in f and "name_list" not in f:
                    args.input_file = os.path.join(root, f)
                    break
            if args.input_file:
                break
        if not args.input_file:
            print("No input file given and no .txt file found under data/.", file=sys.stderr)
            sys.exit(1)
        print(f"Using input file: {args.input_file}", file=sys.stderr)
    else:
        args.input_file = os.path.abspath(args.input_file)
        if not os.path.isfile(args.input_file):
            print(f"File not found: {args.input_file}", file=sys.stderr)
            sys.exit(1)

    try:
        text = read_file(args.input_file)
    except FileExistsError:
        print(f"Cannot read file (must be .txt): {args.input_file}", file=sys.stderr)
        sys.exit(1)

    # TODO do something about nltk flag if needed or not
    sentences = get_sentences(text)
    if args.max_sentences is not None:
        sentences = sentences[: args.max_sentences]
    if not sentences:
        print("No sentences found.", file=sys.stderr)
        sys.exit(0)

    # Load tokenizer (used for chat template prompt formatting)
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)

    # Fall back to Transformers if vLLM/CUDA not available.
    llm = None
    sampling_params = None
    vllm_err = None
    has_cuda = torch.cuda.is_available()

    if has_cuda:
        from vllm import LLM, SamplingParams
        llm = LLM(model=args.model, trust_remote_code=True)
        sampling_params = SamplingParams(
            temperature=0.0,
            top_p=1.0,
            max_tokens=args.max_new_tokens,
            stop=["\n"],
        )

    results = []
    if llm is not None and sampling_params is not None:
        print(f"Using vLLM for inference: {args.model}", file=sys.stderr)
        prompts = [build_chat_prompt(tokenizer, s) for s in sentences]
        outputs = llm.generate(prompts, sampling_params)
        # vLLM returns outputs in the same order as the input prompts.
        for i, (sent, out) in enumerate(zip(sentences, outputs)):
            reply = (out.outputs[0].text if out.outputs else "").strip()
            label = normalize_label(reply)
            results.append((sent, label))
            if args.output is None:
                print(f"{i+1}\t{label}\t{sent[:80]}{'...' if len(sent) > 80 else ''}")
    else:
        if not has_cuda:
            print("CUDA not available; falling back to Transformers.", file=sys.stderr)
        elif vllm_err is not None:
            print(f"vLLM init failed ({type(vllm_err).__name__}: {vllm_err}); falling back to Transformers.", file=sys.stderr)

        device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"Loading {args.model} on {device} (Transformers fallback)...", file=sys.stderr)
        model = AutoModelForCausalLM.from_pretrained(
            args.model,
            torch_dtype=torch.float16 if device != "cpu" else torch.float32,
            device_map="auto" if device != "cpu" else None,
            trust_remote_code=True,
        )
        if device != "cpu" and getattr(model, "device_map", None) is None:
            model = model.to(device)

        for i, sent in enumerate(sentences):
            label = run_zero_shot_single_transformers(
                model,
                tokenizer,
                sent,
                device,
                max_new_tokens=args.max_new_tokens,
            )
            results.append((sent, label))
            if args.output is None:
                print(f"{i+1}\t{label}\t{sent[:80]}{'...' if len(sent) > 80 else ''}")

            if i == 10:
                exit(0)

    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["sentence", "label"])
            for sent, label in results:
                w.writerow([sent, label])
        print(f"Wrote {len(results)} rows to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
