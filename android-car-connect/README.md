# Car Connect (Android Auto)

Android companion that projects a driver-optimized **points of interest** experience to a compatible car display using Google’s official **Android for Cars App Library**.

## Important: CarPlay vs Android Auto

| Platform | Phone | How it works |
| --- | --- | --- |
| **Apple CarPlay** | iPhone only | Apple proprietary protocol — **not available on Android** |
| **Android Auto** | Android phone | Official Google projection to a compatible head unit |
| **Android Automotive OS** | Built into the car | App installs on the vehicle itself |

This project targets **Android Auto**. It does **not** reverse-engineer or implement Apple CarPlay.

## What’s included

- **Phone app** (`MainActivity`) — connection guidance + simulated connect/disconnect UI
- **Car app service** (`CarConnectService`) — discovered by the Android Auto host
- **Car screens** — nearby places map list, place details, navigate/call demo actions

## Open in Android Studio

1. Install [Android Studio](https://developer.android.com/studio) (Ladybug or newer recommended).
2. **File → Open** → select the `android-car-connect/` folder.
3. Let Gradle sync finish.
4. Run on a phone (API 28+) or emulator.

## Test with Android Auto Desktop Head Unit (DHU)

1. On the phone, enable **Developer mode** in the Android Auto app.
2. Start the **Desktop Head Unit** from the Android SDK extras.
3. Connect the phone over USB (or follow wireless DHU docs).
4. Launch **Car Connect** from the DHU app launcher.

For official steps, see [Test Android apps for cars](https://developer.android.com/training/cars/testing).

## Project layout

```
android-car-connect/
  app/src/main/java/com/example/carconnect/
    ui/MainActivity.kt          # Phone companion
    car/CarConnectService.kt    # Android Auto entry
    car/HomeScreen.kt           # POI map list on car display
    car/PlaceDetailScreen.kt    # Place actions
  app/src/main/res/xml/automotive_app_desc.xml
```

## Next steps you can ask for

- Media browser / now-playing integration
- Real places via Places API
- Wireless pairing deep-links into the Android Auto settings
- Android Automotive OS (AAOS) flavor of the same car screens
