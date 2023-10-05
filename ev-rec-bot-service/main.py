import os
import asyncio
import base64

import asyncpg
from flask import Flask, request
from google.cloud.sql.connector import Connector
from langchain.chains import LLMChain
from langchain.chat_models import ChatVertexAI
from langchain.llms import VertexAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage
import vertexai


app = Flask(__name__)

PROJECT_ID = "duwenxin-space"  # @param {type:"string"}
vertexai.init(project=PROJECT_ID, location="us-central1")


class Bot:

  def __init__(self):
    self.llm = VertexAI(
        model_name="text-bison@001",
        temperature=0.1,
        top_p=0.8,
        top_k=40,
        verbose=True,
        max_output_tokens=1024,
    )

  def query_bot(self, matches):
    # LLM model

    template = (
        "You are a nice AI bot that helps a user figure out whichalternative"
        " fuel vehicle to purchase. You are given the data of 5 car models:"
        " {car_data} describe the pros and cons of 5 model according to their"
        " specifications. Begin your response with'These are the alternative"
        " fuel vehicles models I recommend for you:'"
    )

    prompt = PromptTemplate(input_variables=["car_data"], template=template)
    llm_chain = LLMChain(prompt=prompt, llm=self.llm)
    answer = llm_chain.run({
        "car_data": matches.__str__(),
    })
    return answer


async def query_db(matches, params):
  loop = asyncio.get_running_loop()
  async with Connector(loop=loop) as connector:
    # Create connection to Cloud SQL database.
    conn: asyncpg.Connection = await connector.connect_async(
        "duwenxin-space:us-central1:ev-recommendation",
        "asyncpg",
        user="postgres",
        password="Fairwinds9)db",
        db="Alternative-Fuel-Vehicles-US",
    )

    query = """
        SELECT * FROM ev_table
        WHERE fuel = '{}'
        AND conventional_fuel_economy_combined != 'nan'
        AND CAST(conventional_fuel_economy_combined AS Float) >= {}
        """.format(
        params["fuel"],
        params["min_conventional_fuel_economy_combined"],
    )

    # Find similar products to the query using cosine similarity search
    # over all vector embeddings. This new feature is provided by `pgvector`.
    results = await conn.fetch(query)

    if len(results) == 0:
      raise Exception("Did not find any results. Adjust the query parameters.")

    for r in results:
      # Collect the description for all the matched similar toy products.
      matches.append({
          "category": r["category"],
          "model": r["model"],
          "model_year": r["model_year"],
          "manufacturer": r["manufacturer"],
          "fuel": r["fuel"],
          "conventional_fuel_economy_combined": r[
              "conventional_fuel_economy_combined"
          ],
          "drivetrain": r["drivetrain"],
      })

    await conn.close()



@app.route("/chat/<fuel>/<min_conventional_fuel_economy_combined>")
async def main(fuel, min_conventional_fuel_economy_combined):
  fuel = fuel.replace('%20', ' ')
  matches = []
  params = {
      "fuel": fuel,
      "min_conventional_fuel_economy_combined": int(min_conventional_fuel_economy_combined),
  }
  await query_db(matches, params)
  matches = matches[:10]

  bot = Bot()
  return bot.query_bot(matches)


if __name__ == "__main__":
  app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
