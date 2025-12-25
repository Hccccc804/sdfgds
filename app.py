import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# 页面配置
st.set_page_config(
    page_title="数字化转型指数查询",
    page_icon="📊",
    layout="wide"
)

# 标题
st.title("📊 企业数字化转型指数查询系统")

# 数据加载
@st.cache_data
def load_data():
    """加载数据"""
    data_files = [
        "data.xlsx",
        "两版合并后的年报数据_完整版.xlsx",
        "data/两版合并后的年报数据_完整版.xlsx"
    ]
    
    for path in data_files:
        if os.path.exists(path):
            return pd.read_excel(path)
    
    st.error("❌ 未找到数据文件")
    return None

df = load_data()

if df is not None:
    # 数据预处理
    df['股票代码'] = df['股票代码'].astype(str)
    df['企业名称'] = df['企业名称'].fillna('未知企业')
    
    available_stocks = sorted(df['股票代码'].unique())
    available_years = sorted(df['年份'].unique())
    stock_name_map = df.groupby('股票代码')['企业名称'].first().to_dict()
    
    # 侧边栏
    st.sidebar.header("🔍 查询条件")
    
    default_stock = available_stocks[0] if available_stocks else "600003"
    stock_search = st.sidebar.text_input("股票代码", value=default_stock, placeholder="例如: 600003")
    selected_year = st.sidebar.slider("年份", int(available_years[0]), int(available_years[-1]), 1999, 1)
    
    if stock_search:
        st.sidebar.info(f"📌 **{stock_search}** ({stock_name_map.get(stock_search, '未知企业')})")
    
    company_all_data = df[df['股票代码'] == stock_search].sort_values('年份')
    filtered_data = df[(df['股票代码'] == stock_search) & (df['年份'] == selected_year)]
    
    # 主内容
    st.header(f"📈 {stock_name_map.get(stock_search, '未知企业')} ({stock_search})")
    
    # 数据概览
    st.subheader("📊 数据概览")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("平均指数", f"{df['数字化转型指数'].mean():.2f}")
    c2.metric("指数最大值", f"{df['数字化转型指数'].max():.2f}")
    c3.metric("企业数量", f"{df['股票代码'].nunique()}")
    c4.metric("年份范围", f"{df['年份'].min()}-{df['年份'].max()}")
    
    # 当前企业数据
    if not filtered_data.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("企业名称", filtered_data['企业名称'].iloc[0][:10])
        c2.metric("当前年份", f"{selected_year}")
        c3.metric("当前指数", f"{filtered_data['数字化转型指数'].iloc[0]:.2f}")
        
        current_year_data = df[df['年份'] == selected_year]
        current_rank = current_year_data[current_year_data['数字化转型指数'] >= filtered_data['数字化转型指数'].iloc[0]].shape[0]
        c4.metric("当年排名", f"{current_rank}/{len(current_year_data)}")
    
    st.markdown("---")
    
    # 趋势图
    st.subheader("📈 数字化转型指数趋势")
    
    if len(company_all_data) > 1:
        fig_line = px.line(company_all_data, x='年份', y='数字化转型指数', 
                          markers=True, line_shape='spline')
        fig_line.update_traces(line=dict(color='#1f77b4', width=4), marker=dict(size=10))
        fig_line.update_layout(height=400, hovermode='x unified')
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("数据不足")
    
    # 指数分布
    st.subheader("📉 指数分布")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### 指数区间分布")
        bins = [0, 20, 40, 60, 80, 100]
        labels = ['0-20', '20-40', '40-60', '60-80', '80-100']
        df['指数区间'] = pd.cut(df['数字化转型指数'], bins=bins, labels=labels)
        distribution = df['指数区间'].value_counts().sort_index()
        fig_pie = px.pie(values=distribution.values, names=distribution.index, 
                        title="数字化转型指数区间分布", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.write("#### 各年份平均指数")
        yearly_avg = df.groupby('年份')['数字化转型指数'].mean().reset_index()
        fig_bar = px.bar(yearly_avg, x='年份', y='数字化转型指数',
                        title="各年份平均数字化转型指数")
        fig_bar.update_traces(marker_color='#2ca02c')
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # 多维度分析
    st.subheader("📊 多维度数据分析")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["热力图", "条形图", "双轴图", "面积图", "变化率"])
    
    with tab1:
        st.write("#### 年度-企业数字化转型热力图")
        pivot_data = df.pivot_table(values='数字化转型指数', index='股票代码', 
                                   columns='年份', aggfunc='mean')
        if not pivot_data.empty:
            top_stocks = df.groupby('股票代码')['数字化转型指数'].mean().nlargest(30).index
            pivot_subset = pivot_data.loc[top_stocks]
            fig_heatmap = px.imshow(pivot_subset, aspect='auto', color_continuous_scale='RdYlGn')
            st.plotly_chart(fig_heatmap, use_container_width=True)
    
    with tab2:
        st.write("#### 年度指数排名TOP20企业")
        top20 = df.groupby('股票代码')['数字化转型指数'].mean().nlargest(20).reset_index()
        top20['企业名称'] = top20['股票代码'].map(stock_name_map)
        fig_ranking = px.bar(top20, x='数字化转型指数', y='股票代码', 
                            orientation='h', title="TOP20企业平均数字化转型指数")
        fig_ranking.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_ranking, use_container_width=True)
    
    with tab3:
        st.write("#### 平均指数与活跃企业数量双轴图")
        yearly_stats = df.groupby('年份').agg({
            '数字化转型指数': 'mean',
            '股票代码': 'nunique'
        }).reset_index()
        yearly_stats.columns = ['年份', '平均指数', '企业数量']
        
        fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
        fig_dual.add_trace(go.Scatter(x=yearly_stats['年份'], y=yearly_stats['平均指数'],
                                      name="平均指数", line=dict(color='#1f77b4', width=3)),
                          secondary_y=False)
        fig_dual.add_trace(go.Bar(x=yearly_stats['年份'], y=yearly_stats['企业数量'],
                                  name="企业数量", marker_color='#ff7f0e'),
                          secondary_y=True)
        fig_dual.update_yaxes(title_text="平均指数", secondary_y=False)
        fig_dual.update_yaxes(title_text="企业数量", secondary_y=True)
        st.plotly_chart(fig_dual, use_container_width=True)
    
    with tab4:
        st.write("#### 数字化转型指数趋势面积图")
        yearly_mean = df.groupby('年份')['数字化转型指数'].mean().reset_index()
        fig_area = go.Figure()
        fig_area.add_trace(go.Scatter(
            x=yearly_mean['年份'], y=yearly_mean['数字化转型指数'],
            fill='tozeroy', mode='lines', name='平均指数',
            line=dict(color='#2ca02c', width=3)
        ))
        fig_area.update_layout(height=400, hovermode='x unified')
        st.plotly_chart(fig_area, use_container_width=True)
    
    with tab5:
        st.write("#### 年度指数变化趋势")
        yearly_mean = df.groupby('年份')['数字化转型指数'].mean().reset_index()
        yearly_mean['变化率'] = yearly_mean['数字化转型指数'].pct_change() * 100
        
        fig_change = go.Figure()
        fig_change.add_trace(go.Scatter(
            x=yearly_mean['年份'], y=yearly_mean['变化率'],
            mode='lines+markers', name='年度变化率',
            line=dict(color='#2ca02c', width=3),
            fill='tozeroy',
            fillcolor='rgba(44, 160, 44, 0.2)'
        ))
        fig_change.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_change.update_layout(height=400, hovermode='x unified')
        st.plotly_chart(fig_change, use_container_width=True)
    
    # 页脚
    st.markdown("---")
    st.caption("📊 数据来源: 企业年报数据 | 技术支持: Streamlit + Plotly")
