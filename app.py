import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Office 365 Quarantine Mail Tracker",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Office 365 Quarantine Mail Intelligence")
st.caption("Upload your Defender quarantine Excel/CSV exports to track, filter, and prune mail records.")

# --- SIDEBAR: Upload & Filters ---
st.sidebar.header("📁 Report Upload & Settings")
uploaded_file = st.sidebar.file_uploader(
    "Upload O365 Quarantine Export (.xlsx or .csv)",
    type=["xlsx", "xls", "csv"]
)

# Days retention cutoff (as per request: remove older ones, keep new ones)
prune_days = st.sidebar.slider("Retention Window (Keep Last N Days)", min_value=1, max_value=30, value=7)

# --- Sample Data Generator for Instant Preview ---
def get_sample_data():
    now = datetime.now()
    return pd.DataFrame([
        {
            "Received": (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "Sender": "billing-update@suspicious-bank-auth.com",
            "Recipient": "cfo@company.com",
            "Subject": "Urgent: Wire Transfer #8942 Authorization",
            "Quarantine Reason": "Phish",
            "Policy Type": "Anti-phish",
            "Expires": (now + timedelta(days=15)).strftime("%Y-%m-%d")
        },
        {
            "Received": (now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S"),
            "Sender": "invoice-doc@malicious-payload.xyz",
            "Recipient": "accounts@company.com",
            "Subject": "Invoice_Nov2026.pdf.exe",
            "Quarantine Reason": "Malware",
            "Policy Type": "Safe Attachments",
            "Expires": (now + timedelta(days=15)).strftime("%Y-%m-%d")
        },
        {
            "Received": (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "Sender": "promotions@global-marketing-blast.biz",
            "Recipient": "marketing@company.com",
            "Subject": "Exclusive Black Friday B2B SaaS Discounts",
            "Quarantine Reason": "High Confidence Spam",
            "Policy Type": "Anti-spam",
            "Expires": (now + timedelta(days=14)).strftime("%Y-%m-%d")
        },
        {
            "Received": (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "Sender": "newsletter@partner-updates.org",
            "Recipient": "info@company.com",
            "Subject": "Weekly Tech Insights Roundup #42",
            "Quarantine Reason": "Bulk",
            "Policy Type": "Anti-spam",
            "Expires": (now + timedelta(days=13)).strftime("%Y-%m-%d")
        },
        {
            "Received": (now - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"),
            "Sender": "service-notice@cloud-host-alert.ru",
            "Recipient": "it-admin@company.com",
            "Subject": "Your Cloud Server Storage Quota Exceeded",
            "Quarantine Reason": "Phish",
            "Policy Type": "Anti-phish",
            "Expires": (now + timedelta(days=11)).strftime("%Y-%m-%d")
        },
        {
            "Received": (now - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S"),
            "Sender": "legacy-promo@old-vendor.net",
            "Recipient": "purchasing@company.com",
            "Subject": "Old Archived Catalog Notice",
            "Quarantine Reason": "Spam",
            "Policy Type": "Anti-spam",
            "Expires": (now + timedelta(days=5)).strftime("%Y-%m-%d")
        }
    ])

# Load either uploaded file or sample data
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.sidebar.success(f"Loaded {len(df)} records from {uploaded_file.name}")
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")
        df = get_sample_data()
else:
    st.info("💡 Showing sample Office 365 Quarantine data. Upload your own export using the sidebar anytime!")
    df = get_sample_data()

# Normalize column names for flexible O365 export schemas
col_map = {}
for col in df.columns:
    c_lower = col.lower()
    if "received" in c_lower or "date" in c_lower or "time" in c_lower:
        col_map[col] = "Received"
    elif "sender" in c_lower or "from" in c_lower:
        col_map[col] = "Sender"
    elif "recipient" in c_lower or "to" in c_lower:
        col_map[col] = "Recipient"
    elif "subject" in c_lower:
        col_map[col] = "Subject"
    elif "reason" in c_lower or "type" in c_lower or "threat" in c_lower:
        if "Quarantine Reason" not in col_map.values():
            col_map[col] = "Quarantine Reason"
    elif "expire" in c_lower:
        col_map[col] = "Expires"

df = df.rename(columns=col_map)

# Convert Received column to datetime for filtering & pruning
if "Received" in df.columns:
    df["Received_dt"] = pd.to_datetime(df["Received"], errors="coerce")
    cutoff_date = datetime.now() - timedelta(days=prune_days)
    # Prune older records
    df = df[df["Received_dt"] >= cutoff_date]
    df["Received"] = df["Received_dt"].dt.strftime("%Y-%m-%d %H:%M")

# Filter by Quarantine Reason in Sidebar
if "Quarantine Reason" in df.columns:
    all_reasons = sorted(list(df["Quarantine Reason"].dropna().unique()))
    selected_reasons = st.sidebar.multiselect("Filter by Threat / Reason", all_reasons, default=all_reasons)
    df = df[df["Quarantine Reason"].isin(selected_reasons)]

# Search box filter
search_term = st.sidebar.text_input("🔍 Search Sender / Subject", "")
if search_term:
    search_lower = search_term.lower()
    mask = df["Sender"].astype(str).str.lower().str.contains(search_lower) | \
           df["Subject"].astype(str).str.lower().str.contains(search_lower)
    df = df[mask]

# --- KPI METRIC CARDS ---
m1, m2, m3, m4 = st.columns(4)
total_count = len(df)
phish_count = len(df[df["Quarantine Reason"].astype(str).str.contains("Phish|Malware", case=False, na=False)]) if "Quarantine Reason" in df.columns else 0
spam_count = len(df[df["Quarantine Reason"].astype(str).str.contains("Spam", case=False, na=False)]) if "Quarantine Reason" in df.columns else 0
bulk_count = len(df[df["Quarantine Reason"].astype(str).str.contains("Bulk", case=False, na=False)]) if "Quarantine Reason" in df.columns else 0

m1.metric("Active in Retention", total_count)
m2.metric("Critical (Phish / Malware)", phish_count, delta="High Risk", delta_color="inverse")
m3.metric("Spam Detections", spam_count)
m4.metric("Bulk Marketing", bulk_count)

# --- VISUAL CHARTS ---
c1, c2 = st.columns([1, 1])

with c1:
    st.subheader("📊 Quarantine Reasons Breakdown")
    if "Quarantine Reason" in df.columns and not df.empty:
        reason_counts = df["Quarantine Reason"].value_counts()
        st.bar_chart(reason_counts)
    else:
        st.write("No data available.")

with c2:
    st.subheader("📅 Inflow Over Time")
    if "Received_dt" in df.columns and not df.empty:
        df["Date_Only"] = df["Received_dt"].dt.date
        date_counts = df.groupby("Date_Only").size()
        st.line_chart(date_counts)
    else:
        st.write("No date data available.")

# --- SUCCINCT INTERACTIVE TABLE ---
st.subheader("📋 Quarantined Messages Table")

display_cols = [c for c in ["Received", "Sender", "Recipient", "Subject", "Quarantine Reason", "Expires"] if c in df.columns]
if not df.empty:
    st.dataframe(
        df[display_cols],
        use_container_width=True,
        hide_index=True
    )
    
    # Export pruned & filtered dataset
    csv_data = df[display_cols].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Filtered Report (CSV)",
        data=csv_data,
        file_name=f"quarantine_report_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
else:
    st.warning("No records match your selected filters.")
