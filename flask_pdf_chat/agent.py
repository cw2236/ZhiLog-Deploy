from typing import Dict, List, Tuple, Any
import openai
from flask import session
import json
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
from agent_logger import AgentOperationLogger
import time
import os

# Perplexity API 封装
PPLX_API_KEY = os.environ.get("PPLX_API_KEY")
if not PPLX_API_KEY:
    raise ValueError("Please set the environment variable PPLX_API_KEY")
def call_perplexity(messages, model="sonar", temperature=0.7, max_tokens=500):
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {PPLX_API_KEY}",
        "Content-Type": "application/json"
    }
    # 只保留 role 和 content 字段
    clean_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
    data = {
        "model": model,
        "messages": clean_messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    response = requests.post(url, headers=headers, json=data, timeout=60)
    try:
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.HTTPError as e:
        print("Perplexity API error:", response.text)
        raise

class Agent:
    def __init__(self):
        self.tools = {
            "search_pdf": self.search_pdf,
            "summarize": self.summarize,
            "ask_question": self.ask_question,
            "add_note": self.add_note,
            "web_search": self.web_search,
            "goto_upload_page": self.goto_upload_page
        }
        
    def search_pdf(self, query: str) -> List[Dict]:
        """Search for related content in PDF"""
        if 'pdf_content' not in session:
            return []
        
        # 简单的文本匹配，实际项目中可以用更复杂的搜索算法
        results = []
        for page_num, content in session['pdf_content'].items():
            if query.lower() in content.lower():
                results.append({
                    'page': page_num,
                    'content': content
                })
        return results
    
    def summarize(self, text: str) -> str:
        """Generate text summary"""
        try:
            messages = [
                {"role": "system", "content": "You are a professional text summarization assistant."},
                {"role": "user", "content": f"Please generate a concise summary for the following text:\n\n{text}"}
            ]
            return call_perplexity(messages)
        except Exception as e:
            return f"Error occurred while generating summary: {str(e)}"
    
    def ask_question(self, question: str, context: str = "") -> str:
        """Answer question based on context"""
        try:
            messages = [
                {"role": "system", "content": "You are a professional question-answering assistant."}
            ]
            if context:
                messages.append({
                    "role": "system",
                    "content": f"Reference the following context:\n{context}"
                })
            messages.append({"role": "user", "content": question})
            return call_perplexity(messages)
        except Exception as e:
            return f"Error occurred while answering question: {str(e)}"
    
    def add_note(self, content: str) -> str:
        """Add note"""
        if 'notes' not in session:
            session['notes'] = []
        
        session['notes'].append(content)
        return "Note added"
    
    def parse_intent(self, user_input: str) -> Tuple[str, str, List[Any]]:
        """Parse user intent to determine which tool to call"""
        try:
            messages = [
                {"role": "system", "content": (
                    "You are an intent parsing assistant. Please analyze user input to determine whether to call a tool and which tool to call."
                    "If the user's question involves latest information, internet, news, search, real-time data, etc., prioritize calling the web_search tool."
                    "If the user expresses intentions like 'upload file', 'import document', 'add material', etc., prioritize calling the goto_upload_page tool."
                    "Available tools: search_pdf, summarize, ask_question, add_note, web_search, goto_upload_page."
                    "Example:\n"
                    "User input: I want to upload a new PDF\n"
                    "Return: {\"intent\": \"upload file\", \"tool\": \"goto_upload_page\", \"args\": []}\n"
                    "Please return in JSON format: {\"intent\": \"intent description\", \"tool\": \"tool name\", \"args\": [parameter list]}"
                )},
                {"role": "user", "content": f"User input: {user_input}\n\nAvailable tools: {list(self.tools.keys())}\n\nPlease return in JSON format: {{\"intent\": \"intent description\", \"tool\": \"tool name\", \"args\": [parameter list]}}"}
            ]
            plan = call_perplexity(messages)
            result = json.loads(plan)
            return result["intent"], result["tool"], result["args"]
        except Exception as e:
            return "Cannot understand intent", "", []
    
    def generate_guide_question(self, intent: str) -> str:
        """Generate guiding question"""
        try:
            messages = [
                {"role": "system", "content": "You are a learning guidance assistant. Please generate a guiding question that helps deepen learning based on the user's learning intent."},
                {"role": "user", "content": f"User intent: {intent}"}
            ]
            return call_perplexity(messages)
        except Exception as e:
            return ""
    
    def respond(self, user_input: str) -> Dict:
        """Process user input and generate response"""
        # Parse intent
        intent, tool_name, tool_args = self.parse_intent(user_input)
        
        # If a tool needs to be called
        if tool_name in self.tools:
            tool_func = self.tools[tool_name]
            tool_result = tool_func(*tool_args)
            # Log (at the moment of calling the tool)
            AgentOperationLogger.log(tool_name, tool_args, tool_result)
            response = f"I found for you: {tool_result}"
        else:
            # Direct conversation
            response = self.ask_question(user_input)
            # Fallback: If the large model's reply contains words like "cannot access the internet" or "knowledge cutoff", it will automatically call web_search
            if any(x in response for x in ["cannot access the internet", "cannot connect to the internet", "knowledge cutoff", "cannot get the latest", "please query", "cannot search", "cannot access the internet"]):
                web_result = self.web_search(user_input)
                response += f"\n【Real-time search results】\n{web_result}"
            # Log (direct conversation)
            AgentOperationLogger.log('ask_question', [user_input], response)
        # Generate guiding question
        guide_question = self.generate_guide_question(intent)
        
        return {
            "response": response,
            "guide_question": guide_question,
            "tool_used": tool_name if tool_name else None
        }

    def fetch_and_summarize(self, urls: list, query: str) -> str:
        texts = []
        for url in urls[:2]:  # Only grab the first 2
            try:
                resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(resp.text, "html.parser")
                ps = soup.find_all(['p'])
                content = "\n".join([p.get_text() for p in ps if len(p.get_text()) > 30])
                if content:
                    texts.append(content[:2000])  # Each article at most 2000 characters
            except Exception as e:
                continue
        if not texts:
            return "Could not retrieve valid web page content."
        # Use large model to summarize
        client = openai.OpenAI()
        prompt = (
            f"Please answer the user's question directly based on the following web page content:\n"
            "Do not say 'not mentioned', 'cannot determine', 'please check yourself' etc. If there is an answer in the web page content, please directly extract and briefly express it.\n\n"
            "【Web page content】\n"
            + "\n\n".join(texts)
        )
        response = client.chat.completions.create(
            model="openai.gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional information retrieval and summary assistant, and can only answer based on web page content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content

    def web_search(self, query: str) -> str:
        try:
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=3)
                output = []
                urls = []
                for r in results:
                    output.append(f"{r['title']}: {r['href']}")
                    urls.append(r['href'])
                summary = self.fetch_and_summarize(urls, query)
                return f"{summary}\n\n【Original search results】\n" + ("\n".join(output) if output else "No related results found")
        except Exception as e:
            return f"Error occurred while searching: {str(e)}"

    def goto_upload_page(self) -> str:
        return "Please jump to the file upload page."

    def autonomous_run(self, user_goal: str, max_steps=5):
        """
        Automatically call tool chain multiple times based on user goal until task completion or maximum steps reached.
        Each step is logged, and the final return is all step trajectories.
        """
        observation = ""
        steps = []
        for step in range(1, max_steps + 1):
            # 1. Let large model plan next step
            plan_prompt = (
                f"Your goal: {user_goal}\n"
                f"Current observation/result: {observation}\n"
                f"You can use the following tools: {list(self.tools.keys())}\n"
                "You can use multiple tools, each time using the result of the previous step as input, until the goal is fully achieved.\n"
                "If only web_search gets original web page content or summary, please continue using summarize, add_note, etc. tools until the goal is fully achieved.\n"
                "Only stop when you think the goal is fully achieved. Otherwise, please continue to the next step.\n"
                "Special note: If the user goal involves 'latest', '2025', 'future', 'current', etc., or you are unsure about the answer, you must first use the web_search tool to get the latest information, then proceed with subsequent summary or note.\n"
                "If you find yourself knowledge cutoff or unsure, you must first use web_search.\n"
                "Return format: {\"tool\": \"tool name\", \"args\": [parameters], \"stop\": true/false, \"thought\": \"your thinking process\"}\n"
                "Example:\n"
                "Step 1: {\"tool\": \"web_search\", \"args\": [\"AI 2025 news\"], \"stop\": false, \"thought\": \"First find the latest AI news\"}\n"
                "Step 2: {\"tool\": \"summarize\", \"args\": [previous step result], \"stop\": false, \"thought\": \"Summarize news content\"}\n"
                "Step 3: {\"tool\": \"add_note\", \"args\": [previous step result], \"stop\": true, \"thought\": \"Save summary content as note, task completed\"}\n"
            )
            messages = [
                {"role": "system", "content": "You are a smart body that can call multiple tools autonomously. Each time you need to decide the next step based on the goal and the result of the previous step."},
                {"role": "user", "content": plan_prompt}
            ]
            plan = call_perplexity(messages, max_tokens=400)
            try:
                plan_json = json.loads(plan)
                tool_name = plan_json.get("tool")
                tool_args = plan_json.get("args", [])
                should_stop = plan_json.get("stop", False)
                thought = plan_json.get("thought", "")
            except Exception:
                # Parse failed, terminate
                break

            # 2. Call tool
            if tool_name not in self.tools:
                break
            result = self.tools[tool_name](*tool_args)
            AgentOperationLogger.log(tool_name, tool_args, result)
            steps.append({
                "step": step,
                "tool": tool_name,
                "input": tool_args,
                "output": result,
                "thought": thought
            })
            observation = str(result)
            # summarize fallback: If the first step is web_search and stop==True, summarize automatically
            if step == 1 and tool_name == "web_search" and str(should_stop).lower() == "true":
                sum_result = self.tools["summarize"](observation)
                AgentOperationLogger.log("summarize", [observation], sum_result)
                steps.append({
                    "step": 2,
                    "tool": "summarize",
                    "input": [observation],
                    "output": sum_result,
                    "thought": "Summarize fallback automatically after web_search"
                })
                break
            if str(should_stop).lower() == "true":
                break
        return steps

# Create global agent instance
agent = Agent() 