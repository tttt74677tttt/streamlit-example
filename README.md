# Car Connect

Starter project for connecting an **Android** phone to a car display.

> **Apple CarPlay is iPhone-only.** Android phones use **Android Auto**.
> This repository implements an Android Auto car app demo — it does not implement CarPlay.

## Contents

| Path | What it is |
| --- | --- |
| [`android-car-connect/`](android-car-connect/) | Android Studio project (phone companion + Android Auto car screens) |
| [`streamlit_app.py`](streamlit_app.py) | Short web overview of CarPlay vs Android Auto |
| [`android-car-connect/README.md`](android-car-connect/README.md) | Build & Desktop Head Unit testing guide |

## Run the overview (Streamlit)

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Build the Android app

1. Open `android-car-connect/` in Android Studio.
2. Run on a device/emulator (min API 28).
3. Test car projection with the Android Auto Desktop Head Unit.

Details: [android-car-connect/README.md](android-car-connect/README.md).
