import streamlit as st
import backtrader as bt
import backtrader.analyzers as btanalyzers
import pandas as pd
import pandas_datareader as pdr
import plotly.graph_objects as go
from datetime import datetime, timedelta
from data_loader import load_stock_data

import matplotlib
matplotlib.use('Agg')
from dotenv import load_dotenv
load_dotenv("/teamspace/studios/this_studio/sentiment_analysis/.env")

import dspy
from dspy.primitives.assertions import assert_transform_module, backtrack_handler
from data_loader import load_stock_data
from base_strategy_improved import BaseStrategy
from dspy.predict import Retry
import backtrader as bt
import dsp
import functools
import random
random.seed(42)


# Tracing LLM output
# import phoenix as px
# px.launch_app()

# from openinference.instrumentation.dspy import DSPyInstrumentor
# from opentelemetry import trace as trace_api
# from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
# from opentelemetry.sdk import trace as trace_sdk
# from opentelemetry.sdk.resources import Resource
# from opentelemetry.sdk.trace.export import SimpleSpanProcessor


# endpoint = "http://127.0.0.1:6007/v1/traces"
# resource = Resource(attributes={})
# tracer_provider = trace_sdk.TracerProvider(resource=resource)
# span_otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
# tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter=span_otlp_exporter))
# trace_api.set_tracer_provider(tracer_provider=tracer_provider)
# DSPyInstrumentor().instrument()



# Define a simple strategy
class SimpleMovingAverageStrategy(bt.Strategy):
    params = (
        ('fast_ma', 10),
        ('slow_ma', 30),
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.fast_ma)
        self.slow_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.slow_ma)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        elif self.crossover < 0:
            self.close()


def get_answer(user_question, data):
    # Define and setting LLM for DSPy
    lm = dspy.Anyscale(
        model="meta-llama/Meta-Llama-3-70B-Instruct",
        max_tokens=2048, 
        use_chat_api=True,
        temperature=0.0
    )

    dspy.settings.configure(lm=lm, trace=[])


    # Generate code with assert
    generate_with_assert = assert_transform_module(GenerateCodeWithAssert(list_ohcl_data=data).map_named_predictors(Retry), functools.partial(backtrack_handler, max_backtracks=8))
    
    return generate_with_assert(user_question)



def run_backtrader_strategy(ticker, period):
    

    # Add data feed
    data = [bt.feeds.PandasData(
                dataname=load_stock_data(ticker=ticker, period=period), datetime="Date", 
                timeframe=bt.TimeFrame.Minutes)]
    
    # Create a Cerebro instance
    cerebro = bt.Cerebro()
    
    for d in data:
        cerebro.adddata(d)

    # Add strategy
    cerebro.addstrategy(SimpleMovingAverageStrategy)

    # Set initial cash
    cerebro.broker.setcash(100000.0)

    # Add analyzers
    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(btanalyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(btanalyzers.Returns, _name='returns')

    # Run the strategy
    results = cerebro.run()

    # Get the final portfolio value
    final_value = cerebro.broker.getvalue()

    # Extract analysis results
    sharpe_ratio = results[0].analyzers.sharpe.get_analysis()['sharperatio']
    max_drawdown = results[0].analyzers.drawdown.get_analysis()['max']['drawdown']
    total_return = results[0].analyzers.returns.get_analysis()['rtot']

    return final_value, sharpe_ratio, max_drawdown, total_return, cerebro





def main():
    st.set_page_config(layout="wide")
    st.title("LLM Finance Q&A")


    # Sidebar
    st.sidebar.title("Market Symbols")
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "FB", "TSLA"]
    selected_symbol = st.sidebar.selectbox("Select a symbol", symbols) 
    
    # start_date = st.sidebar.date_input("Start date", datetime.now() - timedelta(days=365))
    # end_date = st.sidebar.date_input("End date", datetime.now())
    
    
    period = st.sidebar.text_input("Period: (y (year), mo (month), d(day))", "1y")
    
    # Input for user question
    user_question = st.text_input("Enter your finance-related question:")
    
    if user_question:
        final_value, sharpe_ratio, max_drawdown, total_return, cerebro = run_backtrader_strategy(selected_symbol, period)

        # Display results
        col1, col2 = st.columns(2)
        
        # Get the answer
        # response = get_answer(user_question)

        with col1:
            st.subheader("Backtest Results")
            st.write("Status: Successfully executed strategy!")
            st.write(f"Final Portfolio Value: ${final_value:.2f}")
            st.write(f"Sharpe Ratio: {sharpe_ratio:.2f}")
            st.write(f"Total Return: {total_return:.2f}%")

        with col2:
            st.subheader("Equity Curve")
            # st.plotly_chart(cerebro.plot(), use_container_width=True)
            figure = cerebro.plot()[0][0]
            st.pyplot(figure)

if __name__ == "__main__":
    main()