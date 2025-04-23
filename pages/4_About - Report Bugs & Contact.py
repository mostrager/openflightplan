import streamlit as st

st.set_page_config(page_title="About - OpenFlightPlan", layout="centered")

st.title("📱 OpenFlightPlan.io")
st.subheader("Free, mobile-optimized flight planning for orthomosaics & 3D models")

st.markdown("""
OpenFlightPlan is a **fully free, open-source flight planning tool** designed to run directly on your phone, tablet, or laptop — no paid plans, no logins, and no desktop-only interfaces.

---

### 🔥 Why Use OpenFlightPlan?

- **✅ Truly Free:** All premium-level features available with no account or payment.
- **✅ Field-Ready:** Create missions directly from your phone in real-time.
- **✅ Open Source:** Transparent, community-supported, and contribution-friendly.
- **✅ 3D + Ortho Support:** Fully supports photogrammetry mission types.

---

### 💡 How It’s Different

Unlike tools like DroneLink, Pix4Dcapture, or WaypointMap:
- No feature limits
- No paywalls
- No locked export formats

You own your missions. You fly how you want.

---

### 🛠 Got ideas or bugs?

- 💡 [Request a feature](https://github.com/mostrager/mobile-flight-planner/issues/new?template=feature_request.md)
- 🐞 [Report a bug](https://github.com/mostrager/mobile-flight-planner/issues/new?template=bug_report.md)
- 📂 [Browse all issues](https://github.com/mostrager/mobile-flight-planner/issues)

Want to contribute code or improve documentation? Check us out on [GitHub](https://github.com/mostrager/mobile-flight-planner)


Made with 💻 and 📡 by people tired of paying for open skies.
""")

import requests

st.markdown("---")
st.subheader("📬 Contact / Support")

with st.form("contact_form"):
    name = st.text_input("Your Name")
    email = st.text_input("Your Email")
    message = st.text_area("Message")

    submitted = st.form_submit_button("Send")

    if submitted:
        formspree_url = "https://formspree.io/f/mblorgyq"  
        payload = {
            "name": name,
            "email": email,
            "message": message
        }

        response = requests.post(formspree_url, data=payload)

        if response.status_code == 200:
            st.success("✅ Message sent successfully! I’ll be in touch soon.")
        else:
            st.error(f"⚠️ Failed to send. (Error {response.status_code}) Please try again later.")
