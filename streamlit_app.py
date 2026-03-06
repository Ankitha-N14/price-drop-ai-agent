 """
streamlit_app.py — Price Monitor Dashboard
Run: streamlit run streamlit_app.py
"""

import subprocess
import sys
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

import dashboard as db

st.set_page_config(page_title="Price Monitor", page_icon="💰", layout="wide")

st.markdown("""
<style>
.metric-card {
  background: linear-gradient(135deg,#1e3a5f,#2d6a9f);
  border-radius:12px; padding:20px 24px; color:white;
  box-shadow:0 4px 14px rgba(0,0,0,.3); margin-bottom:4px;
}
.metric-card h1 { font-size:2.4rem; margin:0; color:#7dd8ff; }
.metric-card p  { margin:4px 0 0; opacity:.8; font-size:.85rem; }
.alert-row { background:#fff3cd; border-left:4px solid #ffc107;
             padding:8px 14px; border-radius:4px; margin-bottom:6px; font-size:.9rem; }
.ok-row    { background:#d4edda; border-left:4px solid #28a745;
             padding:8px 14px; border-radius:4px; margin-bottom:6px; font-size:.9rem; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💰 Price Monitor")
    st.markdown("---")
    page = st.radio("", [
        "📊 Dashboard", "🛒 Products", "📈 Trends",
        "🔔 Alerts", "⚙️ Settings", "📋 Logs",
    ], label_visibility="collapsed")
    st.markdown("---")

    if st.button("▶️ Run Agent Now", use_container_width=True, type="primary"):
        with st.spinner("Running price check…"):
            try:
                r = subprocess.run(
                    [sys.executable, "-c",
                     "from agent import run_once, load_config; "
                     "from notifier import EmailNotifier; "
                     "run_once(load_config(), EmailNotifier())"],
                    capture_output=True, text=True, timeout=180,
                )
                if r.returncode == 0:
                    st.success("✅ Check complete!")
                else:
                    st.error(f"Error:\n{r.stderr[-400:]}")
            except subprocess.TimeoutExpired:
                st.warning("Timed out (>3 min). Check logs.")
            except Exception as e:
                st.error(str(e))

    if st.button("🔄 Refresh Page", use_container_width=True):
        st.rerun()

    st.caption(f"Refreshed: {datetime.now().strftime('%H:%M:%S')}")


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if page == "📊 Dashboard":
    st.title("📊 Dashboard")
    s     = db.summary_stats()
    cols  = st.columns(4)
    cards = [
        ("🛒", s["total_products"],  "Products Tracked"),
        ("🔍", s["checks_last_7d"],  "Checks (7 days)"),
        ("🔔", s["alerts_last_7d"],  "Alerts (7 days)"),
        ("✅", s["below_threshold"], "Below Threshold Now"),
    ]
    for col, (icon, val, label) in zip(cols, cards):
        with col:
            st.markdown(
                f'<div class="metric-card"><h1>{icon} {val}</h1><p>{label}</p></div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("Recent Price Checks")
        hist = db.load_history(days=7)
        if hist.empty:
            st.info("No data yet. Click **Run Agent Now** in the sidebar.")
        else:
            show = [c for c in ["timestamp","name","site","price","currency","threshold","alert_triggered"] if c in hist.columns]
            st.dataframe(hist[show].tail(40).sort_values("timestamp", ascending=False),
                         use_container_width=True, hide_index=True)

    with c2:
        st.subheader("Latest Alerts")
        alerts = db.alerts_history(days=7)
        if alerts.empty:
            st.markdown('<div class="ok-row">✅ No alerts — prices above threshold</div>', unsafe_allow_html=True)
        else:
            for _, r in alerts.tail(8).iterrows():
                name = str(r.get("name",""))[:40]
                cur  = r.get("currency","₹")
                price= r.get("price","?")
                ts   = str(r.get("timestamp",""))[:16]
                st.markdown(
                    f'<div class="alert-row">🔔 <b>{name}</b><br>{cur} {price} · {ts}</div>',
                    unsafe_allow_html=True,
                )


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🛒 Products":
    st.title("🛒 Products")

    prods = db.load_products()

    with st.expander("➕ Add New Product"):
        with st.form("add"):
            c1, c2 = st.columns(2)
            pid   = c1.text_input("Product ID", placeholder="P006")
            name  = c2.text_input("Name",       placeholder="iPhone 15")
            url   = st.text_input("URL (Amazon or Flipkart)", placeholder="https://www.amazon.in/dp/...")
            thr   = st.number_input("Alert Threshold (₹)", min_value=0.0, value=999.0, step=50.0)
            if st.form_submit_button("Add", type="primary"):
                if not pid or not url:
                    st.error("Product ID and URL are required.")
                elif not ("amazon" in url.lower() or "flipkart" in url.lower()):
                    st.error("Only Amazon.in and Flipkart URLs are supported.")
                elif not prods.empty and pid in prods["product_id"].astype(str).values:
                    st.error("Product ID already exists.")
                else:
                    db.add_product(pid, name, url, thr)
                    st.success(f"Added {pid}")
                    st.rerun()

    if prods.empty:
        st.info("No products yet.")
    else:
        edited = st.data_editor(
            prods, use_container_width=True, hide_index=True, num_rows="dynamic",
            column_config={
                "url":        st.column_config.LinkColumn("URL"),
                "threshold":  st.column_config.NumberColumn("Threshold ₹",  format="₹%.0f"),
                "last_price": st.column_config.NumberColumn("Last Price ₹", format="₹%.0f"),
            },
        )
        c1, c2 = st.columns([1, 6])
        if c1.button("💾 Save", type="primary"):
            db.save_products(edited)
            st.success("Saved!")
            st.rerun()

        st.markdown("---")
        ids = [""] + list(prods["product_id"].astype(str))
        del_id = st.selectbox("Delete product", ids)
        if del_id and st.button(f"🗑 Delete {del_id}"):
            db.delete_product(del_id)
            st.success("Deleted")
            st.rerun()

    if not prods.empty:
        st.download_button("⬇ Download products.csv",
                           prods.to_csv(index=False).encode(), "products.csv", "text/csv")


# ═══════════════════════════════════════════════════════════════════════════════
# TRENDS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Trends":
    st.title("📈 Price Trends")
    prods = db.load_products()
    if prods.empty:
        st.info("Add products first.")
        st.stop()

    options = {
        f"{r.get('product_id','')} — {str(r.get('name', r.get('url','')))[:55]}": r.get("product_id","")
        for _, r in prods.iterrows()
    }
    days  = st.slider("Window (days)", 1, 90, 30)
    label = st.selectbox("Product", list(options.keys()))
    pid   = options[label]
    trend = db.price_trend(pid, days)

    if trend.empty:
        st.info("No data for this product yet. Run the agent first.")
    else:
        fig = px.line(trend, x="timestamp", y="price",
                      title=f"Price History — {label}",
                      labels={"timestamp": "Date", "price": "Price (₹)"},
                      template="plotly_dark")
        fig.update_traces(line=dict(width=2.5, color="#00d4ff"))
        if trend["threshold"].notna().any():
            t = trend["threshold"].dropna().iloc[0]
            fig.add_hline(y=t, line_dash="dash", line_color="#ff5252",
                          annotation_text=f"Target ₹{t:,.0f}", annotation_position="top left")
        st.plotly_chart(fig, use_container_width=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Latest",  f"₹{trend['price'].iloc[-1]:,.0f}")
        c2.metric("Lowest",  f"₹{trend['price'].min():,.0f}")
        c3.metric("Highest", f"₹{trend['price'].max():,.0f}")

    st.markdown("---")
    st.subheader("All Products — Latest Prices")
    hist = db.load_history(days)
    if not hist.empty and "product_id" in hist.columns:
        latest = (hist.sort_values("timestamp")
                  .groupby("product_id").last().reset_index()
                  [["product_id","name","site","price","threshold","currency","timestamp"]])
        # Colour rows where price ≤ threshold
        def highlight(row):
            if pd.notna(row.get("price")) and pd.notna(row.get("threshold")) and row["price"] <= row["threshold"]:
                return ["background-color:#1a3a1a"] * len(row)
            return [""] * len(row)
        st.dataframe(latest.style.apply(highlight, axis=1),
                     use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ALERTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🔔 Alerts":
    st.title("🔔 Alert History")
    days   = st.slider("Look-back (days)", 1, 90, 30)
    alerts = db.alerts_history(days)

    if alerts.empty:
        st.success(f"No alerts in the last {days} days.")
    else:
        st.warning(f"**{len(alerts)} alert(s)** in the last {days} days")
        show = [c for c in ["timestamp","name","site","price","threshold","currency","url"] if c in alerts.columns]
        st.dataframe(alerts[show].sort_values("timestamp", ascending=False),
                     use_container_width=True, hide_index=True)
        fig = px.scatter(alerts, x="timestamp", y="price", color="name",
                         title="Alert Events", template="plotly_dark",
                         labels={"timestamp":"Time","price":"Price (₹)"})
        st.plotly_chart(fig, use_container_width=True)
        st.download_button("⬇ Download Alerts CSV",
                           alerts.to_csv(index=False).encode(), "alerts.csv", "text/csv")


# ═══════════════════════════════════════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    st.title("⚙️ Settings")
    cfg = db.load_config()

    st.subheader("🤖 Agent")
    c1, c2, c3 = st.columns(3)
    interval = c1.number_input("Check interval (s)", 60, 86400,
                                int(cfg.get("check_interval_seconds", 3600)), step=60)
    timeout  = c2.number_input("Request timeout (s)", 5, 60,
                                int(cfg.get("request_timeout", 20)))
    retries  = c3.number_input("Retry attempts", 1, 10,
                                int(cfg.get("retry_attempts", 3)))

    st.markdown("---")
    st.subheader("📧 Email (SMTP)")

    st.info(
        "**Gmail setup:** Go to Google Account → Security → "
        "[App Passwords](https://myaccount.google.com/apppasswords) → "
        "generate a password → paste below. Do NOT use your regular Gmail password."
    )

    c1, c2 = st.columns(2)
    sender   = c1.text_input("Sender Email",   value=cfg.get("EMAIL_SENDER",   ""))
    password = c2.text_input("App Password",   value=cfg.get("EMAIL_PASSWORD", ""), type="password")
    receiver = c1.text_input("Receiver Email", value=cfg.get("EMAIL_RECEIVER", "") or cfg.get("EMAIL_SENDER",""))
    smtp_host= c2.text_input("SMTP Host",      value=cfg.get("SMTP_HOST", "smtp.gmail.com"))
    smtp_port= c1.number_input("SMTP Port",    value=int(cfg.get("SMTP_PORT", 587)))

    c1, c2, c3 = st.columns(3)
    if c1.button("💾 Save Settings", type="primary"):
        db.save_config({
            "check_interval_seconds": interval,
            "request_timeout":        timeout,
            "retry_attempts":         retries,
            "EMAIL_SENDER":           sender,
            "EMAIL_PASSWORD":         password,
            "EMAIL_RECEIVER":         receiver,
            "SMTP_HOST":              smtp_host,
            "SMTP_PORT":              smtp_port,
        })
        st.success("Saved to config.json!")

    if c2.button("📨 Send Test Email"):
        from notifier import EmailNotifier
        ok = EmailNotifier().test()
        if ok:
            st.success("Test email sent! Check your inbox.")
        else:
            st.error("Failed — check the logs tab for details.")

    st.markdown("---")
    st.subheader("📤 Export")
    st.download_button("⬇ Full Price History CSV",
                       db.export_history_csv(), "price_history.csv", "text/csv")


# ═══════════════════════════════════════════════════════════════════════════════
# LOGS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Logs":
    st.title("📋 Agent Logs")
    n = st.slider("Lines", 50, 1000, 200, step=50)
    text = db.read_log(n)
    st.download_button("⬇ Download agent.log", text.encode(), "agent.log", "text/plain")
    st.code(text, language=None)
