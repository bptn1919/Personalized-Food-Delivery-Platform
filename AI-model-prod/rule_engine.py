import json
import re
import sys
import os
from pathlib import Path

class RuleEngine:
    def __init__(self, config_path='rule_config.json'):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Chỉ còn 3 weight: 0.0, 0.5, 1.0
        self.weight_order = ['weight_1_0', 'weight_0_5', 'weight_0_0']
    
    def classify_weight(self, text):
        """Phân loại weight (0.0, 0.5, 1.0)"""
        text = text.lower()
        
        # Kiểm tra weight_0_0 (tệ) trước
        if self._check_weight_0_0(text):
            return 0.0
        
        # Kiểm tra weight_1_0 (tuyệt vời)
        if self._check_weight_1_0(text):
            return 1.0
        
        # Mặc định là weight_0_5 (trung bình)
        return 0.5
    
    def _check_weight_1_0(self, text):
        """Kiểm tra weight 1.0 - Tuyệt vời"""
        rules = self.config['weight_rules']['weight_1_0']
        
        must_have_ok = all(
            any(kw in text for kw in rules['keywords'].get(key, []))
            for key in rules.get('must_have', [])
        )
        
        optional_count = sum(
            1 for key in rules.get('optional', [])
            if any(kw in text for kw in rules['keywords'].get(key, []))
        )
        
        return must_have_ok and optional_count >= rules.get('need_at_least', 1)
    
    def _check_weight_0_0(self, text):
        """Kiểm tra weight 0.0 - Tệ / spam"""
        rules = self.config['weight_rules']['weight_0_0']
        
        # Kiểm tra block keywords
        for category, keywords in rules.get('block_keywords', {}).items():
            if any(kw in text for kw in keywords):
                return True
        
        # Kiểm tra serious issues
        for issue in rules.get('serious_issues', []):
            if issue in text:
                return True
        
        # Kiểm tra bot patterns
        for pattern in rules.get('bot_patterns', []):
            if re.search(pattern, text):
                return True
        
        # Kiểm tra conditions
        conditions = rules.get('conditions', {})
        if conditions.get('is_short'):
            word_count = len(text.split())
            if word_count <= conditions['is_short'].get('max_word_count', 2):
                return True
        
        return False
    
    def classify_issue(self, text):
        """Phân loại issue dựa trên từ khóa"""
        text = text.lower()
        issues = []
        
        for issue, keywords in self.config['issue_keywords'].items():
            if any(kw in text for kw in keywords):
                issues.append(issue)
        
        return issues[0] if issues else None
    
    def classify(self, text):
        """Phân loại cả weight và issue"""
        weight = self.classify_weight(text)
        issue = self.classify_issue(text)
        return weight, issue


# ===================== HÀM TIỆN ÍCH =====================
def label_comments(comments, rule_engine=None):
    """Gán nhãn cho list comments (string)"""
    if rule_engine is None:
        rule_engine = RuleEngine()
    
    results = []
    total = len(comments)
    
    for i, comment in enumerate(comments):
        weight, issue = rule_engine.classify(comment)
        results.append({
            'comment': comment,
            'weight': weight,
            'issue': issue
        })
        
        # Progress bar
        percent = (i + 1) / total * 100
        bar_len = 50
        filled = int(bar_len * (i + 1) // total)
        bar = '█' * filled + '░' * (bar_len - filled)
        sys.stdout.write(f"\r  Labeling |{bar}| {percent:.1f}% {i+1}/{total} comments")
        sys.stdout.flush()
    
    print()
    return results


def label_comments_file(input_path="data/comments.json", output_path=None, inplace=False):
    """
    Đọc file JSON, gán nhãn weight và issue cho từng comment
    
    Args:
        input_path: Đường dẫn file đầu vào
        output_path: Đường dẫn file đầu ra (nếu None và inplace=False, tự tạo tên mới)
        inplace: Nếu True, ghi đè trực tiếp lên file gốc
    """
    if not os.path.exists(input_path):
        print(f"❌ File {input_path} không tồn tại!")
        return None
    
    # Đọc dữ liệu
    print(f"📁 Đang đọc file: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        print(f"❌ File không đúng định dạng (cần là list)")
        return None
    
    # Xác định cấu trúc file
    if len(data) > 0 and isinstance(data[0], dict) and 'comment' in data[0]:
        # Dạng [{"comment": "...", "uid": "...", ...}, ...]
        comments = [item['comment'] for item in data]
        original_data = data
        is_object_list = True
    elif all(isinstance(item, str) for item in data):
        # Dạng ["comment1", "comment2", ...]
        comments = data
        original_data = None
        is_object_list = False
    else:
        print(f"❌ Không nhận dạng được cấu trúc file")
        return None
    
    print(f"✅ Tìm thấy {len(comments)} comments")
    
    # Gán nhãn
    print("\n🏷️ Đang gán nhãn với Rule Engine...")
    rule_engine = RuleEngine()
    labeled = []
    total = len(comments)
    
    for i, comment in enumerate(comments):
        weight, issue = rule_engine.classify(comment)
        labeled.append({
            'comment': comment,
            'weight': weight,
            'issue': issue
        })
        
        # Progress bar
        percent = (i + 1) / total * 100
        bar_len = 50
        filled = int(bar_len * (i + 1) // total)
        bar = '█' * filled + '░' * (bar_len - filled)
        sys.stdout.write(f"\r  Labeling |{bar}| {percent:.1f}% {i+1}/{total} comments")
        sys.stdout.flush()
    
    print("\n✅ Gán nhãn hoàn tất!")
    
    # Tạo dữ liệu đầu ra
    if is_object_list and original_data:
        # Cập nhật weight và issue vào object gốc
        for i, item in enumerate(original_data):
            item['weight'] = labeled[i]['weight']
            item['issue'] = labeled[i]['issue']
        output_data = original_data
    else:
        output_data = labeled
    
    # Xác định đường dẫn đầu ra
    if inplace:
        output_path = input_path
    elif output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_labeled{ext}"
    
    # Đảm bảo thư mục tồn tại
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    # Lưu file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    # Thống kê
    print(f"\n📊 THỐNG KÊ NHÃN:")
    weight_counts = {0.0: 0, 0.5: 0, 1.0: 0}
    issue_counts = {}
    no_issue = 0
    
    for item in labeled:
        w = item['weight']
        weight_counts[w] = weight_counts.get(w, 0) + 1
        if item['issue']:
            issue_counts[item['issue']] = issue_counts.get(item['issue'], 0) + 1
        else:
            no_issue += 1
    
    print(f"\n  Weight distribution:")
    for w in [0.0, 0.5, 1.0]:
        count = weight_counts.get(w, 0)
        pct = count / len(labeled) * 100 if len(labeled) > 0 else 0
        bar = '█' * int(pct / 2) + '░' * (50 - int(pct / 2))
        print(f"    {w}: {count:6d} ({pct:5.1f}%) |{bar}|")
    
    print(f"\n  Issue distribution (top 10):")
    for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        pct = count / len(labeled) * 100
        bar = '█' * int(pct / 2) + '░' * (50 - int(pct / 2))
        print(f"    {issue:15s}: {count:6d} ({pct:5.1f}%) |{bar}|")
    
    if no_issue > 0:
        pct = no_issue / len(labeled) * 100
        print(f"    {'no_issue':15s}: {no_issue:6d} ({pct:5.1f}%)")
    
    print(f"\n✅ Đã lưu vào: {output_path}")
    return output_data


# ===================== MAIN =====================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Gán nhãn weight và issue cho comments')
    parser.add_argument('--input', '-i', default='data/comments.json',
                        help='Đường dẫn file đầu vào (default: data/comments.json)')
    parser.add_argument('--output', '-o', default=None,
                        help='Đường dẫn file đầu ra (default: input_labeled.json)')
    parser.add_argument('--inplace', '-a', action='store_true',
                        help='Cập nhật trực tiếp vào file gốc')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🏷️ RULE ENGINE - GÁN NHÃN WEIGHT & ISSUE")
    print("=" * 60)
    
    label_comments_file(
        input_path=args.input,
        output_path=args.output,
        inplace=args.inplace
    )