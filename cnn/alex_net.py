import torch
import torchvision
from torchvision import transforms
import torch.optim as optim
import torch.nn as nn
import sys
import os
from PIL import Image


class SglDataset(torch.utils.data.Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.fnames = os.listdir(root_dir)
        self.fnames.remove('.ipynb_checkpoints')
        self.fnames.sort(key=lambda x: int(x[:4]))
        self.transform = transform

    def __len__(self):
        return len(self.fnames)

    def __getitem__(self, index):
        img_id = self.fnames[index]
        img = Image.open(os.path.join(self.root_dir, img_id)).convert("RGB")
        y_label = torch.tensor(int(img_id[:4]) // 50)
        if y_label >= 6:
            y_label += 1

        if self.transform is not None:
            img = self.transform(img)

        return (img, y_label)


def load_data():
    """
    Fetch data from dataset folder
    """
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    train_data = torchvision.datasets.CIFAR10(root='./../datasets/alexnet/train', train=True, download=True, transform=preprocess)
    print(train_data.classes)
    trainloader = torch.utils.data.DataLoader(train_data, batch_size=4, shuffle=True, num_workers=4)

    # Downloading test data
    test_data = torchvision.datasets.CIFAR10(root='./../datasets/alexnet/test', train=False, download=True, transform=preprocess)

    testloader = torch.utils.data.DataLoader(test_data, batch_size=4, shuffle=False, num_workers=4)

    return trainloader, testloader


def load_custom_test_data(data_path):
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    test_dataset = SglDataset(data_path, preprocess)

    test_loader = torch.utils.data.DataLoader(
        test_dataset,
        batch_size=3,
        num_workers=4,
        shuffle=False
    )
    return test_loader


def train_model(model, data_loader, epochs, store_path):
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)

    for e in range(epochs):
        running_loss = 0.0
        for i, data in enumerate(data_loader, 0):
            # get the inputs; data is a list of [inputs, labels]
            inputs, labels = data[0].to(device), data[1].to(device)

            # zero the parameter gradients
            optimizer.zero_grad()

            # forward + backward + optimize
            output = model(inputs)
            loss = criterion(output, labels)
            loss.backward()
            optimizer.step()

            # print statistics
            running_loss += loss.item()
            if i % 2000 == 1999:  # print every 2000 mini-batches
                print('[%d, %5d] loss: %.3f' %
                      (e + 1, i + 1, running_loss / 2000))
                running_loss = 0.0

    torch.save(model, store_path)
    print("Model saved at: {}".format(store_path))
    return model


def test_model(model, data_loader):
    total = 0
    correct = 0
    with torch.no_grad():
        for data in data_loader:
            images, labels = data[0].to(device), data[1].to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    print('Accuracy of the network on the 10000 test images: %d %%' % (
            100 * correct / total))


def get_model_data(test_data_path):
    return load_custom_test_data(test_data_path)


if __name__ == '__main__':
    act = sys.argv[1]
    if act == "train":
        epochs = int(sys.argv[2])
        model = torch.hub.load('pytorch/vision:v0.6.0', 'alexnet', pretrained=True)
        model.eval()

        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        print(device)

        model.to(device)

        train_loader, test_loader = load_data()

        MODEL_PATH = './../models/alexnet/model.pth'
        model = train_model(model, train_loader, epochs, MODEL_PATH)

        test_model(model, test_loader)

    elif act == "test":
        mod_path = sys.argv[2]
        test_data_path = sys.argv[3]

        test_data_loader = load_custom_test_data(test_data_path)
        model = torch.load(mod_path)

        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        model.to(device)

        test_model(model, test_data_loader)