# %%
import phoenix as px

px.launch_app()

# %%
from openinference.instrumentation.dspy import DSPyInstrumentor
from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import SimpleSpanProcessor


endpoint = "http://127.0.0.1:6006/v1/traces"
resource = Resource(attributes={})
tracer_provider = trace_sdk.TracerProvider(resource=resource)
span_otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter=span_otlp_exporter))
trace_api.set_tracer_provider(tracer_provider=tracer_provider)
DSPyInstrumentor().instrument()

# %%
%cd /teamspace/studios/this_studio/final_project/Trading_Project

# %%

from utils.file_text_handler import load_file, get_code_from_text
from utils.my_error_messages import extract_error_message
import dspy
import dsp
import cohere
import json
import functools
from dotenv import load_dotenv
import os
import requests
from datetime import datetime
import backtrader as bt
from backtrader import Indicator
# load_dotenv('.env')

text = load_file("cleaned_text.txt")

texts = text.split("\n\n\n\n")

# %%
base_strategy_PATH ="base_strategy_improved.py"
backtrader_examples_PATH = "backtrader_examples.py"
custom_examples_PATH = "custom_examples.py"
base_strats = load_file(base_strategy_PATH)
backtrader_examples = load_file(backtrader_examples_PATH)
custom_examples =load_file(custom_examples_PATH)
list_indicators = load_file("indicators.txt")



instruction = f"""
You are a python developer that intent to make a workable trading strategy. Your tasks are :
- Create a `CustomIndicator` class that inherit from the `Indicator` class
- Create a `BackTestStrategy` class that inherit from the `BaseStrategy` class and modify the `execute` function to follow human requirements.
Note : You MUST STRICTLY follow the instructions above.
Here is the `BaseStrategy` class : 
```python\n{base_strats}```

Here is the examples using price volume trend indicator :
```python\n{custom_examples}```

"""


# %%
from dotenv import load_dotenv
load_dotenv("/teamspace/studios/this_studio/sentiment_analysis/.env")

# %%
# Get example
import pandas as pd
import re
from my_dspy.dspy_signature import FinanceStrategyGenerator
from my_dspy.dspy_data import CSVDataset

FinanceStrategyGenerator.__doc__= instruction
    
# file_path = "Data/complex_trading_strategies.csv"
file_path = "Data/querstion_llm.csv"
dataset = CSVDataset(file_path=file_path, instruction=instruction)

# %%
# better net liquidation value view
from utils.errors_handler import error_tracking_decorator

class MyBuySell(bt.observers.BuySell):
    plotlines = dict(
        buy=dict(marker='$\u21E7$', markersize=12.0),
        sell=dict(marker='$\u21E9$', markersize=12.0)
    )

class CelebroCreator:
    def __init__(self, strategy, list_of_data, stake=100, cash=20000):
        # Initial cerebro
        self.cerebro = bt.Cerebro(cheat_on_open=True)
        
        self.cerebro.addstrategy(strategy)
        self.cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='SharpeRatio')
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='Returns')
        self.cerebro.addobserver(bt.observers.Value)

        for data in list_of_data:
            self.cerebro.adddata(data)
        self.cerebro.broker.set_cash(cash)
        bt.observers.BuySell = MyBuySell
        
        # CURRENT
        self.strats = None
        _, self.message = self._run_cerebro()

    
    # CURRENT
    @error_tracking_decorator
    def _run_cerebro(self):
        self.strats = self.cerebro.run()


    def show(self):
        print("Final Portfolio Value: %.2f" % self.cerebro.broker.getvalue())
        print("Total point return: ", (self.cerebro.broker.getvalue() - self.cerebro.broker.startingcash))

        try:
            sharpe_ratio = self.strats[0].analyzers.SharpeRatio.get_analysis()['sharperatio']
            print('Sharpe Ratio:', sharpe_ratio)
        except:
            print('No Buy/Sell Signal! No Sharpe Ratio!')
        # Plot the results
        figs = self.cerebro.plot(
            iplot=False, 
            # style="pincandle", 
            # width=60 * 10, height=40 * 10,
            figsize=(100, 80),
            # sharpe_ratio=sharpe_ratio
        )
        return figs

# %%
import traceback
import sys
from prompt_retry import prompt_error_template1, prompt_error_template2
from utils.file_text_handler import save_file
from utils.errors_handler import get_error


def check_valid_code(strategy, list_data):
    
    obj = CelebroCreator(strategy,list_data)
    count = {}
    
    if obj.strats is not None:
      count['BuySignal'] = obj.strats[0].cbuy
      count['SellSignal'] = obj.strats[0].csell
      
    message = obj.message
    errors = get_error(message) if message else ["",""]
    
    return errors, count



def check_valid_indicators(**kwargs):
    if kwargs['countBuy'] > 1 and \
       kwargs['countSell'] > 1:
        return True
    return False
    


class GenerateCodeWithAssert(dspy.Module):
  def __init__(self, list_ohcl_data):
    super().__init__()
    self.generate_result = dspy.ChainOfThought(FinanceStrategyGenerator)
    self.ohcl_data = list_ohcl_data
    self.num_retry = 0
    self.flag = 0
    self.complete = False
    self.still_errors = False
    self.max_retry = 8

  
  def forward(self, question):
    
    # Get answer
    ex = self.generate_result(question=question)
    
      
    if self.flag == 0:
        self.flag = 1
    else:
        self.num_retry += 1
        
    # Get and execute code
    exec(get_code_from_text(ex.answer), globals())
    

    # Extract Error
    errors,countSignal = check_valid_code(BackTestStrategy, self.ohcl_data)
    # -------------------
    
    # Check error in the code answer
    check = True if errors[0] == "" else False
    
    if not check:
        p_error = prompt_error_template1(errors=errors) if errors[-1] == "" else prompt_error_template2(errors=errors)
    else:
        p_error = ""
    
    dspy.Suggest(check, f"{p_error}")

    
    # Check the number of buy and sell signals
    check1 = False
    if countSignal:
      check1 = check_valid_indicators(countBuy=countSignal['BuySignal'], countSell=countSignal['SellSignal'])
      
      dspy.Suggest(check1, f"Please review and correct the formulas and conditions. Make sure the strategy includes at least one buy and one sell signal.")
    # ---------
    
    
    ex['num_retry'] = self.num_retry
    

    self.complete = True ex['num_retry'] <= self.max_retry and check1 == True else False
    self.still_errors = True if ex['num_retry'] == self.max_retry and check == False else False
    
    
    
    ex['status'] = {
      "Complete": self.complete,
      "Still_Error": self.still_errors
    }
    
    # Reset attributes
    self.num_retry, self.flag = 0, 0
    self.still_errors, self.complete = False, False
    
    return ex


# %%
from dspy.primitives.assertions import assert_transform_module, backtrack_handler
from data_loader import load_stock_data
from base_strategy_improved import BaseStrategy
from dspy.predict import Retry
import backtrader as bt
import dsp
import random
random.seed(42)


# Anyscale
lm = dspy.Anyscale(
    model="meta-llama/Meta-Llama-3-70B-Instruct",
    max_tokens=2048, 
    use_chat_api=True,
    temperature=0.0
)


dspy.settings.configure(lm=lm, trace=[])

data = [bt.feeds.PandasData(
                dataname=load_stock_data(ticker='AAPL', period="1y"), datetime="Date", 
                timeframe=bt.TimeFrame.Minutes)]

generate_with_assert = assert_transform_module(GenerateCodeWithAssert(list_ohcl_data=data).map_named_predictors(Retry), functools.partial(backtrack_handler, max_backtracks=8))


query = "Formulate a strategy to buy when the Gann Angles indicate support at a key level and the 14-day RSI is above 50 during a bullish market. Define sell conditions for when the Gann Angles indicate resistance at a key level and the RSI falls below 50."
# example = generate_with_assert(dataset.train[0].question)
example = generate_with_assert(query)

# print(f"Question: {dataset.train[0].question}")
print(f"Question: {query}")
print(f"Final Predicted Answer (after CoT process): {example.answer}")
print(f"Number of Retries: {example.num_retry}")

# %%
lm.inspect_history(n=3)

# %%
import matplotlib
%matplotlib inline

result = CelebroCreator(BackTestStrategy,data)
result.show()


# %%


# %% [markdown]
# 

# %% [markdown]
# # Bootstrap find the best few-shots 

# %%
from dspy.teleprompt import BootstrapFewShotWithRandomSearch
from dspy.evaluate import Evaluate
from my_dspy.dspy_metric import validate_answer



teleprompter = BootstrapFewShotWithRandomSearch(metric = validate_answer, max_bootstrapped_demos=3, num_candidate_programs=6)


generated_code_student_teacher = teleprompter.compile(
                student=assert_transform_module(
                    GenerateCodeWithAssert(list_ohcl_data=data).map_named_predictors(Retry), functools.partial(backtrack_handler, max_backtracks=8)), 
                teacher = assert_transform_module(
                    GenerateCodeWithAssert(list_ohcl_data=data).map_named_predictors(Retry), functools.partial(backtrack_handler, max_backtracks=5)), 
                trainset=dataset.train[:30], 
                valset=dataset.dev[:5]

)

# %%
generated_code_student_teacher.save("/teamspace/studios/this_studio/final_project/Trading_Project/module/new_code_generation_fewshot.json")

# %%
evaluate = Evaluate(
    devset = dataset.dev[-10:],
    metric = validate_answer,
    num_threads=3,
    display_progress=True,
    display_table=10
)

evaluate(generated_code_student_teacher)

# %%
question = "Develop a strategy that triggers a buy signal when the Parabolic SAR indicates an uptrend and the Chaikin Money Flow (CMF) is above zero, indicating buying pressure in a bullish market. Define sell conditions for when the Parabolic SAR indicates a downtrend and the CMF is below zero, indicating selling pressure."
example = generated_code_student_teacher(question=question)
example.answer

# %% [markdown]
# 

# %% [markdown]
# 


