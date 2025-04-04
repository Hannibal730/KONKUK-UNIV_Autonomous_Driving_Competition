# 건국대학교 주관 행동모사 자율주행 경진대회

- #### **내용**: 카메라와 모터 제어로직 코딩, 촬영한 주행데이터를 기반으로 자율주행 모델 개발

- #### **대회일**: 2024/06/27

- #### **주임교수**: 건국대학교 기계항공공학부 김창완

- #### **팀원**: 건국대학교 응용통계학과 최대승, 건국대학교 기계공학과 석승연

- #### **수상이력**: 1등 대상 [Click Here](https://www.konkuk.ac.kr/konkuk/2096/subview.do?enc=Zm5jdDF8QEB8JTJGYmJzJTJGa29ua3VrJTJGMjU3JTJGMTEzMTA1OCUyRmFydGNsVmlldy5kbyUzRg==)
  <img src="https://github.com/user-attachments/assets/6288de28-31e7-4c11-a0f6-63b9f097e01c" width="400" alt="Image">
---------
<br>




# 딥러닝 전이학습을 활용한 이미지 분류

이 프로젝트는 딥러닝 모델(ResNet-18 기반 전이학습)을 활용하여 3가지 방향(Go, Left, Right) 이미지 분류 작업을 수행합니다. 주어진 이미지를 학습 및 검증 데이터로 나누고, 데이터 증강 및 전처리를 통해 모델을 학습시킨 후 최적의 성능을 보인 모델을 저장합니다.
<br><br>
## 주요 기능

- **Custom Dataset 구현:** 이미지 데이터와 라벨을 기반으로 PyTorch Dataset 클래스를 커스터마이징
- **데이터 증강 및 전처리:** 학습 데이터에 대해 랜덤 회전, 평행 이동, 크롭을 증강 기법으로 적용
- **전이학습 기반 모델 구성:** 사전 학습된 ResNet-18 모델을 작은 64x64 입력 이미지에 맞게 수정하고, 최종 Fully Connected (FC) 레이어를 3 클래스 분류에 맞게 재구성
- **학습 및 검증 루프:** CrossEntropyLoss, Adam Optimizer, ReduceLROnPlateau 스케줄러를 사용하여 학습 진행 및 Early Stopping 적용
- **성능 시각화:** 학습 및 검증 Loss, Accuracy 곡선을 시각화하여 학습 과정을 모니터링
- **모델 저장 및 평가:** 베스트 모델 저장 후 최종 검증 데이터셋에 대해 평가 진행 <br><br>


## 성능
<img src="https://github.com/user-attachments/assets/2c97a8ee-8687-48a2-9408-ca63194fff72" width="500" alt="Image">
<img src="https://github.com/user-attachments/assets/6023c12b-572a-4a56-8155-5f524f32d53d" width="500" alt="Image">



<br><br>
## 데이터 구조

- **이미지 전처리:**
  - **1. 원본 이미지:** 라즈베리 파이로 캡처한 raw 이미지의 사이즈는 (1500, 1000)입니다.
  - **2. 회전:** 이미지를 180도 회전시킵니다. (`cv2.flip(frame, -1)` 사용)
  - **3. 초기 리사이즈:** ROI 추출을 용이하게 하기 위해 이미지를 (512, 512) 크기로 리사이즈합니다.
  - **4. ROI 생성:** 상단 200픽셀을 제거하여 ROI를 생성합니다. (`frame = frame[200:,:]`)
  - **5. 최종 리사이즈:** 추출된 ROI 이미지를 모델 입력 사이즈인 (64, 64)로 리사이즈하여 저장합니다. <br>


- **순서대로 go, left, right 이미지** <br>

  <img src="https://github.com/user-attachments/assets/95112164-7efa-46c3-af64-9926aae694b3" width="150" alt="Image">  
  <img src="https://github.com/user-attachments/assets/85175b2b-5a76-460c-bf55-6e8d5ac9a00f" width="150" alt="Image">
  <img src="https://github.com/user-attachments/assets/8ba87864-7ac3-47da-8831-2f9b69dc81dc" width="150" alt="Image">


- **이미지 디렉토리:**  
  image <br>
  ├── go : "Go" 이미지들 <br>
  ├── left : "Left" 이미지들   <br>
  └── right : "Right" 이미지들 <br>


<br><br>
## 모델 아키텍처 상세 설명

본 프로젝트에서는 전이학습 기법을 활용하여 사전 학습된 **ResNet-18** 모델을 기반으로 이미지 분류기를 구성하였습니다. 아래는 모델 아키텍처의 각 구성 요소에 대한 상세 설명입니다.

### 1. ResNet-18 기반 모델
- **사전 학습 가중치 사용:**  
  - `models.resnet18(weights=models.ResNet18_Weights.DEFAULT)`를 통해 ImageNet 데이터셋으로 사전 학습된 가중치를 사용하여 모델을 초기화합니다.
  
- **첫 번째 Convolution 레이어 수정:**  
  - **원래 구조:** 7x7 커널, stride=2, padding=3  
  - **수정 후 구조:** 3x3 커널, stride=1, padding=1  
  - **이유:** 작은 해상도(64x64)의 이미지에서 과도한 다운샘플링을 방지하고, 세밀한 특징을 추출하기 위해 변경되었습니다.
  
- **MaxPooling 레이어 제거:**  
  - 기존 ResNet-18은 첫 번째 Convolution 이후 MaxPooling 레이어를 사용하여 해상도를 줄입니다.
  - 작은 이미지에서는 중요한 공간 정보를 잃을 수 있으므로, 이를 `nn.Identity()`로 대체하여 제거하였습니다.

### 2. Fully Connected (FC) 레이어 재구성
- **기존 FC 레이어 교체:**  
  - ImageNet 분류를 위해 설계된 1000 클래스 출력 대신, 3 클래스(Go, Left, Right) 분류를 위한 레이어로 재구성합니다.
  
- **세부 구성:**  
  - **중간 Hidden Layer:**  
    - **Linear Layer:** 입력 feature 수(`num_features`)를 32개의 뉴런으로 축소  
    - **Batch Normalization:** 학습 안정성과 수렴 속도 향상을 위해 적용  
    - **ReLU 활성화 함수:** 비선형성을 부여하여 모델 성능을 향상  
    - **Dropout (0.6):** 과적합을 방지하기 위해 높은 확률로 뉴런을 랜덤하게 비활성화  
  - **최종 출력 레이어:**  
    - 32개의 뉴런을 3개의 클래스 출력으로 변환하는 Linear 레이어를 사용하여 최종 분류 결과를 도출합니다.

### 3. 전체 모델 흐름
1. **입력 처리:**  
   - 입력 이미지의 크기는 64x64이며, RGB 채널로 구성됩니다.
2. **Feature Extraction:**  
   - 수정된 첫 번째 Convolution 레이어를 포함한 ResNet-18 블록들을 통과하며 이미지의 고수준 특징을 추출합니다.
3. **분류 단계:**  
   - 추출된 feature는 Global Average Pooling 등을 통해 flatten된 후, 재구성된 FC 레이어를 거쳐 3개의 클래스에 대한 확률로 변환됩니다.

이와 같은 모델 아키텍처 설계는 작은 해상도의 이미지에서도 충분한 특징 추출 및 분류 성능을 발휘할 수 있도록 최적화되었습니다.



```mermaid
flowchart TD
    A["Input: 64×64×3"]
    B["Conv1: (3x3, 64)<br/> stride=1, padding=1<br/>+ BatchNorm <br/> + ReLU"]
    C["ResNet‑18 Adjustment:<br/>MaxPool Layer Removed<br/>(Replaced with Identity)"]
    D["ResNet‑18 Backbone: <br/>Conv2: (3x3, 64) <br/> → 64×64×64 <br/> Conv3: (3x3, 128) <br/>→ 32×32×128<br/> Conv4: (3x3, 256) <br/> →16×16×256 <br/> Conv5: (3x3, 512) <br/> → 8×8×512"]
    E["Global Average Pooling:<br/>AdaptiveAvgPool2d <br/> → 1×1×512"]
    F["Flatten (→ 512)"]
    G1["Classifier:<br/>[Dropout(0.5)]<br/>Linear(512, 32)"]
    G2["Classifier:<br/>Linear(512, 32) <br/>+ BatchNorm <br/> + ReLU <br/> + Dropout(0.6) <br/> + Linear(512, 32)"]
    H["Output: 3 Logits"]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G1
    G1 --> G2
    G2 --> H

```
![Image](https://github.com/user-attachments/assets/a5b7fa5b-83f6-4c17-bb05-b73ac7e49db5)

<br><br>
## 학습 과정

- **데이터 분할:**  
  - 전체 데이터의 80%를 학습, 20%를 검증 데이터로 사용합니다.
- **손실 함수:**  
  - CrossEntropyLoss (다중 분류 문제에 적합)
- **최적화 알고리즘:**  
  - Adam Optimizer (learning rate=1e-3, weight_decay=1e-3)
- **학습률 스케줄링:**  
  - ReduceLROnPlateau: 검증 Loss 기준으로 학습률을 동적으로 조정합니다.
- **Early Stopping:**  
  - 검증 Loss 개선이 일정 에폭 동안 없을 경우 조기 종료를 통해 오버피팅을 방지합니다.
- **학습 에폭:**  
  - 최대 120 에폭 (Early Stopping 조건에 따라 조기 종료될 수 있음)

<br><br>
## 실행 방법

1. **환경 설정 및 의존성 설치**  
   Python 및 필요한 라이브러리(PyTorch, Torchvision, OpenCV, NumPy, Matplotlib, scikit-learn)를 설치합니다.
   ```bash
   pip install torch torchvision opencv-python numpy matplotlib scikit-learn

2. **데이터 준비**
   각 클래스 별로 `/image/go`, `/image/left`, `/image/right` 경로에 이미지 파일을 배치합니다.
   <br>이미지 파일 다운로드 [Click Here](https://drive.google.com/file/d/1aTDsimYZ3yXoyvhpsowJX1jH8MCZJUkK/view?usp=drive_link)


4. **코드 실행**
   학습 스크립트를 실행합니다.

    ```bash
   python model.py
