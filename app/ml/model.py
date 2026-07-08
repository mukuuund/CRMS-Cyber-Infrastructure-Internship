import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence
import re
import json

class SimpleTokenizer:
    def __init__(self, max_tokens, max_seq_length):
        self.max_tokens = max_tokens
        self.max_seq_length = max_seq_length
        self.vocab = {"<PAD>": 0, "<UNK>": 1}
        
    def load(self, filepath):
        with open(filepath, 'r') as f:
            self.vocab = json.load(f)
            
    def texts_to_sequences(self, texts):
        sequences = []
        for text in texts:
            words = re.findall(r'\w+', str(text).lower())
            seq = [self.vocab.get(w, 1) for w in words]
            if len(seq) > self.max_seq_length:
                seq = seq[:self.max_seq_length]
            else:
                seq = seq + [0] * (self.max_seq_length - len(seq))
            sequences.append(seq)
        return sequences

class PriorityModelV3(nn.Module):
    def __init__(self, vocab_size, embed_dim, num_classes, num_issue_types, issue_type_embed_dim, gru_hidden_dim, num_numeric_features):
        super(PriorityModelV3, self).__init__()
        
        # Text Embedding
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        
        # TextCNN Branch
        self.conv1 = nn.Conv1d(in_channels=embed_dim, out_channels=100, kernel_size=3)
        self.conv2 = nn.Conv1d(in_channels=embed_dim, out_channels=100, kernel_size=4)
        self.conv3 = nn.Conv1d(in_channels=embed_dim, out_channels=100, kernel_size=5)
        
        # BiGRU Branch
        self.gru = nn.GRU(embed_dim, gru_hidden_dim, bidirectional=True, batch_first=True)
        
        # Issue Type Branch
        self.issue_embedding = nn.Embedding(num_issue_types, issue_type_embed_dim)
        
        # Numeric Branch
        self.num_fc = nn.Linear(num_numeric_features, 32)
        self.num_relu = nn.ReLU()
        self.num_drop = nn.Dropout(0.1)
        
        # Final Dense Branch
        cnn_out_dim = 300
        gru_out_dim = gru_hidden_dim * 2
        combined_dim = cnn_out_dim + gru_out_dim + issue_type_embed_dim + 32
        
        self.fc1 = nn.Linear(combined_dim, 256)
        self.relu1 = nn.ReLU()
        self.drop1 = nn.Dropout(0.4)
        
        self.fc2 = nn.Linear(256, 128)
        self.relu2 = nn.ReLU()
        self.drop2 = nn.Dropout(0.3)
        
        self.fc3 = nn.Linear(128, 64)
        self.relu3 = nn.ReLU()
        self.drop3 = nn.Dropout(0.2)
        
        self.out = nn.Linear(64, num_classes)
        
    def forward(self, text, lengths, issue_type, num_feat):
        # text: (batch, seq_len)
        embeds = self.embedding(text) # (batch, seq_len, embed_dim)
        
        # TextCNN Branch
        embeds_cnn = embeds.permute(0, 2, 1) # (batch, embed_dim, seq_len)
        x1 = torch.relu(self.conv1(embeds_cnn))
        x1 = torch.max(x1, dim=2)[0]
        x2 = torch.relu(self.conv2(embeds_cnn))
        x2 = torch.max(x2, dim=2)[0]
        x3 = torch.relu(self.conv3(embeds_cnn))
        x3 = torch.max(x3, dim=2)[0]
        cnn_out = torch.cat((x1, x2, x3), dim=1) # (batch, 300)
        
        # BiGRU Branch
        packed_embeds = pack_padded_sequence(embeds, lengths.cpu(), batch_first=True, enforce_sorted=False)
        _, hidden = self.gru(packed_embeds)
        forward_hidden = hidden[-2, :, :]
        backward_hidden = hidden[-1, :, :]
        gru_out = torch.cat((forward_hidden, backward_hidden), dim=1) # (batch, 128)
        
        # Issue Type Branch
        issue_emb = self.issue_embedding(issue_type) # (batch, issue_dim)
        
        # Numeric Branch
        num_out = self.num_relu(self.num_fc(num_feat))
        num_out = self.num_drop(num_out) # (batch, 32)
        
        # Combine all features
        combined = torch.cat((cnn_out, gru_out, issue_emb, num_out), dim=1)
        
        x = self.fc1(combined)
        x = self.relu1(x)
        x = self.drop1(x)
        
        x = self.fc2(x)
        x = self.relu2(x)
        x = self.drop2(x)
        
        x = self.fc3(x)
        x = self.relu3(x)
        x = self.drop3(x)
        
        logits = self.out(x)
        return logits
