from PIL import Image
from torchvision import transforms

TARGET_SIZE = 384

val_transform = transforms.Compose([
    transforms.Resize((TARGET_SIZE, TARGET_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])

def load_and_preprocess_image(path, device):
    img = Image.open(path).convert("RGB")
    tensor = val_transform(img).unsqueeze(0).to(device)
    return tensor
