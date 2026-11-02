import streamlit as st

st.set_page_config(
    page_title="AI Box Market Evaluation",
    page_icon="📦",
    layout="wide",
)

st.title("CarPlay AI Box — Market Evaluation")
st.caption("Hold on custom Android↔CarPlay software. Evaluate the commercial AI Box path.")

st.success(
    "**Verdict:** Android does not speak Apple CarPlay natively. "
    "In the market, an **AI Box** (Android computer on the car’s wired CarPlay USB port) "
    "is the standard way to get Android apps on a CarPlay screen. "
    "**Buy hardware; don’t reverse-engineer CarPlay.**"
)

st.markdown(
    """
### How an AI Box works

1. Plugs into the factory **wired CarPlay / Android Auto data USB** port  
2. Head unit treats it as a **CarPlay-compatible device**  
3. Box boots its **own Android OS** on the factory screen  
4. Often also offers **wireless CarPlay + wireless Android Auto** for phones  

It is **not** a phone app, and **not** the same as a simple wireless dongle.
"""
)

st.subheader("Product comparison (consumer market)")

st.dataframe(
    {
        "Product": [
            "Carlinkit TBox Ultra",
            "Carlinkit TBox / Ambient",
            "Ottocast P3 / P3 Pro",
            "MMB Max 5.0",
            "CarBridgeX",
            "Ottocast i3 / Mekede",
            "Carlinkit T2C",
        ],
        "Best for": [
            "Default performance/value (6350)",
            "Mainstream wireless CP + AA",
            "Split-screen, GPS, SIM, HDMI",
            "Premium connectivity/storage",
            "Cheapest streaming",
            "BMW-specific",
            "Tesla-specific",
        ],
        "Chipset class": [
            "Qualcomm 6350",
            "6125 / 6225",
            "Mostly 6225",
            "QCM6225",
            "Budget",
            "BMW-tuned",
            "Tesla path",
        ],
        "Watch-outs": [
            "Wireless reconnect can flake",
            "Slower than Ultra",
            "Weak wireless CP/AA vs price",
            "Pricey",
            "Fewer features",
            "Only for BMW",
            "Only for Tesla",
        ],
    },
    hide_index=True,
    use_container_width=True,
)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**Needs**")
    st.markdown("- Wired CarPlay and/or wired AA\n- USB **data** port\n- Often Y-cable power")
with c2:
    st.markdown("**Won’t fix**")
    st.markdown("- Cars with no CP/AA at all\n- Replacing a head unit\n- Legal video-while-driving")
with c3:
    st.markdown("**Build vs buy**")
    st.markdown("- **Buy** the box\n- **Build** apps/launcher on it\n- **Don’t** build CarPlay protocol")

st.subheader("Decision tree")
st.code(
    """
Car has wired CarPlay or wired Android Auto?
├─ No  → AI Box won't help (need HU replacement / OEM)
└─ Yes
   ├─ BMW odd/wireless-only → BMW-specific box
   ├─ Tesla                 → T2C-class adapter
   └─ Normal car
      ├─ Best value/perf    → Carlinkit TBox Ultra (6350)
      ├─ Split-screen/SIM   → Ottocast P3 family
      └─ Budget streaming   → CarBridgeX-class
""".strip(),
    language="text",
)

st.info(
    "Full write-up: `docs/AIBOX_MARKET_EVALUATION.md`. "
    "Previous Android Auto demo under `android-car-connect/` is on hold."
)

st.markdown("### Waiting on direction")
choice = st.radio(
    "What should we do next?",
    [
        "Shortlist a box for a specific car (need make/model/year)",
        "Design software that runs on AI Box Android",
        "Park everything — evaluation only",
    ],
    index=2,
)
st.write(f"Selected (local UI only): **{choice}**")
