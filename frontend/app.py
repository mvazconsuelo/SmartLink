"""SmartLink dashboard (Streamlit).

The frontend only talks to the SmartLink API over HTTP. It never touches D1:
the API is the single owner of the data and the business rules.
"""

from __future__ import annotations

import os
from datetime import date, timedelta

import pandas as pd
import requests
import streamlit as st

API_URL = os.environ.get("API_URL", "http://localhost:8000").rstrip("/")
TIMEOUT_SECONDS = 10

st.set_page_config(page_title="SmartLink", page_icon="🔗", layout="wide")


class ApiError(Exception):
    """The API could not be reached, or answered with an error."""

    pass


def api(method: str, path: str, **kwargs) -> requests.Response:
    """Call the API with the session's token. Raises ApiError; an expired token returns to the login."""
    headers = kwargs.pop("headers", {})
    if token := st.session_state.get("token"):
        headers["Authorization"] = f"Bearer {token}"
    try:
        response = requests.request(method, f"{API_URL}{path}", headers=headers, timeout=TIMEOUT_SECONDS, **kwargs)
    except requests.RequestException as exc:
        raise ApiError(f"Cannot reach the SmartLink API at {API_URL}") from exc
    if response.status_code == 401 and token:
        # Expired or invalid token: back to the login screen.
        st.session_state.pop("token", None)
        st.rerun()
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail")
        except ValueError:
            detail = response.text
        if isinstance(detail, list):  # FastAPI validation errors
            detail = "; ".join(f"{'.'.join(map(str, e['loc'][1:]))}: {e['msg']}" for e in detail)
        raise ApiError(f"{detail} (HTTP {response.status_code})")
    return response


def login_page() -> None:
    """Log in or create an account."""
    st.title("🔗 SmartLink")
    login_tab, register_tab = st.tabs(["Log in", "Create account"])
    for tab, path, label in [(login_tab, "/auth/login", "Log in"), (register_tab, "/auth/register", "Create account")]:
        with tab, st.form(path):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button(label):
                try:
                    token = api("POST", path, json={"username": username, "password": password}).json()
                except ApiError as exc:
                    st.error(str(exc))
                else:
                    st.session_state["token"] = token["access_token"]
                    st.session_state["username"] = username
                    st.rerun()


def create_link_section() -> None:
    """The form that creates a short link."""
    st.subheader("Create a short link")
    with st.form("shorten", clear_on_submit=True):
        original_url = st.text_input("Original URL", placeholder="https://example.com/a/very/long/path")
        col1, col2 = st.columns(2)
        alias = col1.text_input("Custom alias (optional)", placeholder="my-link")
        expires = col2.date_input("Expires on (optional)", value=None, min_value=date.today() + timedelta(days=1))
        if st.form_submit_button("Shorten"):
            payload = {"original_url": original_url.strip()}
            if alias.strip():
                payload["custom_alias"] = alias.strip()
            if expires:
                payload["expires_at"] = expires.isoformat()
            try:
                link = api("POST", "/shorten", json=payload).json()
            except ApiError as exc:
                st.error(str(exc))
            else:
                st.success(f"Created: {link['short_url']}")
                st.session_state["selected_code"] = link["code"]


def dashboard_section() -> None:
    """Totals and charts from /stats."""
    stats = api("GET", "/stats").json()
    st.subheader("Dashboard")
    col1, col2, col3 = st.columns(3)
    col1.metric("Links", stats["total_urls"])
    col2.metric("Total clicks", stats["total_clicks"])
    col3.metric("Expired links", stats["expired_urls"])

    left, right = st.columns(2)
    with left:
        st.caption("Clicks per day (last 30 days)")
        if stats["clicks_per_day"]:
            st.bar_chart(pd.DataFrame(stats["clicks_per_day"]).set_index("day"))
        else:
            st.info("No clicks yet.")
    with right:
        st.caption("Most used links")
        st.dataframe(pd.DataFrame(stats["top_links"]), hide_index=True, width="stretch")
        st.caption("Latest clicks")
        st.dataframe(pd.DataFrame(stats["recent_clicks"]), hide_index=True, width="stretch")


def links_section() -> None:
    """The user's links, with the details, QR code and clicks of the selected one."""
    links = api("GET", "/urls").json()
    st.subheader("My links")
    if not links:
        st.info("You have no links yet.")
        return

    table = pd.DataFrame(links)[["code", "short_url", "original_url", "status", "click_count", "expires_at"]]
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_config={
            "short_url": st.column_config.LinkColumn("short_url"),
            "original_url": st.column_config.LinkColumn("original_url"),
        },
    )

    codes = [link["code"] for link in links]
    default = codes.index(st.session_state["selected_code"]) if st.session_state.get("selected_code") in codes else 0
    code = st.selectbox("Link details", codes, index=default)
    detail = api("GET", f"/urls/{code}").json()
    qr_png = api("GET", f"/urls/{code}/qr").content

    left, right = st.columns([1, 2])
    with left:
        st.image(qr_png, caption=detail["short_url"], width=220)
        st.download_button("Download QR", qr_png, file_name=f"smartlink-{code}.png", mime="image/png")
    with right:
        st.markdown(f"**{detail['short_url']}** → {detail['original_url']}")
        st.markdown(f"Status: `{detail['status']}` · Clicks: **{detail['click_count']}**")
        if detail["clicks_per_day"]:
            st.bar_chart(pd.DataFrame(detail["clicks_per_day"]).set_index("day"))
        if detail["recent_clicks"]:
            st.dataframe(pd.DataFrame(detail["recent_clicks"]), hide_index=True, width="stretch")


def main_page() -> None:
    """The signed-in page: sidebar, new link, dashboard and links."""
    with st.sidebar:
        st.write(f"Signed in as **{st.session_state.get('username', '')}**")
        if st.button("Log out"):
            st.session_state.clear()
            st.rerun()
    st.title("🔗 SmartLink")
    try:
        create_link_section()
        dashboard_section()
        links_section()
    except ApiError as exc:
        st.error(str(exc))


if "token" in st.session_state:
    main_page()
else:
    login_page()
