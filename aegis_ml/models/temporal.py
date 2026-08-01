import os
import time
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import logging
import pickle
from hmmlearn import hmm

logger = logging.getLogger("aegis.phase8.temporal")

# ---------------------------------------------------------
# PyTorch Base Module for RNNs (LSTM / GRU)
# ---------------------------------------------------------
class PyTorchRNN(nn.Module):
    def __init__(self, rnn_type, input_dim, hidden_dim, num_layers, dropout):
        super(PyTorchRNN, self).__init__()
        
        self.rnn_type = rnn_type
        if rnn_type == 'LSTM':
            self.rnn = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True, dropout=dropout if num_layers > 1 else 0)
        elif rnn_type == 'GRU':
            self.rnn = nn.GRU(input_dim, hidden_dim, num_layers, batch_first=True, dropout=dropout if num_layers > 1 else 0)
        else:
            raise ValueError(f"Unknown rnn_type: {rnn_type}")
            
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        rnn_out, _ = self.rnn(x)
        last_out = rnn_out[:, -1, :]
        return self.fc(last_out)

# ---------------------------------------------------------
# Base Wrapper for PyTorch Models
# ---------------------------------------------------------
class TemporalRNNClassifier:
    def __init__(self, rnn_type, input_dim=7, hidden_dim=32, num_layers=2, dropout=0.1, lr=0.001, epochs=30):
        self.rnn_type = rnn_type
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.dropout = dropout
        self.lr = lr
        self.epochs = epochs
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
        self.model = PyTorchRNN(rnn_type, input_dim, hidden_dim, num_layers, dropout).to(self.device)
        
        # Binary Classification
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.lr)
        self.criterion = nn.BCELoss()

    def fit(self, X_train, y_train, batch_size=64):
        self.model.train()
        X_tensor = torch.FloatTensor(X_train).to(self.device)
        y_tensor = torch.FloatTensor(y_train).view(-1, 1).to(self.device)
        
        dataset = torch.utils.data.TensorDataset(X_tensor, y_tensor)
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        for epoch in range(self.epochs):
            total_loss = 0.0
            for batch_X, batch_y in dataloader:
                self.optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)
                loss.backward()
                self.optimizer.step()
                total_loss += loss.item() * batch_X.size(0)
            
            avg_loss = total_loss / len(dataset)
            if (epoch + 1) % 10 == 0:
                logger.info(f"{self.rnn_type} Epoch {epoch+1}/{self.epochs}, Loss: {avg_loss:.6f}")

    def predict_proba(self, X):
        self.model.eval()
        X_tensor = torch.FloatTensor(X).to(self.device)
        with torch.no_grad():
            preds = self.model(X_tensor)
        # Returns probability of class 1
        return preds.cpu().numpy().flatten()

    def predict(self, X, threshold=0.5):
        probs = self.predict_proba(X)
        return (probs > threshold).astype(int)

    def save(self, filepath):
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'params': {
                'rnn_type': self.rnn_type,
                'input_dim': self.input_dim,
                'hidden_dim': self.hidden_dim,
                'num_layers': self.num_layers,
                'dropout': self.dropout
            }
        }, filepath)

    def load(self, filepath):
        checkpoint = torch.load(filepath, map_location=self.device)
        params = checkpoint['params']
        self.rnn_type = params['rnn_type']
        self.input_dim = params['input_dim']
        self.hidden_dim = params['hidden_dim']
        self.num_layers = params['num_layers']
        self.dropout = params['dropout']
        
        self.model = PyTorchRNN(self.rnn_type, self.input_dim, self.hidden_dim, self.num_layers, self.dropout).to(self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])

# ---------------------------------------------------------
# LSTM and GRU Implementations
# ---------------------------------------------------------
class LSTMClassifier(TemporalRNNClassifier):
    def __init__(self, **kwargs):
        super().__init__(rnn_type='LSTM', **kwargs)

class GRUClassifier(TemporalRNNClassifier):
    def __init__(self, **kwargs):
        super().__init__(rnn_type='GRU', **kwargs)

# ---------------------------------------------------------
# HMM Classifier (Generative approach)
# ---------------------------------------------------------
class HMMClassifier:
    def __init__(self, n_components=3, covariance_type='diag', n_iter=100):
        self.n_components = n_components
        self.covariance_type = covariance_type
        self.n_iter = n_iter
        
        # We will train two HMMs: one for Normal (class 0), one for Anomaly (class 1)
        self.hmm_normal = hmm.GaussianHMM(n_components=n_components, covariance_type=covariance_type, n_iter=n_iter, random_state=42)
        self.hmm_anomaly = hmm.GaussianHMM(n_components=n_components, covariance_type=covariance_type, n_iter=n_iter, random_state=42)

    def fit(self, X_train, y_train):
        """
        X_train: (N, seq_len, input_dim)
        y_train: (N,)
        """
        # HMM in hmmlearn expects 2D array (samples * seq_len, features) and a lengths array.
        X_0 = X_train[y_train == 0]
        X_1 = X_train[y_train == 1]
        
        if len(X_0) > 0:
            lengths_0 = [X_0.shape[1]] * X_0.shape[0]
            X_0_flat = X_0.reshape(-1, X_0.shape[2])
            self.hmm_normal.fit(X_0_flat, lengths_0)
            
        if len(X_1) > 0:
            lengths_1 = [X_1.shape[1]] * X_1.shape[0]
            X_1_flat = X_1.reshape(-1, X_1.shape[2])
            self.hmm_anomaly.fit(X_1_flat, lengths_1)

    def predict_proba(self, X):
        """
        Returns a pseudo-probability of class 1 using log-likelihoods.
        """
        probs = []
        for i in range(X.shape[0]):
            x_seq = X[i] # (seq_len, input_dim)
            
            try:
                ll_0 = self.hmm_normal.score(x_seq)
            except:
                ll_0 = -1e9
                
            try:
                ll_1 = self.hmm_anomaly.score(x_seq)
            except:
                ll_1 = -1e9
                
            # Softmax to convert log-likelihoods to probabilities
            # P(Anomaly) = exp(ll_1) / (exp(ll_0) + exp(ll_1))
            # numerically stable:
            max_ll = max(ll_0, ll_1)
            exp_0 = np.exp(ll_0 - max_ll)
            exp_1 = np.exp(ll_1 - max_ll)
            
            p1 = exp_1 / (exp_0 + exp_1 + 1e-12)
            probs.append(p1)
            
        return np.array(probs)

    def predict(self, X, threshold=0.5):
        probs = self.predict_proba(X)
        return (probs > threshold).astype(int)

    def save(self, filepath):
        with open(filepath, 'wb') as f:
            pickle.dump({
                'hmm_normal': self.hmm_normal,
                'hmm_anomaly': self.hmm_anomaly,
                'n_components': self.n_components,
                'covariance_type': self.covariance_type
            }, f)

    def load(self, filepath):
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.hmm_normal = data['hmm_normal']
            self.hmm_anomaly = data['hmm_anomaly']
            self.n_components = data['n_components']
            self.covariance_type = data['covariance_type']
