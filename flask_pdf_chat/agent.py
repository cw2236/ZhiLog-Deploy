from typing import Dict, List, Tuple, Any
import openai
from flask import session
import json
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
from agent_logger import AgentOperationLogger
import time

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
        """在 PDF 中搜索相关内容"""
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
        """生成文本摘要"""
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="openai.gpt-4o",
                messages=[
                    {"role": "system", "content": "你是一个专业的文本摘要助手。"},
                    {"role": "user", "content": f"请为以下文本生成一个简洁的摘要：\n\n{text}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"生成摘要时出错：{str(e)}"
    
    def ask_question(self, question: str, context: str = "") -> str:
        """基于上下文回答问题"""
        try:
            client = openai.OpenAI()
            messages = [
                {"role": "system", "content": "你是一个专业的问答助手。"}
            ]
            
            if context:
                messages.append({
                    "role": "system", 
                    "content": f"参考以下上下文：\n{context}"
                })
            
            messages.append({"role": "user", "content": question})
            
            response = client.chat.completions.create(
                model="openai.gpt-4o",
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"回答问题时出错：{str(e)}"
    
    def add_note(self, content: str) -> str:
        """添加笔记"""
        if 'notes' not in session:
            session['notes'] = []
        
        session['notes'].append(content)
        return "笔记已添加"
    
    def parse_intent(self, user_input: str) -> Tuple[str, str, List[Any]]:
        """解析用户意图，决定调用哪个工具"""
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="openai.gpt-4o",
                messages=[
                    {"role": "system", "content": (
                        "你是一个意图解析助手。请分析用户输入，决定是否需要调用工具，以及调用哪个工具。"
                        "如果用户的问题涉及最新信息、互联网、新闻、查找、实时数据等，优先调用 web_search 工具。"
                        "如果用户表达了'上传文件''导入文档''添加资料'等意图，优先调用 goto_upload_page 工具。"
                        "可用工具：search_pdf, summarize, ask_question, add_note, web_search, goto_upload_page。"
                        "示例：\n"
                        "用户输入：我要上传一个新的PDF\n"
                        "返回：{\"intent\": \"上传文件\", \"tool\": \"goto_upload_page\", \"args\": []}\n"
                        "请以JSON格式返回：{\"intent\": \"意图描述\", \"tool\": \"工具名\", \"args\": [参数列表]}"
                    )},
                    {"role": "user", "content": f"用户输入：{user_input}\n\n可用工具：{list(self.tools.keys())}\n\n请以JSON格式返回：{{\"intent\": \"意图描述\", \"tool\": \"工具名\", \"args\": [参数列表]}}"}
                ]
            )
            result = json.loads(response.choices[0].message.content)
            return result["intent"], result["tool"], result["args"]
        except Exception as e:
            return "无法理解意图", "", []
    
    def generate_guide_question(self, intent: str) -> str:
        """生成引导性问题"""
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="openai.gpt-4o",
                messages=[
                    {"role": "system", "content": "你是一个学习引导助手。请根据用户的学习意图，生成一个有助于深入学习的引导性问题。"},
                    {"role": "user", "content": f"用户意图：{intent}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return ""
    
    def respond(self, user_input: str) -> Dict:
        """处理用户输入并生成回复"""
        # 解析意图
        intent, tool_name, tool_args = self.parse_intent(user_input)
        
        # 如果需要调用工具
        if tool_name in self.tools:
            tool_func = self.tools[tool_name]
            tool_result = tool_func(*tool_args)
            # 记录日志（调用工具的那一刻）
            AgentOperationLogger.log(tool_name, tool_args, tool_result)
            # 如果是跳转上传页，直接返回，不再生成其它内容
            if tool_name == "goto_upload_page":
                return {
                    "response": tool_result,
                    "guide_question": "",
                    "tool_used": tool_name
                }
            response = f"我为你找到了：{tool_result}"
        else:
            # 直接对话
            response = self.ask_question(user_input)
            # 兜底：如大模型回复中出现无法联网/知识截止等字样，则自动调用web_search
            if any(x in response for x in ["无法实时访问互联网", "无法联网", "知识截止", "无法获取最新", "请查询", "无法检索", "无法访问互联网"]):
                web_result = self.web_search(user_input)
                response += f"\n【实时搜索结果】\n{web_result}"
            # 记录日志（直接对话）
            AgentOperationLogger.log('ask_question', [user_input], response)
        # 生成引导性问题
        guide_question = self.generate_guide_question(intent)
        
        return {
            "response": response,
            "guide_question": guide_question,
            "tool_used": tool_name if tool_name else None
        }

    def fetch_and_summarize(self, urls: list, query: str) -> str:
        texts = []
        for url in urls[:2]:  # 只抓前2个
            try:
                resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(resp.text, "html.parser")
                ps = soup.find_all(['p'])
                content = "\n".join([p.get_text() for p in ps if len(p.get_text()) > 30])
                if content:
                    texts.append(content[:2000])  # 每篇最多2000字
            except Exception as e:
                continue
        if not texts:
            return "未能抓取到有效网页内容。"
        # 用大模型总结
        client = openai.OpenAI()
        prompt = (
            f"请只根据下方网页内容，直接回答用户问题：{query}\n"
            "不要说'未提及'、'无法判断'、'请自行查阅'等。如果网页内容中有答案，请直接提取并简明表述。\n\n"
            "【网页内容】\n"
            + "\n\n".join(texts)
        )
        response = client.chat.completions.create(
            model="openai.gpt-4o",
            messages=[
                {"role": "system", "content": "你是一个专业的信息检索与总结助手，只能根据网页内容作答。"},
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
                return f"{summary}\n\n【原始搜索结果】\n" + ("\n".join(output) if output else "未找到相关结果")
        except Exception as e:
            return f"搜索时出错：{str(e)}"

    def goto_upload_page(self) -> str:
        return "请跳转到文件上传页面。"

    def autonomous_run(self, user_goal: str, max_steps=5):
        """
        根据用户目标，自动多步调用工具链，直到任务完成或达到最大步数。
        每一步都记录日志，最终返回所有步骤轨迹。
        """
        observation = ""
        steps = []
        for step in range(1, max_steps + 1):
            # 1. 让大模型规划下一步
            plan_prompt = (
                f"你的目标：{user_goal}\n"
                f"当前观察/结果：{observation}\n"
                f"你可以使用的工具：{list(self.tools.keys())}\n"
                "请输出下一步要用的工具、输入参数（用JSON数组），以及是否终止任务（true/false）。"
                "返回格式：{\"tool\": \"工具名\", \"args\": [参数], \"stop\": true/false, \"thought\": \"你的思考过程\"}"
            )
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="openai.gpt-4o",
                messages=[
                    {"role": "system", "content": "你是一个可以自主多步调用工具的智能体，每一步都要根据目标和上一步结果决定下一步。"},
                    {"role": "user", "content": plan_prompt}
                ],
                temperature=0.3,
                max_tokens=400
            )
            plan = response.choices[0].message.content
            try:
                plan_json = json.loads(plan)
                tool_name = plan_json.get("tool")
                tool_args = plan_json.get("args", [])
                should_stop = plan_json.get("stop", False)
                thought = plan_json.get("thought", "")
            except Exception:
                # 解析失败，终止
                break

            # 2. 调用工具
            if tool_name not in self.tools:
                break
            result = self.tools[tool_name](*tool_args)
            AgentOperationLogger.log(tool_name, tool_args, result)
            # 如果是跳转上传页，立即终止并只返回该步骤
            if tool_name == "goto_upload_page":
                steps.append({
                    "step": step,
                    "tool": tool_name,
                    "input": tool_args,
                    "output": result,
                    "thought": thought
                })
                break
            steps.append({
                "step": step,
                "tool": tool_name,
                "input": tool_args,
                "output": result,
                "thought": thought
            })
            observation = str(result)
            if should_stop:
                break
        return steps

# 创建全局 agent 实例
agent = Agent() 