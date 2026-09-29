import re

# 1. Update password_health.py
with open("pages/password_health.py", "r", encoding="utf-8") as f:
    ph_text = f.read()

ph_new_css = """def load_css():
    from utils.theme import inject_cyber_theme
    inject_cyber_theme()
    st.markdown('''
    <style>
        .report-title {
            font-size: 26px;
            font-weight: 800;
            color: #f8fafc;
            margin-bottom: 4px;
            letter-spacing: -0.4px;
        }
        .report-subtitle {
            color: #94a3b8;
            font-size: 13.5px;
            margin-bottom: 20px;
        }
        .section-title {
            font-size: 15px;
            font-weight: 700;
            color: #f8fafc;
            margin-top: 18px;
            margin-bottom: 12px;
        }
        .report-card {
            border: 1px solid rgba(56, 189, 248, 0.18);
            border-radius: 14px;
            padding: 20px;
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(14px);
            margin-bottom: 12px;
        }
        .report-score {
            font-size: 54px;
            font-weight: 800;
            text-align: center;
            line-height: 1;
            font-family: 'JetBrains Mono', monospace;
        }
        .report-score-label {
            text-align: center;
            color: #94a3b8;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .report-status {
            text-align: center;
            font-size: 17px;
            font-weight: 700;
            margin-top: 8px;
        }
        .report-info {
            border: 1px solid rgba(56, 189, 248, 0.15);
            border-radius: 12px;
            padding: 14px;
            text-align: center;
            min-height: 85px;
            background: rgba(15, 23, 42, 0.65);
        }
        .report-info-value {
            font-size: 24px;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
        }
        .report-info-label {
            color: #94a3b8;
            font-size: 12px;
            margin-top: 4px;
        }
        .finding {
            border: 1px solid rgba(56, 189, 248, 0.15);
            border-radius: 10px;
            padding: 12px 16px;
            margin-bottom: 8px;
            font-size: 13.5px;
            background: rgba(15, 23, 42, 0.65);
            color: #cbd5e1;
        }
    </style>
    ''', unsafe_allow_html=True)"""

ph_updated = re.sub(r'def load_css\(\):.*?(?=\n# ============================================================)', ph_new_css, ph_text, flags=re.DOTALL)
with open("pages/password_health.py", "w", encoding="utf-8") as f:
    f.write(ph_updated)
print("Updated password_health.py")


# 2. Update my_vault.py
with open("pages/my_vault.py", "r", encoding="utf-8") as f:
    mv_text = f.read()

mv_new_css = """def load_css():
    from utils.theme import inject_cyber_theme
    inject_cyber_theme()
    st.markdown('''
    <style>
        .vault-title {
            font-size: 26px;
            font-weight: 800;
            color: #f8fafc;
            letter-spacing: -0.4px;
            margin-bottom: 4px;
        }
        .vault-subtitle {
            font-size: 13.5px;
            color: #94a3b8;
            margin-bottom: 20px;
        }
        .vault-info {
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(56, 189, 248, 0.18);
            border-radius: 12px;
            padding: 14px 18px;
            margin: 14px 0 18px 0;
            color: #94a3b8;
            font-size: 13px;
        }
        .password-card {
            background: rgba(15, 23, 42, 0.65);
            border: 1px solid rgba(56, 189, 248, 0.14);
            border-radius: 10px;
            padding: 10px 14px;
            margin-bottom: 6px;
            min-height: 44px;
            display: flex;
            align-items: center;
        }
        .password-title {
            color: #f8fafc;
            font-size: 13.5px;
            font-weight: 600;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .password-value {
            color: #cbd5e1;
            font-size: 13px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .password-url {
            color: #38bdf8;
            font-size: 13px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .table-header {
            color: #94a3b8;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            padding: 0 5px 8px 5px;
        }
        .delete-warning {
            background: rgba(244, 63, 94, 0.12);
            border: 1px solid rgba(244, 63, 94, 0.35);
            border-radius: 12px;
            padding: 16px 20px;
            margin: 14px 0;
            color: #fb7185;
            font-size: 13.5px;
        }
    </style>
    ''', unsafe_allow_html=True)"""

mv_updated = re.sub(r'def load_css\(\):.*?(?=\n# ============================================================)', mv_new_css, mv_text, flags=re.DOTALL)
with open("pages/my_vault.py", "w", encoding="utf-8") as f:
    f.write(mv_updated)
print("Updated my_vault.py")


# 3. Update view_password.py
with open("pages/view_password.py", "r", encoding="utf-8") as f:
    vp_text = f.read()

vp_new_css = """def load_css():
    from utils.theme import inject_cyber_theme
    inject_cyber_theme()
    st.markdown('''
    <style>
        .vault-title {
            font-size: 26px;
            font-weight: 800;
            color: #f8fafc;
            letter-spacing: -0.4px;
            margin-bottom: 4px;
        }
        .vault-subtitle {
            font-size: 13.5px;
            color: #94a3b8;
            margin-bottom: 20px;
        }
        .detail-card {
            background: rgba(15, 23, 42, 0.75);
            border: 1px solid rgba(56, 189, 248, 0.18);
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 15px;
        }
        .detail-label {
            font-size: 11px;
            color: #94a3b8;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            margin-bottom: 5px;
        }
        .detail-value {
            font-size: 14px;
            color: #f8fafc;
            margin-bottom: 18px;
            word-break: break-word;
        }
        .password-box {
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid rgba(56, 189, 248, 0.22);
            border-radius: 10px;
            padding: 12px 16px;
            color: #38bdf8;
            font-size: 15px;
            font-family: 'JetBrains Mono', monospace;
            margin-bottom: 12px;
            word-break: break-all;
        }
        .metadata-card {
            background: rgba(15, 23, 42, 0.65);
            border: 1px solid rgba(56, 189, 248, 0.15);
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 15px;
        }
    </style>
    ''', unsafe_allow_html=True)"""

vp_updated = re.sub(r'def load_css\(\):.*?(?=\n# ============================================================)', vp_new_css, vp_text, flags=re.DOTALL)
with open("pages/view_password.py", "w", encoding="utf-8") as f:
    f.write(vp_updated)
print("Updated view_password.py")


# 4. Update add_password.py if load_css exists
with open("pages/add_password.py", "r", encoding="utf-8") as f:
    ap_text = f.read()

if "def load_css" in ap_text:
    ap_new_css = """def load_css():
    from utils.theme import inject_cyber_theme
    inject_cyber_theme()"""
    ap_updated = re.sub(r'def load_css\(\):.*?(?=\n# ============================================================)', ap_new_css, ap_text, flags=re.DOTALL)
    with open("pages/add_password.py", "w", encoding="utf-8") as f:
        f.write(ap_updated)
    print("Updated add_password.py")
else:
    # If no load_css, make sure inject_cyber_theme is called
    if "inject_cyber_theme" not in ap_text:
        ap_updated = "from utils.theme import inject_cyber_theme\n" + ap_text
        ap_updated = ap_updated.replace("def show(user):", "def show(user):\n    inject_cyber_theme()")
        with open("pages/add_password.py", "w", encoding="utf-8") as f:
            f.write(ap_updated)
        print("Updated add_password.py with inject_cyber_theme")
