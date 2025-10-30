import httpx
import os
from typing import Optional, Dict, Any
import json


class LLMClient:
    """
    Flexible LLM client that can work with:
    - OpenWebUI API
    - aichat-ng (via HTTP if configured)
    - OpenAI-compatible endpoints
    """

    def __init__(
        self,
        model_name: str,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 120,
    ):
        self.model_name = model_name
        self.api_base = api_base or os.getenv("LLM_API_BASE", "http://localhost:11434")
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.timeout = timeout

    async def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Send a chat request to the LLM"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # OpenAI-compatible format
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                payload = {
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }

                headers = {"Content-Type": "application/json"}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                # Try OpenAI-compatible endpoint first
                response = await client.post(
                    f"{self.api_base}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )

                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    # Fallback to Ollama format if OpenAI format fails
                    ollama_payload = {
                        "model": self.model_name,
                        "prompt": prompt,
                        "system": system_prompt,
                        "stream": False,
                    }
                    response = await client.post(
                        f"{self.api_base}/api/generate",
                        json=ollama_payload,
                        headers={"Content-Type": "application/json"},
                    )
                    if response.status_code == 200:
                        result = response.json()
                        return result.get("response", "")

                raise Exception(f"LLM API error: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"Error calling LLM: {e}")
            # Return a safe fallback
            return f"[LLM Error: {str(e)}]"


class Secretary(LLMClient):
    """The secretary - receives raw input and interprets it"""

    def __init__(self):
        super().__init__(
            model_name=os.getenv("SECRETARY_MODEL", "qwen2.5:7b"),
            api_base=os.getenv("SECRETARY_API_BASE"),
        )

    async def process_input(self, raw_input: str) -> Dict[str, Any]:
        """Take raw input and return structured understanding"""
        system_prompt = """You are a helpful secretary. The user has severe ADHD and memory issues.
They will give you very short, possibly cryptic notes about tasks or ideas.
Your job is to:
1. Understand what they mean (they know what they mean, even if it's one word)
2. Extract any implicit urgency or importance
3. NOT ask questions - just interpret based on context
4. Return ONLY a JSON object with these fields:
   - processed_text: Your understanding of the task
   - implicit_urgency: low/medium/high
   - is_life_critical: true if it's about health, meds, food, basic survival
   - is_quick_win: true if it seems like a fast task
   - category_guess: your best guess at category
   - notes: any helpful context

Example input: "pillows walmart"
Example output: {"processed_text": "Order pillows from Walmart", "implicit_urgency": "medium", "is_life_critical": false, "is_quick_win": true, "category_guess": "shopping", "notes": "User has been trying to order these"}

Return ONLY valid JSON, no other text."""

        response = await self.chat(raw_input, system_prompt=system_prompt, temperature=0.3)

        # Try to parse JSON from response
        try:
            # Find JSON in response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except:
            pass

        # Fallback if JSON parsing fails
        return {
            "processed_text": raw_input,
            "implicit_urgency": "low",
            "is_life_critical": False,
            "is_quick_win": False,
            "category_guess": "misc",
            "notes": "Could not process",
        }


class Organizer(LLMClient):
    """The organizer - manages multiple tasks and categorizes"""

    def __init__(self):
        super().__init__(
            model_name=os.getenv("ORGANIZER_MODEL", "granite-code:8b"),
            api_base=os.getenv("ORGANIZER_API_BASE"),
        )

    async def categorize_tasks(self, tasks: list) -> Dict[str, Any]:
        """Look at multiple tasks and organize them"""
        system_prompt = """You are a task organizer. Look at these tasks and group them logically.
Consider: similar themes, related activities, what could be done together.
The user has ADHD and works best with loose groupings, not rigid categories.
Return JSON with category suggestions."""

        task_summary = "\n".join([f"- {t['raw_input']}" for t in tasks[:20]])
        prompt = f"Here are the current tasks:\n{task_summary}\n\nSuggest categories and groupings."

        response = await self.chat(prompt, system_prompt=system_prompt, temperature=0.5)
        return {"analysis": response}


class Prioritizer(LLMClient):
    """The prioritizer - assesses importance without being rigid"""

    def __init__(self):
        super().__init__(
            model_name=os.getenv("PRIORITIZER_MODEL", "mistral:7b-instruct"),
            api_base=os.getenv("PRIORITIZER_API_BASE"),
        )

    async def assess_priority(self, task: Dict[str, Any], context: list) -> float:
        """Assess task priority (0-1 scale) considering context"""
        system_prompt = """You are assessing task priority for someone with ADHD and memory issues.
Priority factors:
- Life critical (meds, food, health): HIGHEST
- Has deadline approaching: HIGH
- Is blocking other tasks: HIGH
- Is interesting but not urgent: LOWER (these are tempting distractions!)
- Quick wins when stuck: MEDIUM-HIGH

Return ONLY a number between 0 and 1, nothing else.
0.9-1.0: Critical (health, safety, urgent needs)
0.7-0.8: Important (time-sensitive, necessary)
0.5-0.6: Normal (good to do, not urgent)
0.3-0.4: Low (nice to have)
0.0-0.2: Later (can wait indefinitely)"""

        task_info = f"Task: {task.get('processed_text', task.get('raw_input'))}"
        if task.get("is_life_critical"):
            task_info += "\n- This is life critical (health/safety)"
        if task.get("due_by"):
            task_info += f"\n- Due by: {task['due_by']}"

        response = await self.chat(task_info, system_prompt=system_prompt, temperature=0.3)

        # Parse priority from response
        try:
            # Extract first number between 0 and 1
            import re

            match = re.search(r"0?\.\d+|[01]\.0", response)
            if match:
                priority = float(match.group())
                return max(0.0, min(1.0, priority))
        except:
            pass

        # Default priority
        return 0.5
