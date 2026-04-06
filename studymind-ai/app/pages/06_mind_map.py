# app/pages/06_mind_map.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
import streamlit.components.v1 as components
from utils.session_state import init_session_state
from features.mind_map import generate_mind_map, render_mind_map_html
init_session_state()

st.markdown('<div class="sm-page-title">Mind Map</div>', unsafe_allow_html=True)
st.markdown('<div class="sm-page-sub">Interactive knowledge graph — drag, zoom, and explore how concepts connect</div>', unsafe_allow_html=True)

if not st.session_state.docs_indexed:
    st.markdown('<div class="sm-empty"><div class="sm-empty-ico">🗺️</div><div class="sm-empty-title">Index documents first</div></div>', unsafe_allow_html=True)
    st.stop()

st.markdown('<div class="sm-highlight"><div class="sm-highlight-title">Build Knowledge Graph</div>', unsafe_allow_html=True)
c1,c2,c3 = st.columns([3,1,1])
topic     = c1.text_input("Topic focus", placeholder="Leave blank for all concepts")
max_nodes = c2.slider("Max nodes", 8, 25, 15)
if c3.button("🗺️  Build Map", use_container_width=True):
    with st.spinner("Building knowledge graph from your notes…"):
        data = generate_mind_map(st.session_state.vector_store, topic=topic, max_nodes=max_nodes)
    st.session_state.mind_map_data = data; st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.mind_map_data:
    data    = st.session_state.mind_map_data
    metrics = data.get("metrics",{})

    if metrics:
        st.markdown(f"""
        <div class="sm-stats">
          <div class="sm-stat"><span class="sm-stat-n">{metrics.get('num_nodes',0)}</span><span class="sm-stat-l">Concepts</span></div>
          <div class="sm-stat"><span class="sm-stat-n">{metrics.get('num_edges',0)}</span><span class="sm-stat-l">Links</span></div>
          <div class="sm-stat"><span class="sm-stat-n" style="font-size:1.2rem">{metrics.get('density',0)}</span><span class="sm-stat-l">Density</span></div>
          <div class="sm-stat"><span class="sm-stat-n" style="font-size:0.95rem;overflow:hidden;white-space:nowrap;text-overflow:ellipsis">{metrics.get('central_node','—')}</span><span class="sm-stat-l">Central</span></div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sm-div"></div>', unsafe_allow_html=True)

    html = render_mind_map_html(data, height="540px")
    if "<svg" in html or "<div" in html:
        html = html.replace("<body>", '<body style="background:#07091a;margin:0;padding:0;">')
        components.html(html, height=560, scrolling=False)
    else:
        st.error("Install pyvis: `pip install pyvis`")

    st.markdown("""
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:0.9rem;align-items:center;">
      <span class="sm-badge badge-v">● Core Concepts</span>
      <span class="sm-badge badge-em">● Sub-Concepts</span>
      <span class="sm-badge badge-a">● Examples</span>
      <span style="font-size:11px;color:var(--t3);">Drag nodes · Scroll to zoom · Click to explore</span>
    </div>""", unsafe_allow_html=True)

    with st.expander("🔧  Raw graph data"):
        cn,ce = st.columns(2)
        cn.markdown("**Nodes**")
        for n in data.get("nodes",[]): cn.markdown(f"- `{n['id']}`: {n.get('label','')}")
        ce.markdown("**Edges**")
        for e in data.get("edges",[]): ce.markdown(f"- `{e['from']}` → `{e['to']}` _{e.get('label','')}_")
else:
    st.markdown("""
    <div class="sm-empty">
      <div class="sm-empty-ico">🗺️</div>
      <div class="sm-empty-title">No mind map generated yet</div>
      <div class="sm-empty-sub">Configure options above and click Build Map to<br>visualize your notes as an interactive knowledge graph.</div>
      <div style="margin-top:1.3rem;">
        <span class="sm-badge badge-v">● Core</span>&nbsp;
        <span class="sm-badge badge-em">● Detail</span>&nbsp;
        <span class="sm-badge badge-a">● Example</span>
      </div>
    </div>""", unsafe_allow_html=True)