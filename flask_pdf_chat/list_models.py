import openai

client = openai.OpenAI()
models = client.models.list()
for m in models.data:
    print(m.id) 