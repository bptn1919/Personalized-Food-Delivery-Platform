import torch
import torch.nn as nn
from transformers import AutoModel

class PhoBERTMultiTask(nn.Module):
    def __init__(self, num_weights=3, num_issues=27, dropout=0.3):
        super().__init__()
        # ✅ Đúng repository
        self.bert = AutoModel.from_pretrained("Fsoft-AIC/videberta-xsmall")
        
        hidden_size = self.bert.config.hidden_size
        print(f"📊 Model hidden size: {hidden_size}")
        
        self.dropout = nn.Dropout(dropout)
        self.weight_classifier = nn.Linear(hidden_size, num_weights)
        self.issue_classifier = nn.Linear(hidden_size, num_issues)
    
    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids, attention_mask)
        # ✅ Đúng - dùng CLS token
        pooled = outputs.last_hidden_state[:, 0, :]
        pooled = self.dropout(pooled)
        return self.weight_classifier(pooled), self.issue_classifier(pooled)