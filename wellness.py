import os
from datetime import datetime, timezone, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_FILE = "wellness_belegung_daten.csv"
MAX_PERSONEN = 10
TZ_CH = timezone(timedelta(hours=1))  # CET; CEST wird ähnlich gut dargestellt

DAY_MAPPING = {
    "Monday": "Montag", "Tuesday": "Dienstag", "Wednesday": "Mittwoch",
    "Thursday": "Donnerstag", "Friday": "Freitag",
    "Saturday": "Samstag", "Sunday": "Sonntag",
}
WEEKDAYS_ORDER = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


@st.cache_data(ttl=300)
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["Datum_Uhrzeit"] = pd.to_datetime(df["Datum"] + " " + df["Uhrzeit"])
    df["Wochentag"] = df["Datum_Uhrzeit"].dt.day_name().map(DAY_MAPPING)
    df["Stunde"] = df["Datum_Uhrzeit"].dt.hour
    df["Uhrzeit_HM"] = df["Datum_Uhrzeit"].dt.strftime("%H:%M")
    return df


def render_gauge(latest_free: int, latest_when: str) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=latest_free,
        title={"text": f"Aktuell freie Plätze (Stand: {latest_when})", "font": {"size": 22}},
        gauge={
            "axis": {"range": [0, MAX_PERSONEN], "tickwidth": 1},
            "bar": {"color": "darkblue"},
            "steps": [
                {"range": [0, 2], "color": "red"},
                {"range": [2, 5], "color": "orange"},
                {"range": [5, 10], "color": "lightgreen"},
            ],
        },
    ))
    fig.update_layout(height=320, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def render_heatmap(df: pd.DataFrame) -> go.Figure:
    pivot = (
        df.pivot_table(values="Freie Plätze", index="Wochentag", columns="Stunde", aggfunc="mean")
          .reindex(WEEKDAYS_ORDER)
    )
    pivot = pivot.dropna(axis=1, how="all")

    fig = px.imshow(
        pivot,
        color_continuous_scale="RdYlGn",
        zmin=0, zmax=MAX_PERSONEN,
        aspect="auto",
        labels=dict(x="Stunde", y="Wochentag", color="Ø freie Plätze"),
        text_auto=".1f",
        title="Heatmap – Ø freie Plätze (grün = leer, rot = voll)",
    )
    fig.update_xaxes(
        tickmode="array",
        tickvals=list(pivot.columns),
        ticktext=[f"{int(h):02d}:00" for h in pivot.columns],
        side="top",
    )
    fig.update_traces(
        textfont=dict(size=12, color="black"),
        hovertemplate="%{y} · %{x}:00<br>Ø %{z:.1f} freie Plätze<extra></extra>",
    )
    fig.update_layout(height=420, margin=dict(l=20, r=20, t=70, b=20), coloraxis_colorbar=dict(title="frei"))
    return fig


def main():
    st.set_page_config(page_title="Wellness Wädenswil", page_icon="🏊‍♂️", layout="wide")
    st.title("Wellness Wädenswil – Auslastung")

    tab_status, tab_charts = st.tabs(["ℹ️ Status", "📈 Visualisierung"])

    with tab_status:
        st.subheader("Setup")
        st.markdown(
            "- **Scraping läuft automatisch** via GitHub Actions (alle 15 Min, 06–20 UTC).\n"
            "- **Dashboard** liest direkt aus `wellness_belegung_daten.csv` im Repo.\n"
            "- Cache 5 Min – auf `R` drücken erzwingt Reload."
        )
        if os.path.exists(DATA_FILE):
            df_raw = pd.read_csv(DATA_FILE)
            if not df_raw.empty:
                last_row = df_raw.iloc[-1]
                st.metric("Letzter Datenpunkt", f"{last_row['Datum']} {last_row['Uhrzeit']}")
                st.metric("Anzahl Messpunkte gesamt", f"{len(df_raw):,}".replace(",", "'"))
            else:
                st.info("CSV vorhanden, aber leer.")
        else:
            st.warning("Noch keine Daten – Scraper hatte vermutlich noch keinen Lauf.")

    with tab_charts:
        if not os.path.exists(DATA_FILE):
            st.info("Es wurden noch keine Daten gesammelt.")
            return

        try:
            df = load_data(DATA_FILE)
        except Exception as e:
            st.error(f"Fehler beim Laden der Daten: {e}")
            return

        if df.empty:
            st.info("Die CSV-Datei ist noch leer.")
            return

        latest_free = int(df["Freie Plätze"].iloc[-1])
        latest_when = f"{df['Datum'].iloc[-1]} {df['Uhrzeit'].iloc[-1]}"
        st.plotly_chart(render_gauge(latest_free, latest_when), use_container_width=True)
        st.divider()

        df_polar = df.groupby(["Wochentag", "Stunde"])["Freie Plätze"].mean().reset_index()
        fig_polar = px.line_polar(
            df_polar, r="Freie Plätze", theta="Stunde", color="Wochentag",
            line_close=True, title="Die Wellness-Uhr (Wann ist Platz?)",
            category_orders={"Wochentag": WEEKDAYS_ORDER},
        )
        fig_polar.update_traces(fill="toself", opacity=0.4, line_shape="spline", hoverinfo="name+r+theta")
        fig_polar.update_layout(polar=dict(
            bgcolor="rgba(240, 248, 255, 0.4)",
            radialaxis=dict(range=[0, MAX_PERSONEN], visible=True, showticklabels=False, gridcolor="rgba(0,0,0,0.1)"),
            angularaxis=dict(
                tickmode="array",
                tickvals=list(range(24)),
                ticktext=[f"{i}:00" for i in range(24)],
                rotation=90, direction="clockwise", gridcolor="rgba(0,0,0,0.1)",
            ),
        ))

        fig_violin = px.violin(
            df, x="Freie Plätze", y="Wochentag", color="Wochentag",
            box=True, points="all", orientation="h",
            title="Verteilung (Wie verlässlich kriege ich einen Platz?)",
            category_orders={"Wochentag": WEEKDAYS_ORDER},
        )
        fig_violin.update_xaxes(range=[-1, MAX_PERSONEN + 1])

        col_a, col_b = st.columns(2)
        col_a.plotly_chart(fig_polar, use_container_width=True)
        col_b.plotly_chart(fig_violin, use_container_width=True)
        st.divider()

        df_avg = df.groupby(["Wochentag", "Uhrzeit_HM"])["Freie Plätze"].mean().reset_index()
        df_avg["Uhrzeit_Plot"] = pd.to_datetime("1900-01-01 " + df_avg["Uhrzeit_HM"])
        fig_line = px.line(
            df_avg, x="Uhrzeit_Plot", y="Freie Plätze", color="Wochentag",
            title="Durchschnittlicher Tagesverlauf", markers=True,
            category_orders={"Wochentag": WEEKDAYS_ORDER},
        )
        fig_line.update_yaxes(range=[0, MAX_PERSONEN])
        fig_line.update_xaxes(tickformat="%H:%M", title="Uhrzeit")

        st.plotly_chart(fig_line, use_container_width=True)
        st.plotly_chart(render_heatmap(df), use_container_width=True)

        st.subheader("Rohdaten (letzte 20)")
        st.dataframe(df.tail(20), use_container_width=True)


if __name__ == "__main__":
    main()
