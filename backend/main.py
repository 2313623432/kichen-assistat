from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FoodRequest(BaseModel):
    ingredients: str

llm = ChatOpenAI(
    model="deepseek-chat",
    api_key="sk-50b9c8e-xxxx-xxxx-xxxx-xxxxxxxxxxxx",  # 替换为你的API Key
    base_url="https://api.deepseek.com",
)

def search_bilibili_video(keyword):
    url = "https://api.bilibili.com/x/web-interface/search/all/v2"
    params = {"keyword": f"{keyword} 家常菜", "page": 1}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, params=params, headers=headers)
        data = res.json()
        for item in data["data"]["result"]:
            if item["result_type"] == "video":
                videos = sorted(item["data"], key=lambda x: x.get("play", 0), reverse=True)
                v = videos[0]
                title = v["title"].replace("<em class='keyword'>", "").replace("</em>", "")
                bv = v["bvid"]
                link = f"https://www.bilibili.com/video/{bv}"
                author = v["author"]
                play = f"{v['play']:,}"
                return f"标题：{title}\nUP主：{author}\n播放量：{play}\n链接：{link}"
        return "未找到视频"
    except:
        return "获取视频失败"

prompt = PromptTemplate.from_template("""
你是美食博主，根据视频信息，写出详细、美观、好看的菜谱。
不要用列表，不要限制步骤，段落自然舒服，排版优雅。

视频信息：{search_result}

输出格式（严格按这个HTML，好看、精致）：
<div class="result-card">
  <div class="video-box">
    <h4>🎬 推荐做菜视频</h4>
    <p>【标题】xxx</p>
    <p>【UP主】xxx</p>
    <p>【播放】xxx</p>
    <p>【观看】<a href="xxx" target="_blank">点击打开</a></p>
  </div>
  <div class="cook-box">
    <h4>🍳 详细做法</h4>
    <p>详细写做法，越多越好，越详细越好，段落清晰</p>
  </div>
</div>
""")

chain = prompt | llm | StrOutputParser()

@app.post("/api")
async def api(data: FoodRequest):
    try:
        video = search_bilibili_video(data.ingredients)
        res = chain.invoke({"search_result": video})
        return res
    except Exception as e:
        return f"<div class='err'>错误：{str(e)}</div>"