import torch
import os

class Config:
    # ✅ Đúng repository
    MODEL_NAME = "Fsoft-AIC/videberta-xsmall"
    MAX_LEN = 256
    BATCH_SIZE = 32
    EPOCHS = 10
    LEARNING_RATE = 2e-5
    NUM_CLASSES = 3
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_PATH = os.path.join(BASE_DIR, "models/best_model.pth")
    
    WEIGHT_MAPPING = {0: 0.0, 1: 0.5, 2: 1.0}
    WEIGHT_TO_CLASS = {v: k for k, v in WEIGHT_MAPPING.items()}
    WEIGHT_CLASSES = ['0.0', '0.5', '1.0']
    
    RULE_CONFIG_PATH = os.path.join(BASE_DIR, "rule_config.json")
    
    @classmethod
    def load_issue_keywords(cls):
        import json
        if not os.path.exists(cls.RULE_CONFIG_PATH):
            old_path = os.path.join(cls.BASE_DIR, "rule_config.json")
            if os.path.exists(old_path):
                with open(old_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return config.get('issue_keywords', {})
            return {}
        with open(cls.RULE_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('issue_keywords', {})
    
    @classmethod
    def get_issue_list(cls):
        return list(cls.load_issue_keywords().keys())
    
    @classmethod
    def get_num_issues(cls):
        return len(cls.get_issue_list())
    
    @classmethod
    def get_issue_to_class(cls):
        return {issue: idx for idx, issue in enumerate(cls.get_issue_list())}
    
    @classmethod
    def get_class_to_issue(cls):
        return {idx: issue for idx, issue in enumerate(cls.get_issue_list())}