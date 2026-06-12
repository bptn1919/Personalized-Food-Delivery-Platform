import torch
import json
import os
import re
from transformers import AutoTokenizer
from phobert_model import PhoBERTMultiTask
from rule_engine import RuleEngine
from datetime import datetime
import uuid

class Predictor:
    def __init__(self, model_path="models/phobert_multitask_best.pth", device=None):
        """
        Khởi tạo predictor
        Args:
            model_path: Đường dẫn đến model đã train
            device: 'cuda' hoặc 'cpu'
        """
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
        
        print(f"📱 Device: {self.device}")
        
        # Load tokenizer
        print("📦 Loading tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained("Fsoft-AIC/videberta-xsmall")
        
        # Load model
        print("📦 Loading model...")
        self.model = PhoBERTMultiTask(num_weights=3, num_issues=27, dropout=0.3)
        
        # Load checkpoint
        checkpoint = torch.load(model_path, map_location=self.device)
        
        # Xử lý checkpoint (có thể là full checkpoint hoặc state_dict)
        if 'model_state_dict' in checkpoint:
            state_dict = checkpoint['model_state_dict']
        else:
            state_dict = checkpoint
        
        # Load state_dict
        self.model.load_state_dict(state_dict, strict=False)
        
        # 👇 QUAN TRỌNG: Ép model về float32 để tránh lỗi dtype
        self.model = self.model.float()
        
        self.model.to(self.device)
        self.model.eval()
        
        # Load rule engine (để dự đoán weight_rule)
        print("📦 Loading rule engine...")
        self.rule_engine = RuleEngine()
        
        # Mapping class -> weight
        self.class_to_weight = {0: 0.0, 1: 0.5, 2: 1.0}
        
        print("✅ Predictor ready!")
    
    def preprocess(self, comment):
        """Tiền xử lý comment"""
        comment = comment.strip()
        comment = re.sub(r'\s+', ' ', comment)  # Xóa khoảng trắng thừa
        return comment
    
    def predict_weight_model(self, comment):
        """Dự đoán weight bằng model ViDeBERTa"""
        comment = self.preprocess(comment)
        
        # Tokenize
        enc = self.tokenizer(
            comment,
            truncation=True,
            padding='max_length',
            max_length=128,
            return_tensors='pt'
        )
        
        input_ids = enc['input_ids'].to(self.device)
        attention_mask = enc['attention_mask'].to(self.device)
        
        # Predict
        with torch.no_grad():
            weight_logits, _ = self.model(input_ids, attention_mask)
            pred_class = torch.argmax(weight_logits, dim=1).item()
        
        weight = self.class_to_weight[pred_class]
        confidence = torch.softmax(weight_logits, dim=1)[0][pred_class].item()
        
        return weight, confidence, pred_class
    
    def predict_weight_rule(self, comment):
        """Dự đoán weight bằng rule engine"""
        comment = self.preprocess(comment)
        weight = self.rule_engine.classify_weight(comment)
        return weight
    
    def predict_issue(self, comment):
        """Dự đoán issue bằng rule engine"""
        comment = self.preprocess(comment)
        issue = self.rule_engine.classify_issue(comment)
        return issue
    
    def predict_combined(self, comment, use_rule_fallback=True):
        """
        Dự đoán kết hợp model + rule
        - Nếu confidence cao, dùng model
        - Nếu confidence thấp, dùng rule
        """
        weight_model, confidence, pred_class = self.predict_weight_model(comment)
        weight_rule = self.predict_weight_rule(comment)
        issue = self.predict_issue(comment)
        
        # Chiến lược kết hợp
        if use_rule_fallback and confidence < 0.7:
            # Confidence thấp, dùng rule
            final_weight = weight_rule
            method = "rule (fallback)"
        elif use_rule_fallback and weight_model != weight_rule:
            # Model và rule khác nhau, ưu tiên rule
            final_weight = weight_rule
            method = "rule (override)"
        else:
            final_weight = weight_model
            method = "model"
        
        return {
            'comment': comment,
            'weight_model': weight_model,
            'weight_rule': weight_rule,
            'final_weight': final_weight,
            'confidence': confidence,
            'pred_class': pred_class,
            'issue': issue,
            'method': method
        }
    
    def predict_batch(self, comments, use_rule_fallback=True):
        """Dự đoán batch nhiều comment"""
        results = []
        for comment in comments:
            result = self.predict_combined(comment, use_rule_fallback)
            results.append(result)
        return results
    
    def save_comment(self, comment, weight, issue, output_path="data/new_comments.json"):
        """Lưu comment mới vào file JSON (tự tạo nếu chưa có)"""
        
        # Tạo thư mục nếu chưa có
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Tạo record mới
        now = datetime.now()
        record = {
            "uid": str(uuid.uuid4()),
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S.%f+07"),
            "updated_at": now.strftime("%Y-%m-%d %H:%M:%S.%f+07"),
            "comment": comment,
            "weight": weight,
            "issue": issue,
            "source": "predicted",
            "predicted_at": now.isoformat()
        }
        
        # Đọc file cũ nếu có
        if os.path.exists(output_path):
            with open(output_path, 'r', encoding='utf-8') as f:
                try:
                    records = json.load(f)
                except:
                    records = []
        else:
            records = []
            print(f"📁 Creating new file: {output_path}")
        
        # Thêm record mới
        records.append(record)
        
        # Lưu lại
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Saved comment to {output_path} (total: {len(records)} comments)")
        return record


def main():
    print("=" * 60)
    print("🍽️ PHOBERT SENTIMENT PREDICTOR")
    print("=" * 60)
    
    # Khởi tạo predictor
    predictor = Predictor(model_path="models/phobert_multitask_best.pth")
    
    print("\n📝 Enter your comments (type 'quit' to exit):")
    print("-" * 60)
    
    while True:
        comment = input("\n👉 Comment: ").strip()
        
        if comment.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break
        
        if not comment:
            print("⚠️ Please enter a comment!")
            continue
        
        # Dự đoán
        result = predictor.predict_combined(comment, use_rule_fallback=True)
        
        # Hiển thị kết quả
        print("\n" + "=" * 50)
        print("📊 PREDICTION RESULT")
        print("=" * 50)
        print(f"📝 Comment: {result['comment'][:100]}...")
        print(f"🤖 Model weight: {result['weight_model']} (conf: {result['confidence']:.2%})")
        print(f"📏 Rule weight: {result['weight_rule']}")
        print(f"🎯 Final weight: {result['final_weight']} (method: {result['method']})")
        print(f"🏷️ Issue: {result['issue'] if result['issue'] else 'None'}")
        print("=" * 50)
        
        # Hỏi lưu không
        save = input("\n💾 Save this comment to database? (y/n): ").strip().lower()
        if save == 'y':
            predictor.save_comment(comment, result['final_weight'], result['issue'])
        
        print("-" * 50)


if __name__ == "__main__":
    main()