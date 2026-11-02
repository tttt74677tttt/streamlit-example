import streamlit as st

st.set_page_config(
    page_title="AI Box Market Evaluation",
    page_icon="📦",
    layout="wide",
)

st.title("CarPlay AI Box — Market Evaluation")
st.caption("Hold on custom Android↔CarPlay software. Focus: commercial AI Boxes.")

st.success(
    "**Yes — AI Boxes support wireless.** "
    "The box stays plugged into the car’s **wired** CarPlay/AA USB port; "
    "your **phone** connects **wirelessly** (CarPlay or Android Auto) over Bluetooth + Wi‑Fi."
)

st.subheader("Wireless model")
left, right = st.columns(2)
with left:
    st.markdown(
        """
**Box ↔ car** → wired USB (host)  
**Phone ↔ box** → **wireless**  
- iPhone → wireless CarPlay  
- Android → wireless Android Auto  

After first pairing, phones usually **auto-reconnect** each drive.
"""
    )
with right:
    st.code(
        """
[Phone]
   │  Bluetooth (pair) + Wi‑Fi (session)
   ▼
[AI Box]  ← Android apps / streaming
   │  USB wired CarPlay/AA
   ▼
[Factory head unit]
""".strip(),
        language="text",
    )

st.subheader("Wireless-capable picks")
st.dataframe(
    {
        "Product": [
            "Carlinkit TBox Ultra",
            "Carlinkit TBox / Ambient",
            "Ottocast P3 / P3 Pro",
            "MMB Max 5.0",
            "Ottocast i3 / Mekede",
            "Carlinkit T2C",
        ],
        "Wireless phone": [
            "CP + AA (best recent quality)",
            "CP + AA",
            "CP + AA (often softer/laggy)",
            "CP + AA",
            "BMW-specific wireless path",
            "Tesla path (not USB CarPlay host)",
        ],
        "Box still needs": [
            "Wired CP/AA USB",
            "Wired CP/AA USB",
            "Wired CP/AA USB",
            "Wired CP/AA USB",
            "BMW-compatible host",
            "Tesla-specific install",
        ],
    },
    hide_index=True,
    use_container_width=True,
)

st.warning(
    "Factory **wireless-only** cars (no wired USB CarPlay/AA host) usually "
    "**don’t** work with standard AI Boxes — BMW often needs a special SKU."
)

st.info("Details: `docs/AIBOX_MARKET_EVALUATION.md`")
