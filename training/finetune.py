import os
import sys
import torch
import multiprocessing

# Windows multiprocessing fix — MUST be before everything
if __name__ == "__main__":
    multiprocessing.freeze_support()

sys.path.insert(0, "F:/naveen/AGI_Start")
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig
from pathlib import Path

def main():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    MODEL_NAME = "unsloth/mistral-7b-instruct-v0.3-bnb-4bit"
    OUTPUT_DIR = "F:/naveen/AGI_Start/training/navix_model"
    DATA_PATH  = "F:/naveen/AGI_Start/training/data/navix_conversations.jsonl"

    # load model
    print("Loading model...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=512,
        dtype=None,
        load_in_4bit=True,
    )

    # add LoRA
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    print(f"Trainable params: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")

    # load dataset
    dataset = load_dataset("json", data_files=DATA_PATH, split="train")
    print(f"Training samples: {len(dataset)}")

    # TRL 0.24+: max_seq_length removed from SFTTrainer — set on tokenizer instead
    tokenizer.model_max_length = 512

    # training config — num_proc=1 for Windows
    training_args = SFTConfig(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        num_train_epochs=3,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=5,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        report_to="none",
        dataset_text_field="text",
        dataset_num_proc=1,    # ← Windows fix
        dataloader_num_workers=0,  # ← Windows fix
    )

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=dataset,
        args=training_args,
    )

    print("Starting training...")
    trainer.train()
    print("Training complete!")

    # save
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"Model saved: {OUTPUT_DIR}")

    # convert to GGUF for Ollama
    print("Converting to GGUF...")
    model.save_pretrained_gguf(
        OUTPUT_DIR + "_gguf",
        tokenizer,
        quantization_method="q4_k_m"
    )
    print(f"GGUF saved: {OUTPUT_DIR}_gguf")

if __name__ == "__main__":
    main()