# Databricks notebook source
# MAGIC %md
# MAGIC # Load Llama-2-13b-chat-hf from LangChain on Databricks
# MAGIC
# MAGIC This example notebook is adapts the [LangChain integration documentation](https://python.langchain.com/docs/modules/model_io/models/llms/integrations/databricks), and shows how to wrap Databricks endpoints as LLMs in LangChain. It supports two endpoint types:
# MAGIC
# MAGIC - Serving endpoint, recommended for production and development. See `02_mlflow_logging_inference` for how to create one.
# MAGIC - Cluster driver proxy app, recommended for iteractive development. See `03_serve_driver_proxy` for how to create one.
# MAGIC
# MAGIC Environment tested:
# MAGIC - MLR: 13.2 ML
# MAGIC - Instance:
# MAGIC   - Wrapping a serving endpoint: `i3.xlarge` on AWS, `Standard_DS3_v2` on Azure
# MAGIC   - Wrapping a cluster driver proxy app: `g5.12xlarge` on AWS, `Standard_NV72ads_A10_v5` or `Standard_NC24ads_A100_v4` on Azure (same instance as the driver proxy app)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Wrapping a serving endpoint
# MAGIC The LangChain Databricks integration could wrap a serving endpoint.
# MAGIC
# MAGIC It requires a model serving endpoint (see `02_mlflow_logging_inference` for how to create one) to be in the "Ready" state.

# COMMAND ----------

# MAGIC %pip install -q -U langchain
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

from langchain.llms import Databricks

# This model serving endpoint is created in `02_mlflow_logging_inference`
llm = Databricks(endpoint_name='models.default.llama2_13b_chat_model')

# COMMAND ----------

result = llm("How to master Python in 3 days?", temperature=0.1, max_new_tokens=200)

displayHTML(result)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Wrapping a cluster driver proxy app
# MAGIC The LangChain Databricks integration also works when given the port that runs a proxy.
# MAGIC
# MAGIC It requires the driver proxy app of the `03_serve_driver_proxy` example notebook running.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Same cluster
# MAGIC If using the same cluster that runs the `03_serve_driver_proxy` notebook, specifying `cluster_driver_port` is required.

# COMMAND ----------

# MAGIC %pip install -q -U langchain
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

from langchain.llms import Databricks

# COMMAND ----------

llm = Databricks(cluster_driver_port="7777")

print(llm("How to master Python in 3 days?"))

# COMMAND ----------

# If the app accepts extra parameters like `temperature`,
# you can set them in `model_kwargs`.
llm = Databricks(cluster_driver_port="7777", model_kwargs={"temperature": 0.1})

print(llm("How to master Python in 3 days?"))

# COMMAND ----------

# Use `transform_input_fn` and `transform_output_fn` if the app
# expects a different input schema and does not return a JSON string,
# respectively, or you want to apply a prompt template on top.


def transform_input(**request):
    """
    Add more instructions into the prompt.
    """
    full_prompt = f"""[INST] Let's think step by step. [/INST]
    User: {request["prompt"]}
    """
    request["prompt"] = full_prompt
    return request


def transform_output(response):
    """
    Add timestamps for the anwsers.
    """
    from datetime import datetime
    now = datetime.now()
    current_time = now.strftime("%d/%m/%Y %H:%M:%S")
    return f"[{current_time}] llama2: {response}"


llm = Databricks(
    cluster_driver_port="7777",
    transform_input_fn=transform_input,
    transform_output_fn=transform_output,
)

print(llm("How to master Python in 3 days?"))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Different cluster
# MAGIC If using a different cluster, it's required to also specify `cluster_id`, which you can find in the cluster configuration page.

# COMMAND ----------

# MAGIC %pip install -q -U langchain
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

from langchain.llms import Databricks

# driver_proxy_api = 'https://dbc-11ce6ca4-7321.cloud.databricks.com/driver-proxy-api/o/0/1023-124355-2d7zvdkz/7777'
cluster_id = '1023-124355-2d7zvdkz'
port = 7777
host = "dbc-11ce6ca4-7321.cloud.databricks.com"

# Use `transform_input_fn` and `transform_output_fn` if the app
# expects a different input schema and does not return a JSON string,
# respectively, or you want to apply a prompt template on top.


def transform_input(**request):
    """
    Add more instructions into the prompt.
    """
    full_prompt = f"""[INST] Let's think step by step. [/INST]
    User: {request["prompt"]}
    """
    request["prompt"] = full_prompt
    return request


def transform_output(response):
    """
    Add timestamps for the anwsers.
    """
    from datetime import datetime
    now = datetime.now()
    current_time = now.strftime("%d/%m/%Y %H:%M:%S")
    return f"[{current_time}] llama2: {response}"


api_token = dbutils.secrets.get(scope="llmtraining", key="model_api_token")
# TODO: this cluster ID is a place holder, please replace `cluster_id` with the actual cluster ID of the server proxy app's cluster
llm = Databricks(host=host, cluster_id=cluster_id, cluster_driver_port="7777", api_token=api_token,
                 transform_input_fn=transform_input,
        transform_output_fn=transform_output,)

print(llm("How to master Python in 3 days?"))

# COMMAND ----------

import requests
import json

# Value was generated in 03_serve_driver_proxy notebook
driver_proxy_api = 'https://dbc-11ce6ca4-7321.cloud.databricks.com/driver-proxy-api/o/0/1023-124355-2d7zvdkz/7777'

def request_chat(prompt, temperature=1.0, max_new_tokens=1024):
  # I have added this already to secrets
  token = dbutils.secrets.get(scope="llmtraining", key="model_api_token") # TODO: fill in with your Databricks personal access token that can access the cluster that runs this driver proxy notebook
  url = 'https://dbc-11ce6ca4-7321.cloud.databricks.com/driver-proxy-api/o/0/1023-124355-2d7zvdkz/7777'
  
  headers = {
      "Content-Type": "application/json",
      "Authentication": f"Bearer {token}"
  }
  data = {
    "prompt": prompt,
    "temperature": temperature,
    "max_new_tokens": max_new_tokens,
  }
  response = requests.post(url, headers=headers, data=json.dumps(data))
  return response.text


print(request_chat("How to master Python in 3 days?"))

# COMMAND ----------


