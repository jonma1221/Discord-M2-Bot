from openai import OpenAI
client = OpenAI()

response = client.responses.create(
    model="gpt-5.2",
    input="This is a test prompt from a python script."
)

print(response.output_text)