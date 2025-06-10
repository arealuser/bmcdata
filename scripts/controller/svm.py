import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import joblib


data = pd.read_csv('labeld.csv')

zero_counts = data.iloc[:, :-1].eq(0).sum(axis=1)


features = data.iloc[:, :-1].values
labels = data['Effective'].values

X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.5, random_state=33)


svm = SVC()


svm.fit(X_train, y_train)


predictions = svm.predict(X_test)


accuracy = accuracy_score(y_test, predictions)


confusion_mat = confusion_matrix(y_test, predictions)
classification_rep = classification_report(y_test, predictions, digits=4)


for pred, actual in zip(predictions, y_test):
    print(f"Predicted: {pred}, Actual: {actual}")


print(f"Accuracy: {accuracy:.4f}")


print("Confusion Matrix:")
print(confusion_mat)
print("Classification Report:")
print(classification_rep)

joblib.dump(svm, 'svm_model.joblib')
