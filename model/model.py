import os
import cv2
import numpy as np
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from torch.optim.lr_scheduler import ReduceLROnPlateau
import torchvision.transforms as transforms
import torchvision.models as models

# ----------------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)

# ----------------------------------------
# Define Custom Dataset (stores images and labels)
class CustomImageDataset(Dataset):
    def __init__(self, images, labels, transform=None):
        """
        images: numpy array, shape (N, H, W, 3), RGB, normalized values ([-1,1])
        labels: numpy array, integer labels
        transform: torchvision.transforms for image augmentation and preprocessing
        """
        self.images = images
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        # Image: (H, W, 3), already normalized to [-1,1]
        image = self.images[idx]
        if self.transform:
            # To apply transform, restore range from [-1,1] to [0,255] and convert to PIL image
            image_uint8 = (((image + 1) * 127.5).clip(0, 255)).astype(np.uint8)
            image = transforms.ToPILImage()(image_uint8)
            image = self.transform(image)
        else:
            image = torch.from_numpy(image.transpose(2, 0, 1))
        label = int(self.labels[idx])
        return image, label

# ----------------------------------------
data = []
labels = []
# Each directory and its label (0: go, 1: left, 2: right)
paths = [("/image/go", 0), ("/image/left", 1), ("/image/right", 2)]
for path, label in paths:
    for img_name in os.listdir(path):
        img_path = os.path.join(path, img_name)
        image = cv2.imread(img_path)  # Read image in BGR format
        if image is None:
            continue

        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = image.astype('float32')

        # Normalize pixel values from [0,255] to [-1,1]
        image = (image / 127.5) - 1
        data.append(image)
        labels.append(label)
data = np.array(data)
labels = np.array(labels)
print("Total number of images =", len(data))

# ----------------------------------------
# Split data into training and validation sets (8:2)
X_train, X_valid, Y_train, Y_valid = train_test_split(data, labels, test_size=0.2, random_state=42)

# ----------------------------------------
# Data augmentation and preprocessing (using torchvision.transforms)
# Apply augmentation and normalization to training data
train_transform = transforms.Compose([
    transforms.RandomRotation(20),          # Rotate up to 20 degrees
    transforms.RandomAffine(degrees=0, translate=(0.05, 0.05)),  # Translation: up to 5% shift horizontally and vertically
    transforms.RandomResizedCrop(64, scale=(0.9, 1.0)),
    transforms.ToTensor(),                    # Convert to tensor ([0,1] range)
    transforms.Normalize(mean=[0.485, 0.456, 0.406],  # ImageNet mean
                         std=[0.229, 0.224, 0.225])   # ImageNet standard deviation
])
# For validation data, apply only preprocessing without augmentation
val_transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

train_dataset = CustomImageDataset(X_train, Y_train, transform=train_transform)
val_dataset   = CustomImageDataset(X_valid, Y_valid, transform=val_transform)

batch_size = 64
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)
val_loader   = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=2)

# ----------------------------------------
# Define model: Transfer Learning (ResNet-34 based) - modified for 64x64 input
model = models.resnet34(weights=models.ResNe34_Weights.DEFAULT)

# The original first conv layer of ResNet-34 is 7x7, stride=2, padding=3,
# but for small images (64x64) it causes excessive downsampling; changed to 3x3, stride=1, padding=1
model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)

# Remove the initial maxpool to preserve resolution
model.maxpool = nn.Identity()

# Replace the final FC layer to match 3 classes
num_features = model.fc.in_features

model.fc = nn.Sequential(
    nn.Linear(num_features, 32),     # Hidden layer
    nn.BatchNorm1d(32),              # Add batch normalization
    nn.ReLU(inplace=True),           # Activation function
    nn.Dropout(0.6),                 # Dropout (to prevent overfitting)
    nn.Linear(32, 3)                 # Final output: 3 classes
)
model = model.to(device)

# ----------------------------------------
# Set Loss, Optimizer, and Scheduler
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-3)
scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=0.1, patience=4, verbose=True, min_lr=1e-6)

# ----------------------------------------
# Training Loop with Early Stopping (based on validation loss)
num_epochs = 120
best_val_loss = float('inf')
patience = 30
patience_counter = 0

train_losses = []
val_losses = []
train_acc_list = []  # List to store train accuracy
val_acc_list = []    # List to store validation accuracy

for epoch in range(1, num_epochs+1):
    model.train()
    running_loss = 0.0
    running_correct = 0

    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        _, preds = torch.max(outputs, 1)
        running_correct += (preds == labels).sum().item()

    train_loss = running_loss / len(train_dataset)
    train_acc = running_correct / len(train_dataset)
    train_losses.append(train_loss)
    train_acc_list.append(train_acc)  # Save training accuracy

    model.eval()
    val_running_loss = 0.0
    val_running_correct = 0
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            val_running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            val_running_correct += (preds == labels).sum().item()

    val_loss = val_running_loss / len(val_dataset)
    val_acc = val_running_correct / len(val_dataset)
    val_losses.append(val_loss)
    val_acc_list.append(val_acc)  # Save validation accuracy

    scheduler.step(val_loss)
    current_lr = optimizer.param_groups[0]['lr']

    print(f"Epoch {epoch}/{num_epochs} - Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f} | "
          f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f} | LR: {current_lr:.6f}")

    if val_loss < best_val_loss:
        best_val_loss = val_loss
        patience_counter = 0
        best_model_wts = model.state_dict()
        torch.save(best_model_wts, "best_model.pth")
    else:
        patience_counter += 1
        if patience_counter >= patience:
            print("Early stopping triggered!")
            break

# ----------------------------------------
# Visualize training curves (Loss)
plt.figure()
plt.plot(train_losses, label='Train Loss')
plt.plot(val_losses, label='Val Loss')
plt.title('Training vs Validation Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend(loc='upper right')
plt.show()

# ----------------------------------------
# Visualize accuracy curves (Train Accuracy: green, Val Accuracy: red)
plt.figure()
plt.plot(train_acc_list, label='Train Accuracy', color='green')
plt.plot(val_acc_list, label='Val Accuracy', color='red')
plt.title('Training vs Validation Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend(loc='lower right')
plt.show()

# ----------------------------------------
# Final evaluation: Load the saved best model and evaluate on the validation dataset
model.load_state_dict(torch.load("best_model.pth"))
model.eval()
final_loss = 0.0
final_correct = 0
final_total = 0
with torch.no_grad():
    for images, labels in val_loader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        loss = criterion(outputs, labels)
        final_loss += loss.item() * images.size(0)
        _, preds = torch.max(outputs, 1)
        final_correct += (preds == labels).sum().item()
        final_total += labels.size(0)
final_val_loss = final_loss / len(val_dataset)
final_val_acc = final_correct / len(val_dataset)
print(f"Final Val Loss: {final_val_loss:.4f} - Final Val Acc: {final_val_acc:.4f}")