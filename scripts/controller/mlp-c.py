#mlp
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pandas as pd


df = pd.read_csv('labeld.csv')

X = df.drop(columns=['Effective'] + [col for col in df.columns if '_Diff' in col]).values
y = df['Effective'].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.5, random_state=42)


scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)


X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.long)
X_test = torch.tensor(X_test, dtype=torch.float32)
y_test = torch.tensor(y_test, dtype=torch.long)


train_data = TensorDataset(X_train, y_train)
test_data = TensorDataset(X_test, y_test)
train_loader = DataLoader(train_data, batch_size=32)
test_loader = DataLoader(test_data, batch_size=32)


model = nn.Sequential(
    nn.Linear(X_train.shape[1], 64),
    nn.ReLU(),
    nn.Linear(64, 2)
)

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters())


for epoch in range(100):
    for inputs, labels in train_loader:
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()


torch.save(model.state_dict(), 'model.pt')
torch.save(scaler.mean_, 'scaler_mean.pt')
torch.save(scaler.scale_, 'scaler_scale.pt')
torch.save(X_train.shape[1], 'input_dim.pt')

model.eval()
correct = 0
total = 0
with torch.no_grad():
    for inputs, labels in test_loader:
        outputs = model(inputs)
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

print('Accuracy: {}'.format(correct / total))



