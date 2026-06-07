from fastapi import APIRouter, HTTPException
from backend.models import AIAssistRequest, AIAssistResponse
from backend.agents.engine import run_agent

router = APIRouter(prefix="/api/jobs/{job_id}/ai-assist", tags=["ai-assist"])

AI_ASSIST_PROMPT = """你是小说转剧本管线的AI辅助编辑。用户会给你当前的阶段数据，以及一句自然语言修改指令。
请根据指令修改数据并返回完整的修改后数据。

重要规则：
1. 只修改用户指令中提到的部分，其他部分保持不变
2. 返回完整的数据对象（不能只返回修改的部分）
3. 保持数据结构与输入完全一致
4. 如果指令模糊，做最合理的解释

返回格式必须是一个JSON对象，包含以下字段：
- "data": 修改后的完整数据（与输入的 current_data 结构相同）
"""


@router.post("", response_model=AIAssistResponse)
async def ai_assist_edit(job_id: int, req: AIAssistRequest):
    try:
        context = {
            "stage": req.stage,
            "instruction": req.instruction,
            "current_data": req.current_data,
        }
        result = await run_agent(AI_ASSIST_PROMPT, context)
        return AIAssistResponse(data=result.get("data", result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI assist failed: {str(e)}")
