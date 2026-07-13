import sqlite3
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Covid 19 Pandemic Dashboard", layout="wide")

@st.cache_data
def prepare_data():
    connection = sqlite3.connect("data/covid_19.db")
    daily_report = pd.read_sql("""SELECT * FROM daily_report;""", con=connection)
    time_series = pd.read_sql("""SELECT * FROM time_series;""", con=connection)
    connection.close()
    time_series["reported_on"] = pd.to_datetime(time_series["reported_on"])
    return daily_report, time_series

daily_report, time_series = prepare_data()

total_cases = daily_report["confirmed"].sum()
total_deaths = daily_report["deaths"].sum()
latest_time_series = time_series[time_series["reported_on"] == "2023-03-09"]
total_vaccinated = latest_time_series["doses_administered"].sum()
sum_confirmed_by_country = daily_report.groupby("country")["confirmed"].sum().sort_values(ascending=False)
top_confirmed = sum_confirmed_by_country.index[:30].to_list()

def filter_global_map(country_names):
    filtered_daily_report = daily_report[daily_report["country"].isin(country_names)]
    if filtered_daily_report.empty:
        return go.Figure()
    countries = filtered_daily_report["country"].values
    provinces = filtered_daily_report["province"].values
    counties = filtered_daily_report["county"].values
    confirmed = filtered_daily_report["confirmed"].values
    deaths = filtered_daily_report["deaths"].values
    information_when_hovered = []
    for country, province, county, c, d in zip(countries, provinces, counties, confirmed, deaths):
        if county is not None:
            marker_information = [(country, province, county), c, d]
        elif province is not None:
            marker_information = [(country, province), c, d]
        else:
            marker_information = [country, c, d]
        information_when_hovered.append(marker_information)
    fig = go.Figure(
        go.Scattermapbox(lat=filtered_daily_report["latitude"],
                        lon=filtered_daily_report["longitude"],
                        customdata=information_when_hovered,
                        hoverinfo="text",
                        hovertemplate="Location: %{customdata[0]}<br>Confirmed: %{customdata[1]}<br>Deaths: %{customdata[2]}",
                        mode="markers",
                        marker={"size": filtered_daily_report["confirmed"],
                                "color": filtered_daily_report["confirmed"],
                                "sizemin": 2,
                                "sizeref": filtered_daily_report["confirmed"].max()/2500,
                                "sizemode": "area"}
        )
    )
    fig.update_layout(mapbox_style="open-street-map",
                    mapbox=dict(zoom=2,
                                center=go.layout.mapbox.Center(
                                lat=0,
                                lon=0),
                                ),
                                margin={"r":0, "t":0, "l":0, "b":0}
                    )
    return fig

#建立streamlit介面
tab1, tab2 = st.tabs(["Global Map", "Country Time Series"])

#建立散佈圖
with tab1:
    st.title("📊 Covid 19 Global Map")
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Total cases", value=f"{total_cases:,}")
    col2.metric(label="Total deaths", value=f"{total_deaths:,}")
    col3.metric(label="Total doses administered", value=f"{total_vaccinated:,}")
    st.markdown("---")
    selected_countries = st.multiselect(
        label="Select countries:",
        options=daily_report["country"].unique().tolist(),
        default=top_confirmed
    )
    map_fig = filter_global_map(selected_countries)
    st.plotly_chart(map_fig, width="stretch")

#建立折線圖
with tab2:
    st.title("📈 Covid 19 Country Time Series")
    country_options = time_series["country"].unique().tolist()
    default_index = country_options.index("Taiwan*") if "Taiwan*" in country_options else 0
    selected_country = st.selectbox(
        label="Select a country:",
        options=country_options,
        index=default_index
        
    )
    filtered_df = time_series[time_series["country"] == selected_country].sort_values("reported_on")

    st.subheader("Confirmed Cases")
    st.line_chart(data=filtered_df, x="reported_on", y="confirmed")
    st.subheader("Deaths")
    st.line_chart(data=filtered_df, x="reported_on", y="deaths")
    st.subheader("Doses Administered")
    st.line_chart(data=filtered_df, x="reported_on", y="doses_administered")