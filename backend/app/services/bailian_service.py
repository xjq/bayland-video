import json
import re
from typing import List, Optional
from openai import OpenAI
from ..config import Config


class BailianService:
    """百炼API调用服务"""

    def __init__(self):
        self.client = OpenAI(
            api_key=Config.DASHSCOPE_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

    def split_text(self, original_text: str) -> List[str]:
        """调用qwen-max拆分文案为15s片段"""
        system_prompt = """你是一个视频脚本专家。请将用户输入的口播文案拆分为多个适合15秒口播的片段。

要求：
1. 每个片段应该是完整的句子或段落，内容连贯
2. 每个片段大概300字，适合15秒的口播
3. 保持原文的逻辑顺序和语义完整性
4. 不要添加或删除原文内容，只做切分 
5. 以JSON数组格式返回，每个元素是一个片段文本

只返回JSON数组，不要有其他内容。示例格式：
["第一段文案内容", "第二段文案内容", "第三段文案内容"]"""

        response = self.client.chat.completions.create(
            model=Config.TEXT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": original_text}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        result_text = response.choices[0].message.content.strip()
        
        # 尝试提取JSON数组
        try:
            # 尝试直接解析
            segments = json.loads(result_text)
        except json.JSONDecodeError:
            # 尝试从文本中提取JSON数组
            match = re.search(r'\[.*\]', result_text, re.DOTALL)
            if match:
                segments = json.loads(match.group())
            else:
                # 如果无法解析，按段落分割
                segments = [p.strip() for p in original_text.split('\n\n') if p.strip()]

        return segments

    def optimize_to_prompt(self, segment_text: str) -> str:
        """调用qwen-max将文案转换为视频提示词"""
        system_prompt = """你是视频生成专家。请将口播文案转换为适合AI视频生成模型的提示词。

要求：
1. 提示词应该描述视觉场景、人物动作、环境氛围，而非口播内容本身
2. 使用具体的视觉描述词汇
3. 保持简洁，控制在80字以内
4. 可以包含镜头语言描述（如：特写、全景、平移等）

只返回提示词文本，不要有其他解释。"""

        response = self.client.chat.completions.create(
            model=Config.TEXT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请将以下口播文案转换为视频生成提示词：\n{segment_text}"}
            ],
            temperature=0.8,
            max_tokens=200
        )

        return response.choices[0].message.content.strip()

    def optimize_to_prompt2(self, segment_text: str) -> str:

        prefix = "Create a realistic, high-quality talking-head video of a friendly and knowledgeable health-conscious speaker (gender-neutral or female-presenting, natural appearance, soft lighting, neutral background). The speaker delivers the following script in a clear, conversational tone with appropriate facial expressions and lip-sync accuracy:"
        sufix = "Ensure natural mouth movements, subtle head gestures, and authentic eye contact. The video should be 1080p, well-lit, with clean audio synchronization, and a calm, trustworthy atmosphere—ideal for wellness or natural health content."
        return prefix + segment_text + sufix

    def submit_video_task(self, prompt: str, image_url: str) -> dict:
        """提交视频生成任务（i2v图生视频模式）"""
        import requests
        
        if not image_url:
            return {
                "success": False,
                "error": "i2v模式需要提供首帧图片"
            }
        
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis"
        headers = {
            "Authorization": f"Bearer {Config.DASHSCOPE_API_KEY}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"
        }
        
        payload = {
            "model": Config.VIDEO_MODEL,
            "input": {
                "prompt": prompt,
                "img_url": image_url
            },
            "parameters": {
                "duration": Config.VIDEO_DURATION,
                "size": Config.VIDEO_RESOLUTION,
                "prompt_extend": Config.VIDEO_PROMPT_EXTEND
            }
        }

        print(f"\n{'='*60}")
        print(f"[百炼] 提交视频生成任务")
        print(f"[百炼] 模型: {Config.VIDEO_MODEL}")
        print(f"[百炼] 图片URL: {image_url}")
        print(f"[百炼] 提示词: {prompt[:100]}..." if len(prompt) > 100 else f"[百炼] 提示词: {prompt}")
        print(f"[百炼] 参数: duration={Config.VIDEO_DURATION}, size={Config.VIDEO_RESOLUTION}, prompt_extend={Config.VIDEO_PROMPT_EXTEND}")
        print(f"[百炼] 请求URL: {url}")

        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        
        print(f"[百炼] HTTP状态码: {response.status_code}")
        print(f"[百炼] 响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
        print(f"{'='*60}\n")
        
        if "output" in result and "task_id" in result["output"]:
            return {
                "success": True,
                "task_id": result["output"]["task_id"]
            }
        else:
            return {
                "success": False,
                "error": result.get("message", str(result))
            }

    def query_video_task(self, task_id: str) -> dict:
        """查询视频任务状态"""
        import requests
        
        url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
        headers = {
            "Authorization": f"Bearer {Config.DASHSCOPE_API_KEY}"
        }

        response = requests.get(url, headers=headers)
        result = response.json()
        
        print(f"\n[百炼] 查询任务状态: {task_id}")
        print(f"[百炼] HTTP状态码: {response.status_code}")
        print(f"[百炼] 响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if "output" not in result:
            print(f"[百炼] 错误: 响应中没有output字段")
            return {
                "status": "failed",
                "error": result.get("message", str(result))
            }

        output = result["output"]
        task_status = output.get("task_status", "UNKNOWN")
        
        print(f"[百炼] 任务状态: {task_status}")
        if output.get("video_url"):
            print(f"[百炼] 视频URL: {output['video_url']}")
        if output.get("message"):
            print(f"[百炼] 消息: {output['message']}")
        
        status_map = {
            "PENDING": "pending",
            "RUNNING": "generating",
            "SUCCEEDED": "completed",
            "FAILED": "failed"
        }

        return {
            "status": status_map.get(task_status, "pending"),
            "video_url": output.get("video_url"),
            "error": output.get("message")
        }
