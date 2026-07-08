import os
import json
import torch
import numpy as np
from app.ml.model import PriorityModelV3, SimpleTokenizer

class Predictor:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        # Paths
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        models_dir = os.path.join(base_dir, 'models', 'priority_model')
        config_path = os.path.join(models_dir, 'model_config_v3.json')
        
        with open(config_path, 'r') as f:
            self.config = json.load(f)
            
        self.device = torch.device("cpu") # CPU inference for FastAPI
        
        # Load artifacts
        with open(os.path.join(models_dir, 'label_map_v3.json'), 'r') as f:
            self.label_map = json.load(f)
            self.reverse_label_map = {int(v): k for k, v in self.label_map.items()}
            
        with open(os.path.join(models_dir, 'issue_type_map_v3.json'), 'r') as f:
            self.issue_type_map = json.load(f)
            
        with open(os.path.join(models_dir, 'feature_scaler_v3.json'), 'r') as f:
            self.scaler_stats = json.load(f)
            
        self.tokenizer = SimpleTokenizer(
            max_tokens=self.config['max_tokens'],
            max_seq_length=self.config['max_sequence_length']
        )
        self.tokenizer.load(os.path.join(models_dir, 'vocab_v3.json'))
        
        # Initialize model
        self.model = PriorityModelV3(
            vocab_size=self.config['vocab_size'],
            embed_dim=self.config['embedding_dim'],
            num_classes=3,
            num_issue_types=self.config['num_issue_types'],
            issue_type_embed_dim=self.config['issue_type_embedding_dim'],
            gru_hidden_dim=self.config['gru_hidden_dim'],
            num_numeric_features=self.config['num_numeric_features']
        )
        
        # Load weights
        model_path = os.path.join(models_dir, 'priority_model_v3.pth')
        self.model.load_state_dict(torch.load(model_path, map_location=self.device, weights_only=True))
        self.model.eval()
        
        self.keywords = [
            'error', 'exception', 'crash', 'failure', 'security', 
            'data loss', 'cannot', 'unable', 'timeout', 'memory', 
            'production', 'login', 'server', 'build', 'compile'
        ]
        self.numeric_length_features = ['summary_char_len', 'description_char_len', 'summary_word_count', 'description_word_count']

    def predict(self, title: str, description: str, issue_type: str):
        title = title or ""
        description = description or ""
        issue_type = issue_type or "Unknown"
        
        # 1. Text processing
        model_text = f"[TITLE] {title} [TITLE] {title} [DESC] {description[:1500]}"
        seq = self.tokenizer.texts_to_sequences([model_text])
        text_tensor = torch.tensor(seq, dtype=torch.long)
        
        actual_len = (text_tensor != 0).sum().item()
        if actual_len == 0:
            actual_len = 1
        len_tensor = torch.tensor([actual_len])
        
        # 2. Issue Type processing
        issue_idx = self.issue_type_map.get(issue_type, self.issue_type_map.get('Unknown', 0))
        issue_tensor = torch.tensor([issue_idx], dtype=torch.long)
        
        # 3. Numeric Features processing
        search_text = (title + " " + description).lower()
        feat_vector = []
        
        # Length features
        feat_vector.append(float(len(title)))
        feat_vector.append(float(len(description)))
        feat_vector.append(float(len(title.split())))
        feat_vector.append(float(len(description.split())))
        
        # Scale length features
        for i, col in enumerate(self.numeric_length_features):
            mean_val = self.scaler_stats[col]['mean']
            std_val = self.scaler_stats[col]['std']
            feat_vector[i] = (feat_vector[i] - mean_val) / std_val
            
        # Binary features
        for kw in self.keywords:
            feat_vector.append(1.0 if kw in search_text else 0.0)
            
        num_tensor = torch.tensor([feat_vector], dtype=torch.float32)
        
        # 4. Inference
        with torch.no_grad():
            logits = self.model(text_tensor, len_tensor, issue_tensor, num_tensor)
            probs = torch.softmax(logits, dim=1).squeeze().numpy()
            
        pred_idx = int(np.argmax(probs))
        predicted_label = self.reverse_label_map[pred_idx]
        confidence = float(probs[pred_idx])
        
        class_probs = {self.reverse_label_map[i]: float(probs[i]) for i in range(len(probs))}
        
        return {
            "predicted_priority": predicted_label,
            "confidence": confidence,
            "class_probabilities": class_probs,
            "warning": "AI suggestion only. Final priority should be confirmed by PM/BA."
        }
