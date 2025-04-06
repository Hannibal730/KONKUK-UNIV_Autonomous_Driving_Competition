# 건국대학교 주관 행동모사 자율주행 경진대회에서 1등을 수상한 딥러닝 모델


- #### **대회명:** 건국대학교 주관 행동모사 자율주행 경진대회
- #### **대회일:** 2024/06/27
- #### **내용:** 카메라로 촬영한 주행데이터를 기반으로 자율주행 딥러닝 모델 개발하고, 모델을 탑재한 1/10 size 자율주행 경주를 진행
- #### **주임교수:** 건국대학교 기계항공공학부 김창완
- #### **팀원:** 건국대학교 응용통계학과 최대승, 건국대학교 기계공학과 석승연
- #### **수상이력:** 1등 대상 [Click Here](https://www.konkuk.ac.kr/konkuk/2096/subview.do?enc=Zm5jdDF8QEB8JTJGYmJzJTJGa29ua3VrJTJGMjU3JTJGMTEzMTA1OCUyRmFydGNsVmlldy5kbyUzRg==)
  <img src="https://github.com/user-attachments/assets/6288de28-31e7-4c11-a0f6-63b9f097e01c" width="400" alt="Image">
----
<br>


## 1. 서론 (Introduction)

본 연구에서는 소규모 이미지(64×64)를 대상으로 전이학습(Transfer Learning)을 활용한 이미지 분류 파이프라인을 제안한다.
<br>
기존의 대형 네트워크가 소규모 입력에 대해 과도한 다운샘플링을 발생시키는 문제를 개선하기 위해, 사전 학습된 ResNet 모델의 입력 계층 및 출력 계층을 수정하고, 다양한 데이터 증강 기법을 적용하여 모델의 일반화 성능을 향상시키고자 한다.
<br>
최종적으로 제안하는 모델은 자율주행 차량에 탑재되어 세 개의 클래스로 구성된 분류 문제(예: go, left, right)를 해결한다.
<br>
챕터5에서는 직접 고안한 모델, 전이학습 원본 모델, 전이학습 수정 모델을 비교해가며 최적의 모델을 찾아가는 실험과정을 자세하게 설명한다.

---
<br>

## 2. 이미지 데이터 전처리 (Preprocess Image Data)

### 2.1 데이터 수집

  - 연습 트랙에서 자동차를  수동주행하면서 전방 카메라로 주행 데이터를 취득한다.
  - 취득한 데이터는 직진, 좌회전, 우회전으로 구분하고 각각 0, 1, 2로 라벨링한다.
  - 그리고 각각 `/image/go`, `/image/left`, `/image/right` 디렉토리에 저장한다.

### 2.2 데이터 전처리
  - **1. 원본 이미지:** 카메라로 캡처한 raw 이미지의 사이즈는 (1500, 1000)이며, 실제 모습과 비교하면 180도 회전된 상태이다.
  - **2. 회전:** 이미지를 180도 회전시킵니다. (`cv2.flip(frame, -1)` 사용)
  - **3. 초기 리사이즈:** ROI 추출을 용이하게 하기 위해 이미지를 (512, 512) 크기로 리사이즈합니다.
  - **4. ROI 생성:** 상단 200픽셀을 제거하여 ROI를 생성합니다. (`frame = frame[200:,:]`)
  - **5. 최종 리사이즈:** 추출된 ROI 이미지를 모델 입력 사이즈인 (64, 64)로 리사이즈한다.

|||||
|:---:|:---:|:---:|:---:|
|direction|go|left|right|
|Preprocessed <br> images|<img src="https://github.com/user-attachments/assets/95112164-7efa-46c3-af64-9926aae694b3" width="150" alt="Image">  |<img src="https://github.com/user-attachments/assets/85175b2b-5a76-460c-bf55-6e8d5ac9a00f" width="150" alt="Image">|<img src="https://github.com/user-attachments/assets/8ba87864-7ac3-47da-8831-2f9b69dc81dc" width="150" alt="Image">|


### 2.3 데이터 저장 디렉토리
 -  image <br>
  ├── go : 0으로 라벨링된 직진 이미지 <br>
  ├── left : 1로 라벨링된 좌회전 이미지  <br>
  └── right : 2로 라벨링링된 우회전 이미지

### 2.4 데이 파일 다운로드
- [Click Here](https://drive.google.com/file/d/1aTDsimYZ3yXoyvhpsowJX1jH8MCZJUkK/view?usp=drive_link)
---
<br>

## 3. 데이터 증강 (Dataset and Data Augmentation)
### 3.1 데이터셋
- **데이터 로드:**  
  - 각 클래스에 해당하는 이미지들은 `/image/go`, `/image/left`, `/image/right` 디렉토리에서 OpenCV를 통해 로드된다.
  - 이미지는 BGR 포맷으로 읽혀지며, 이후 RGB로 변환된다.
  - 데이터는 float32 형식으로 변환된 후, 픽셀 값이 [0,255]에서 [-1,1] 범위로 정규화된다.
- **데이터 규모:**  
  전체 8531개의 이미지가 구성되어있으며 학습과 검증에 사용된다.
- **데이터 분할:**  
  전체 데이터셋은 학습용과 검증용으로 8:2의 비율로 분할된다.

### 3.2 커스텀 데이터셋 클래스
- **클래스 설계:**  
  `CustomImageDataset` 클래스는 이미지와 대응 라벨을 함께 저장하며, 데이터 증강 및 전처리를 위한 transform을 선택적으로 적용한다.
  학습 데이터는 transform을 적용하고, 검증 데이터는 transform을 적용하지 않는다.

- **전처리 과정:**  
  transform이 지정된 경우, 정규화된 이미지([-1,1] 범위])를 복원하여 [0,255] 범위의 PIL 이미지로 변환한 후 지정된 transform을 적용한다.
  그렇지 않으면 NumPy 배열을 텐서 형식으로 변환한다.

### 3.4 데이터 증강 (Data Augmentation)
- **데이터 증강 기법:**  
  학습 데이터에 적용된 증강은 모델이 다양한 입력 변형에 강인해지도록 돕는다. 사용한 기법들은 다음과 같다:

  1. **RandomRotation (최대 20도 회전):**  
     - **설명:** 이미지가 무작위로 -20도에서 +20도 사이에서 회전된다.  
     - **효과:** 회전된 이미지에서도 동일한 클래스를 인식할 수 있도록 하여, 방향 변화에 대한 모델의 강인성을 향상시킨다.
  
  2. **RandomAffine (최대 5% 평행 이동):**  
     - **설명:** 회전(degrees=0)은 수행하지 않고, 이미지가 가로와 세로 방향으로 최대 5%까지 평행 이동된다.  
     - **효과:** 객체의 위치 변화에 대응할 수 있도록 학습시켜, 위치 불변성을 높인다.
  
  3. **RandomResizedCrop (크롭 후 재조정):**  
     - **설명:** 원본 이미지의 임의의 부분을 크롭한 후, 64×64 크기로 재조정한다.  
     - **효과:** 다양한 구도와 크기를 가진 이미지 조각에 대해 학습하여, 카메라 각도의 미세한 변화에 대한 강인성을 향상시킨다.
  
  4. **ToTensor (텐서 변환):**  
     - **설명:** PIL 이미지 또는 NumPy 배열을 PyTorch 텐서로 변환하며, 자동으로 픽셀 값을 [0,1] 범위로 조정한다.
  
  5. **Normalize (정규화):**  
     - **설명:** ImageNet 데이터셋에서 사용된 평균([0.485, 0.456, 0.406])과 표준편차([0.229, 0.224, 0.225])로 각 채널별 정규화를 진행한다.  
     - **효과:** 사전학습된 모델과의 일관성을 유지하여 전이학습 효과를 극대화한다.
  
- **검증 데이터 처리:**  
  검증 데이터에는 데이터 증강 기법을 적용하지 않고, 단순히 ToTensor와 Normalize만 적용된다. 이는 모델 성능 평가 시 원본 이미지의 특성을 그대로 반영하기 위함이다.

---
<br>

## 4. 모델 아키텍처 및 수정 (Model Architecture and Modifications)

### 4.1 전이학습 모델 선택
- **모델 선택:**  
  사전학습된 ResNet 모델(ResNet-18 또는 ResNet-34)을 사용하며, 코드에서는 ResNet-18 기반의 전이학습을 기본으로 한다.
- **가중치 다운로드:**  
  PyTorch Hub를 통해 ImageNet으로 사전 학습된 가중치를 다운로드하여 초기 모델 파라미터로 사용한다.

### 4.2 네트워크 수정
- **입력 계층 수정:**  
  원래 ResNet의 첫 번째 합성곱 계층은 7×7 커널, stride=2, padding=3으로 설정되어 있으나, 이는 64×64 이미지에서는 과도한 다운샘플링을 발생시킨다.  
  → 따라서 첫 번째 conv layer를 3×3 커널, stride=1, padding=1로 재설정하여 해상도 손실을 줄인다.
  
- **MaxPool 레이어 제거:**  
  첫 번째 maxpool 계층을 Identity 함수로 대체하여, 초기 입력 해상도가 유지되도록 한다.
  
- **출력 계층 수정:**  
  기존의 1000 클래스 출력 대신, 중간 hidden layer(크기 32)를 포함한 Fully Connected (FC) 레이어 구조로 변경한다.  
  - 배치 정규화, ReLU 활성화, 드롭아웃(비율 0.6)을 적용하여 과적합을 방지하고 모델의 일반화 능력을 향상시킨다.
  - 최종 출력은 3개의 클래스에 맞게 구성된다.

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


---
<br>

## 5. 학습 전략 (Training Strategy)

### 5.1 학습 환경 및 디바이스 설정
- **디바이스:**  
  CUDA 사용 가능 시 GPU를, 그렇지 않으면 CPU를 활용하여 학습을 진행한다.

### 5.2 손실 함수 및 옵티마이저 설정
- **손실 함수:**  
  다중 분류 문제에 적합한 CrossEntropyLoss를 사용한다.
- **옵티마이저:**  
  Adam 옵티마이저를 사용하며, 초기 학습률은 1e-3, weight_decay는 1e-3로 설정된다.

### 5.3 학습률 스케줄링 및 조기 종료
- **학습률 스케줄러:**  
  ReduceLROnPlateau를 사용하여 검증 손실이 개선되지 않을 경우 학습률에 0.1씩 곱한다.
- **조기 종료 (Early Stopping):**  
  최대 120 에폭 동안 학습을 진행하며, 검증 손실이 개선되지 않으면 설정한 patience 이후 조기 종료를 수행한다. 가장 우수한 모델 가중치를 저장한 후, 최종 평가에 사용한다.

### 5.4 학습 루프 및 로그 기록
- **학습 단계:**  
  각 에폭마다 학습 데이터셋을 통해 손실과 정확도를 계산하고, 옵티마이저를 통해 모델 파라미터를 업데이트한다.
- **검증 단계:**  
  에폭 종료 후, 검증 데이터셋을 통해 모델 성능(손실 및 정확도)을 평가하며, 학습률 스케줄러에 해당 값을 전달하여 학습률을 조정한다.
- **로그 출력:**  
  에폭마다 현재 학습 손실, 검증 손실, 학습 및 검증 정확도, 학습률을 출력하여 학습 진행 상황을 모니터링한다.

---
<br>

## 6. 실험 및 파라미터 튜닝(Experiments and Parameter Tuning)

### 6.1 실험 과정
- 직접 설계한 모델에서 전이학습 활용 모델까지의 실험 과정

||||||
|:---:|:---:|:---:|:---:|:---:|
|1|2|3|4|5|
|![Image](https://github.com/user-attachments/assets/c3576f7f-ec99-49de-8e85-1ab2f5c5ea8e)|![Image](https://github.com/user-attachments/assets/b5c82881-c747-4dac-971c-2b28b217ca55)|![Image](https://github.com/user-attachments/assets/25129819-f665-46da-ba8b-cb1020751454)|![Image](https://github.com/user-attachments/assets/c081ffa6-8505-40ef-b466-5be5281d37b5)|![Image](https://github.com/user-attachments/assets/55edc841-b98f-46ba-85fa-498c7ff54b0f)|
||||||
|6|7|8|9|10|
|![Image](https://github.com/user-attachments/assets/912684d8-a1e9-4adf-99c4-4477c633e6fc)|![Image](https://github.com/user-attachments/assets/7d045543-033e-4222-8a6c-27cc9450006c)|![Image](https://github.com/user-attachments/assets/c826b9c0-e07a-47bb-ae3e-958fc485e993)|![Image](https://github.com/user-attachments/assets/2f31b431-8337-4049-aa48-da4bcc9d2e4c)|![Image](https://github.com/user-attachments/assets/fca806ee-93e9-4378-a196-d7dfed50bda0)|
||||||
|11|12|13|14|15|
|![Image](https://github.com/user-attachments/assets/da966e73-111d-47de-80ed-bbdbf2b25b06)|![Image](https://github.com/user-attachments/assets/d081e5ba-6e3b-45af-8fb4-fd0e485edab0)|![Image](https://github.com/user-attachments/assets/1370e4f4-82e9-4124-a530-03111bce1070)|![Image](https://github.com/user-attachments/assets/044a2fd8-79b8-4d7b-8ccf-09e31f6ccec5)|![Image](https://github.com/user-attachments/assets/c9c071d5-f407-430d-817a-4c586f701aeb)|
||||||
|16|17|18|19|20|
|![Image](https://github.com/user-attachments/assets/ef1c948a-383b-40d0-900a-be4f163b3c9b)|![Image](https://github.com/user-attachments/assets/49d357ed-3aa7-4930-a044-8c2ea6860700)|![Image](https://github.com/user-attachments/assets/5ec0f562-f645-41ef-b866-622c399c5d3e)|![Image](https://github.com/user-attachments/assets/73ab3b16-5964-4401-a565-b981563bcbfe)|![Image](https://github.com/user-attachments/assets/59b81288-9da0-4e20-9b34-a818a018db47)|
||||||
|21|22|23|24|25|
|![Image](https://github.com/user-attachments/assets/3b1016c0-c9e2-43bb-bb58-19dcba555812)|![Image](https://github.com/user-attachments/assets/be389cb8-70ec-4315-bb1f-980d5d9d91a0)|![Image](https://github.com/user-attachments/assets/13840fec-c408-4997-ad1a-244af4a36dfd)|![Image](https://github.com/user-attachments/assets/2a7e3240-37fa-466f-9a58-8b7dccaa67c2)|![Image](https://github.com/user-attachments/assets/ce3cecb4-3064-4621-8ee8-8b18243af2c4)|
||||||
|26|27|28|29|30|
|![Image](https://github.com/user-attachments/assets/43c91944-2c0b-45b2-9b01-fe9156c32a60)|![Image](https://github.com/user-attachments/assets/a7a7dd91-3cce-47c1-8e46-4e724822bf22)|![Image](https://github.com/user-attachments/assets/3a86c501-1fab-4782-9159-097e57bc7d20)|![Image](https://github.com/user-attachments/assets/e9a1b41c-06bc-41d8-986d-6177c6608650)|![Image](https://github.com/user-attachments/assets/10e9df58-fd60-4c86-9afa-c1b945e6f636)|
||||||



---
<br>

## 7. 결과 시각화 및 최종 평가 (Results Visualization and Final Evaluation)

### 7.1 학습 곡선 시각화
- **손실 곡선:**  
  Matplotlib을 활용하여 에폭별 학습 손실과 검증 손실을 그래프로 시각화한다.
- **정확도 곡선:**  
  학습 정확도와 검증 정확도의 변화를 별도의 그래프로 나타내어, 모델의 수렴 및 일반화 성능을 직관적으로 확인할 수 있다.

### 7.2 최종 모델 평가
- **최적 모델 선택:**  
  조기 종료 기준에 따라 저장된 최적의 모델 가중치를 불러와 최종 평가를 진행한다.
- **평가 지표:**  
  전체 검증 데이터셋에 대해 최종 손실과 정확도를 계산하여 모델의 성능을 정량적으로 평가한다.

---
<br>

## 8. 결론 (Conclusion)

본 연구에서는 전이학습 기반의 ResNet 모델을 소규모 이미지 분류 문제에 효과적으로 적용하기 위한 종합적인 파이프라인을 제안하였다.  
- **주요 기여:**  
  - 소규모 이미지에 적합한 입력 계층 수정 및 maxpool 제거를 통한 해상도 보존  
  - 다양한 데이터 증강 기법(RandomRotation, RandomAffine, RandomResizedCrop 등)을 적용하여 모델의 일반화 성능 강화  
  - 사전 학습된 모델을 기반으로 한 출력 계층 수정 및 안정적인 학습 전략(학습률 스케줄링, 조기 종료) 구현  
- **실험 결과:**  
  제안한 방법을 통해 학습 과정에서 손실 및 정확도 변화를 면밀히 모니터링하였으며, 최종 평가에서 우수한 분류 성능을 확인할 수 있었다.
- **향후 연구 방향:**  
  다양한 데이터 증강 방법에 대해서 계획적으로 실험하는 방법을 공부하고 싶다.

---


```mermaid
flowchart TD
  A["Input Image\n64x64x3"] --> B["Conv2d\n3 → 64, 3x3, padding=1"]
  B --> C["ReLU"]
  C --> D["MaxPool2d\nkernel=2, stride=2\n(Output: 32x32x64)"]
  
  D --> E["Conv2d\n64 → 128, 3x3, padding=1"]
  E --> F["ReLU"]
  F --> G["MaxPool2d\nkernel=2, stride=2\n(Output: 16x16x128)"]
  
  G --> H["Conv2d\n128 → 256, 3x3, padding=1"]
  H --> I["ReLU"]
  I --> J["MaxPool2d\nkernel=2, stride=2\n(Output: 8x8x256)"]
  
  J --> K["Flatten\n(16384 dims)"]
  K --> L["Linear\n16384 → 64"]
  L --> M["ReLU"]
  M --> N["Linear\n64 → num_classes (3)"]
  N --> O["Output"]

```

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