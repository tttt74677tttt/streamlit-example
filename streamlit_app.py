import streamlit as st

st.set_page_config(
    page_title="Car Connect",
    page_icon="🚗",
    layout="wide",
)

st.title("Car Connect")
st.caption("Android → car display via Android Auto (not Apple CarPlay)")

st.markdown(
    """
### Can Android connect to CarPlay?

**No.** Apple CarPlay is proprietary and works only with iPhone.
On Android, the supported way to use a car's display is **Android Auto**
(or apps built for **Android Automotive OS** when the car runs Android natively).

This repo includes a starter Android project that does the legitimate thing:
project a driver-optimized POI experience through the official
[Android for Cars App Library](https://developer.android.com/training/cars/apps/library).
"""
)

left, right = st.columns(2)

with left:
    st.subheader("Android project")
    st.markdown(
        """
Open `android-car-connect/` in **Android Studio**, then:

1. Sync Gradle  
2. Run on a phone (API 28+)  
3. Test with the **Desktop Head Unit (DHU)** for Android Auto  

Phone UI covers USB / wireless setup tips and a simulated connection state.
The car display UI shows nearby places (fuel, coffee, parking, EV charging).
"""
    )

with right:
    st.subheader("Architecture")
    st.code(
        """
Phone app (MainActivity)
        │
        │  USB / Wireless
        ▼
Android Auto host (car / DHU)
        │
        ▼
CarConnectService → Session → Screens
  • HomeScreen (PlaceListMap)
  • PlaceDetailScreen
  • MessageScreen
""".strip(),
        language="text",
    )

st.subheader("Quick comparison")
st.dataframe(
    {
        "System": ["Apple CarPlay", "Android Auto", "Android Automotive OS"],
        "Phone": ["iPhone", "Android", "N/A (runs in car)"],
        "Supported here": ["No", "Yes (demo)", "Possible follow-up"],
    },
    hide_index=True,
    use_container_width=True,
)

st.info(
    "See `android-car-connect/README.md` for build and DHU testing steps."
)
