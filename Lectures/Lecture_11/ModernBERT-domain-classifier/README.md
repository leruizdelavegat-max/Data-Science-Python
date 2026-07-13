---
library_name: transformers
license: apache-2.0
base_model: answerdotai/ModernBERT-base
tags:
- generated_from_trainer
metrics:
- f1
model-index:
- name: ModernBERT-domain-classifier
  results: []
---

<!-- This model card has been generated automatically according to the information the Trainer had access to. You
should probably proofread and complete it, then remove this comment. -->

# ModernBERT-domain-classifier

This model is a fine-tuned version of [answerdotai/ModernBERT-base](https://huggingface.co/answerdotai/ModernBERT-base) on an unknown dataset.
It achieves the following results on the evaluation set:
- Loss: 0.5135
- F1: 0.9309

## Model description

More information needed

## Intended uses & limitations

More information needed

## Training and evaluation data

More information needed

## Training procedure

### Training hyperparameters

The following hyperparameters were used during training:
- learning_rate: 5e-05
- train_batch_size: 8
- eval_batch_size: 8
- seed: 42
- optimizer: Use adamw_torch_fused with betas=(0.9,0.999) and epsilon=1e-08 and optimizer_args=No additional optimizer arguments
- lr_scheduler_type: linear
- num_epochs: 5

### Training results

| Training Loss | Epoch | Step | Validation Loss | F1     |
|:-------------:|:-----:|:----:|:---------------:|:------:|
| 1.4074        | 1.0   | 113  | 0.4462          | 0.8683 |
| 0.3511        | 2.0   | 226  | 0.5212          | 0.9411 |
| 0.1377        | 3.0   | 339  | 0.4445          | 0.9440 |
| 0.0533        | 4.0   | 452  | 0.5057          | 0.9309 |
| 0.0151        | 5.0   | 565  | 0.5135          | 0.9309 |


### Framework versions

- Transformers 4.48.0.dev0
- Pytorch 2.7.1+cu118
- Datasets 3.1.0
- Tokenizers 0.21.4
