# Python package
import json
import functools
import os
import sys
import matplotlib
matplotlib.use('Agg')
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), "src/my_dspy"))
sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__),".env"))

# Backtrader package
import backtrader as bt
from backtrader import Indicator
import backtrader.analyzers as btanalyzers
from utils.backtrader_cerebro import CelebroCreator
from utils.data_loader import load_stock_data

import phoenix as px
import requests
from openinference.instrumentation.dspy import DSPyInstrumentor
from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import SimpleSpanProcessor


# DSPy package
import dspy
import dsp
from dspy.predict import Retry
from dspy.primitives.assertions import (
    assert_transform_module,
    backtrack_handler,
)
from src.my_dspy.dspy_module import GenerateCodeWithAssert


# My package
## Utils package
from utils.file_text_handler import get_code_from_text, load_file
from utils.prompt_template.base_strategy_improved import BaseStrategy

# Streamlit package
import streamlit as st


#  Tracing LLM inference
def setup_tracing_llm():
    px.launch_app()
    endpoint = "http://127.0.0.1:6006/v1/traces"
    resource = Resource(attributes={})
    tracer_provider = trace_sdk.TracerProvider(resource=resource)
    span_otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
    tracer_provider.add_span_processor(
        SimpleSpanProcessor(span_exporter=span_otlp_exporter)
    )
    trace_api.set_tracer_provider(tracer_provider=tracer_provider)
    DSPyInstrumentor().instrument()


# Get the answer from the DSPy program with assertion
def get_answer(user_question, data):
    generate_with_assert = assert_transform_module(
        GenerateCodeWithAssert(list_ohcl_data=data).map_named_predictors(Retry),
        functools.partial(backtrack_handler, max_backtracks=8),
    )

    few_shot_path = os.path.join(os.path.dirname(__file__), "src/module/new_code_generation_fewshot_v3.json")
    generate_with_assert.load(few_shot_path)

    return generate_with_assert(user_question)




def main():
    # Setup tracing for LLM inference
    setup_tracing_llm()
    
    # Streamlit configuration layout
    st.set_page_config(layout="wide")
    st.title("Text2Alpha")


    # Sidebar
    st.sidebar.title("Market Configuration")
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "FB", "TSLA"]
    selected_symbol = st.sidebar.selectbox("Select a symbol", symbols) 
    
    # start_date = st.sidebar.date_input("Start date", datetime.now() - timedelta(days=365))
    # end_date = st.sidebar.date_input("End date", datetime.now())
    
    
    period = st.sidebar.text_input("Period: (y (year), mo (month), d(day))", "1y")
    
    # Input for user question
    user_question = st.text_input("Enter your finance-related question:")
    
    # Load the stock data
    data = [
        bt.feeds.PandasData(
            dataname=load_stock_data(ticker=selected_symbol, period=period),
            datetime="Date",
            timeframe=bt.TimeFrame.Minutes,
        )
    ]

    # Setup tracing for LLM inference


    # Configure LLM Anyscale endpoint
    lm = dspy.Anyscale(
        model="meta-llama/Meta-Llama-3-70B-Instruct",
        max_tokens=2048,
        use_chat_api=True,
        temperature=0.0,
    )
    dspy.settings.configure(lm=lm, trace=[])
    
    # Check if user question is provided
    if user_question:
        
        response = get_answer(user_question, data)
        complete_status, still_errors_status = response.Complete, response.Still_Error[:-1]

        if complete_status:
            exec(get_code_from_text(response.answer), globals())
            strategy = CelebroCreator(BackTestStrategy,data)
            

        # Display results
        col1, col2 = st.columns(2)
        


        with col1:
            st.subheader("Backtest Results")
            
            if still_errors_status=='True':
                st.write("Status: Unsuccessful strategy generation!!!")
                st.write("Message: Unfortunately, we were unable to generate a suitable trading strategy based on your query. Please try another query or provide more detailed information about the indicators you would like to use. This can help our system better understand and create a strategy that meets your needs.")
            
            elif not complete_status:
                st.write("Status: Incomplete Strategy Generation!!!")
                st.write("Message: The generation of your trading strategy was incomplete due to insufficient information about the indicators or strategy. Please provide more detailed descriptions and formulas for the indicators or strategy you are using. This additional information will help our system generate a more accurate and complete strategy")
                
            else:
                results = strategy.return_analysis() 
                st.write("Status: Successfully executed strategy!")
                st.write(f"Starting Cash: ${results['StartingCash']}")
                st.write(f"Final Portfolio Value: ${results['FinalPortfolioValue']:.2f}")
                st.write(f"Sharpe Ratio: {results['SharpeRatio']:.2f}")
                st.write(f"Total Return: {results['TotalReturn']:.2f}%")

        with col2:
            st.subheader(f"{selected_symbol} Trend")
            # st.plotly_chart(cerebro.plot(), use_container_width=True)
            if complete_status:
                figure = strategy.show()[0][0]
                st.pyplot(figure)
            else:
                figure = CelebroCreator(strategy=None, list_of_data=data).show()[0][0]
                st.pyplot(figure)



if __name__ == "__main__":
    main()