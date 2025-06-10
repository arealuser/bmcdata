# lstm-c.py
import torch
import torch.nn as nn
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from torch.utils.data import TensorDataset, DataLoader
from sklearn.metrics import accuracy_score, recall_score, f1_score, classification_report
import joblib


df = pd.read_csv('labeld.csv')
X = df.drop(columns=['Effective'] + [col for col in df.columns if '_Diff' in col]).values
y = df['Effective'].values


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)
X_train_tensor = torch.tensor(X_train, dtype=torch.float32).unsqueeze(1)
y_train_tensor = torch.tensor(y_train, dtype=torch.float32)
X_test_tensor = torch.tensor(X_test, dtype=torch.float32).unsqueeze(1)
y_test_tensor = torch.tensor(y_test, dtype=torch.float32)

# 构建 DataLoader
train_data = TensorDataset(X_train_tensor, y_train_tensor)
train_loader = DataLoader(train_data, batch_size=32, shuffle=True)

# 定义模型
class LSTMClassifier(nn.Module):
    def __init__(self, input_dim, hidden_dim=64, num_layers=1):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 1)
        self.sigmoid = nn.Sigmoid()
    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return self.sigmoid(out)

input_dim = X_train_tensor.shape[2]
model = LSTMClassifier(input_dim=input_dim)
criterion = nn.BCELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

# 训练模型
for epoch in range(10):
    for batch_X, batch_y in train_loader:
        pred = model(batch_X).squeeze()
        loss = criterion(pred, batch_y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

# 保存模型
torch.save(model.state_dict(), 'lstm_model.pt')
torch.save(input_dim, 'lstm_input_dim.pt')
joblib.dump(scaler.mean_, 'lstm_scaler_mean.joblib')
joblib.dump(scaler.scale_, 'lstm_scaler_scale.joblib')

# 评估模型
model.eval()
with torch.no_grad():
    preds = model(X_test_tensor).squeeze()
    predicted = (preds > 0.5).float()
    acc = accuracy_score(y_test_tensor, predicted)
    rec = recall_score(y_test_tensor, predicted)
    f1 = f1_score(y_test_tensor, predicted)
    print(f"\n[Test Results]")
    print(f"Accuracy: {acc:.4f}")
    print(f"Recall:   {rec:.4f}")
    print(f"F1 Score: {f1:.4f}")
    print("Classification Report:")
    print(classification_report(y_test_tensor, predicted, digits=4))
