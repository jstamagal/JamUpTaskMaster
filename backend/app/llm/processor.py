"""
Single-model task processor using gpt-oss-assistant
Modular design for future expansion
"""
import httpx
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime


class TaskProcessor:
    """
    Main brain - processes tasks using gpt-oss-assistant
    Designed to be swappable/extensible
    """

    def __init__(
        self,
        model_name: str = "gpt-oss-20b-assistant:latest",
        api_base: str = "http://localhost:11434",
        timeout: int = 120,
    ):
        self.model_name = model_name
        self.api_base = api_base
        self.timeout = timeout

    async def _call_model(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        """Call the LLM via Ollama API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": temperature},
                }

                if system_prompt:
                    payload["system"] = system_prompt

                response = await client.post(
                    f"{self.api_base}/api/generate",
                    json=payload,
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
                else:
                    raise Exception(f"API error: {response.status_code}")

        except Exception as e:
            print(f"Error calling model: {e}")
            return ""

    async def process_new_tasks(
        self,
        new_tasks: List[Dict[str, Any]],
        existing_tasks: List[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process new tasks with full context awareness
        Returns updated task data for each new task
        """
        existing_tasks = existing_tasks or []

        # Build context
        context_prompt = self._build_context_prompt(new_tasks, existing_tasks)

        # Call model
        response = await self._call_model(
            context_prompt,
            system_prompt=self._get_system_prompt(),
            temperature=0.3,
        )

        # Parse response
        return self._parse_response(response, new_tasks)

    def _get_system_prompt(self) -> str:
        """System prompt that defines the assistant's role"""
        return """You are a task management assistant for someone with ADHD, CPTSD, and short-term memory loss.

Your job:
1. Understand cryptic/short task inputs (user knows what they mean)
2. Assess REAL priority based on human needs, not just urgency
3. Identify patterns (keeps mentioning food = probably hasn't eaten)
4. Flag life-critical items (meds, food, hydration, health)
5. Note quick wins (fast tasks to build momentum)
6. Don't ask questions - work with what you have

Priority hierarchy:
- CRITICAL (0.9-1.0): Health, safety, meds, basic needs (food/water)
- HIGH (0.7-0.8): Time-sensitive, blocking other tasks, been stuck on this for days
- MEDIUM (0.5-0.6): Normal importance, should do
- LOW (0.3-0.4): Nice to have
- LATER (0.0-0.2): Ideas, interesting but not urgent (these are DISTRACTIONS)

Return ONLY valid JSON array, one object per task, no other text."""

    def _build_context_prompt(
        self,
        new_tasks: List[Dict[str, Any]],
        existing_tasks: List[Dict[str, Any]],
    ) -> str:
        """Build the prompt with full context"""
        prompt = "# New tasks to process:\n\n"

        for i, task in enumerate(new_tasks, 1):
            prompt += f"{i}. Raw input: \"{task['raw_input']}\"\n"
            if task.get("created_at"):
                prompt += f"   Created: {task['created_at']}\n"

        if existing_tasks:
            prompt += f"\n# Current active tasks ({len(existing_tasks)} total):\n\n"
            # Show top 10 by priority
            active_sample = sorted(
                existing_tasks,
                key=lambda x: x.get('priority_score', 0),
                reverse=True
            )[:10]

            for task in active_sample:
                prompt += f"- {task.get('processed_text', task.get('raw_input', 'Unknown'))}\n"
                prompt += f"  Priority: {task.get('priority_score', 0):.2f}, "
                prompt += f"Category: {task.get('category', 'none')}\n"

        prompt += """

# For each new task, return JSON object with:
- processed_text: Your understanding of what they mean
- priority_score: Number 0.0-1.0 (use the hierarchy above)
- category: Short category name (shopping, health, tech, etc.)
- is_life_critical: true/false (is this about survival/health?)
- is_quick_win: true/false (can be done in <10 min?)
- notes: Brief context or observations

Return as JSON array: [{"processed_text": "...", "priority_score": 0.8, ...}, ...]
"""
        return prompt

    def _parse_response(
        self,
        response: str,
        new_tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Parse LLM response into structured task updates"""
        try:
            # Find JSON array in response
            start = response.find("[")
            end = response.rfind("]") + 1

            if start >= 0 and end > start:
                json_str = response[start:end]
                parsed = json.loads(json_str)

                # Validate we got the right number of results
                if isinstance(parsed, list) and len(parsed) == len(new_tasks):
                    return parsed
        except Exception as e:
            print(f"Error parsing response: {e}")
            print(f"Response was: {response[:500]}")

        # Fallback: return default values for each task
        return [
            {
                "processed_text": task["raw_input"],
                "priority_score": 0.5,
                "category": "misc",
                "is_life_critical": False,
                "is_quick_win": False,
                "notes": "Could not process automatically",
            }
            for task in new_tasks
        ]

    async def reprocess_task(
        self,
        task: Dict[str, Any],
        context: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Reprocess a single task (for manual refresh or updates)"""
        result = await self.process_new_tasks([task], context or [])
        return result[0] if result else {}

    async def get_suggestions(
        self,
        current_tasks: List[Dict[str, Any]],
        user_state: Optional[str] = None
    ) -> str:
        """
        Get AI suggestions for what to do next
        Optional user_state: "stuck", "hyperfocused", "low_energy", etc.
        """
        system_prompt = """You are helping someone with ADHD decide what to do next.
Be supportive but direct. Suggest 1-3 specific tasks based on:
- Priority (life critical first)
- Their current state
- Quick wins if they're stuck
- Pattern breaking if hyperfocused on low-priority items

Keep it brief and actionable."""

        # Build prompt
        prompt = "# Current tasks:\n\n"

        # Show top tasks by priority
        sorted_tasks = sorted(
            current_tasks,
            key=lambda x: x.get('priority_score', 0),
            reverse=True,
        )[:15]

        for task in sorted_tasks:
            priority = task.get('priority_score', 0)
            text = task.get('processed_text', task.get('raw_input', 'Unknown'))
            flags = []
            if task.get('is_life_critical'):
                flags.append("LIFE CRITICAL")
            if task.get('is_quick_win'):
                flags.append("quick win")

            flag_str = f" [{', '.join(flags)}]" if flags else ""
            prompt += f"- [{priority:.2f}] {text}{flag_str}\n"

        if user_state:
            prompt += f"\nUser state: {user_state}\n"

        prompt += "\nWhat should they focus on next?"

        response = await self._call_model(prompt, system_prompt, temperature=0.5)
        return response


# Global instance (can be overridden via config)
_processor = None


def get_processor() -> TaskProcessor:
    """Get or create the global task processor"""
    global _processor
    if _processor is None:
        model = os.getenv("TASK_MODEL", "gpt-oss-20b-assistant:latest")
        api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        _processor = TaskProcessor(model_name=model, api_base=api_base)
    return _processor
