# Car Connect / AI Box evaluation

## Status: HOLD on custom CarPlay bridge

Android phones **cannot** natively connect to Apple CarPlay. The consumer-market solution is a **CarPlay AI Box** (hardware), not a phone app.

See the evaluation:

- **[`docs/AIBOX_MARKET_EVALUATION.md`](docs/AIBOX_MARKET_EVALUATION.md)** — full market analysis  
- **`streamlit run streamlit_app.py`** — interactive summary  

### Quick verdict

| Goal | Path |
| --- | --- |
| Android apps on a CarPlay car screen | **Buy an AI Box** (e.g. Carlinkit TBox Ultra) |
| Official phone projection on Android cars | Android Auto (car must support it) |
| Build our own CarPlay USB endpoint | **Not recommended** |

### Also in this repo (on hold)

[`android-car-connect/`](android-car-connect/) — earlier Android Auto demo. Paused while we evaluate AI Boxes.
