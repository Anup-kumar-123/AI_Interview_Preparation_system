import plotly.graph_objects as go
import streamlit as st

from src.utils.ui_styles import empty_state, stretch

VIOLET, AMBER, MINT = "#7C5CFF", "#FFB547", "#4ADE9C"
RADAR_LABELS = {
    "situation": "Situation",
    "action": "Action",
    "result": "Result",
    "clarity": "Clarity",
    "technical_depth": "Technical depth",
}


def _style(fig, height=340):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Figtree, sans-serif", color="#ECEBFF"),
        margin=dict(l=10, r=10, t=30, b=10),
        height=height,
        showlegend=False,
    )
    return fig


def render_analytics_dashboard(history: list):
    """Renders performance metrics and charts from the scored answers."""
    if not history:
        st.markdown(
            empty_state("📈", "No answers scored yet",
                        "Complete a mock interview question and your trends will show up here."),
            unsafe_allow_html=True,
        )
        return

    scores = [int(h["eval"].get("score", 0)) for h in history]
    labels = [f"Q{i + 1}" for i in range(len(scores))]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Answers scored", len(scores))
    m2.metric("Average", f"{sum(scores) / len(scores):.0f}")
    m3.metric("Best", max(scores))
    m4.metric("Latest", scores[-1], delta=(scores[-1] - scores[-2]) if len(scores) > 1 else None)

    st.write("")
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.subheader("Score trend")
        fig = go.Figure(go.Scatter(
            x=labels, y=scores, mode="lines+markers",
            line=dict(color=VIOLET, width=3, shape="spline"),
            marker=dict(size=10, color=AMBER, line=dict(color="#0A0B14", width=2)),
            fill="tozeroy", fillcolor="rgba(124,92,255,.12)",
        ))
        fig.update_yaxes(range=[0, 100], gridcolor="rgba(154,156,196,.15)")
        fig.update_xaxes(gridcolor="rgba(0,0,0,0)")
        st.plotly_chart(_style(fig), **stretch(st.plotly_chart))

    with col2:
        st.subheader("Strengths by dimension")
        dims = [h["eval"].get("dimension_scores") for h in history if isinstance(h["eval"].get("dimension_scores"), dict)]
        if dims:
            keys = list(RADAR_LABELS)
            avgs = [sum(d.get(k, 0) for d in dims) / len(dims) for k in keys]
            theta = [RADAR_LABELS[k] for k in keys]
            fig = go.Figure(go.Scatterpolar(
                r=avgs + avgs[:1], theta=theta + theta[:1], fill="toself",
                line=dict(color=MINT, width=2), fillcolor="rgba(74,222,156,.18)",
            ))
            fig.update_layout(polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(range=[0, 100], gridcolor="rgba(154,156,196,.2)"),
                angularaxis=dict(gridcolor="rgba(154,156,196,.2)"),
            ))
            st.plotly_chart(_style(fig), **stretch(st.plotly_chart))
        else:
            st.info("Dimension scores appear after your next evaluated answer.")

    st.subheader("Answer review")
    for i in reversed(range(len(history))):
        item, ev = history[i], history[i]["eval"]
        title = item["question"] if len(item["question"]) <= 80 else item["question"][:77] + "..."
        with st.expander(f"Q{i + 1}: {scores[i]}/100 - {title}"):
            st.markdown("**Question**")
            st.write(item["question"])
            st.markdown("**Your answer**")
            st.write(item["answer"])
            if ev.get("strengths"):
                st.markdown("**What worked:** " + ", ".join(ev["strengths"]))
            st.markdown(f"**Next step:** {ev.get('improvement_tip', '')}")
            if ev.get("source") == "offline":
                st.caption("Estimated offline score (Gemini was unavailable).")
