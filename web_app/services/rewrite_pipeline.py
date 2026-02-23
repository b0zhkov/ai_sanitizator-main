
import asyncio
import json
import time

try:
    import llm_validator
    from rewriting_agent import rewriting_agent
    from post_humanizer import humanize
except ImportError:
    # These might fail if run in isolation or if paths aren't set up yet, 
    # but the app sets paths in main.py. 
    # We will assume they are importable when running from main.
    pass

from web_app.routes_history import save_history_entry

async def rewrite_stream_generator(
    raw_text: str,
    clean_text_val: str,
    request, 
    db, 
    user,
    changes_list: list,
    t0: float, 
    strength: str = "medium"
):
    """
    Generator that handles the entire rewrite pipeline:
    1. Validation/Stats
    2. Critique
    3. Streaming Rewrite
    4. Humanization
    5. Verification
    6. History Saving
    """
    print(f"[TIMING] Start processing...")

    yield json.dumps({
        "type": "stage", 
        "data": {
            "step": "clean",
            "clean_text": clean_text_val
        }
    }) + "\n"

    t1 = time.time()
    
    # 1. Stats Collection
    stats = await asyncio.to_thread(llm_validator.collect_stats, clean_text_val)
    print(f"[TIMING] Stats collection took: {time.time() - t1:.2f}s")

    # 2. Critique (Async Task)
    critique_task = asyncio.create_task(
        asyncio.to_thread(llm_validator.get_llm_critique, clean_text_val, stats)
    )

    analysis_for_rewrite = {"statistical_metrics": stats, "llm_critique": None}
    
    yield json.dumps({
        "type": "stage",
        "data": { "step": "analyzed" }
    }) + "\n"

    # 3. Streaming Rewrite
    rewritten_chunks_gen = []
    t2 = time.time()
    try:
        async for chunk in rewriting_agent.stream_rewrite(clean_text_val, analysis_for_rewrite):
            if chunk and isinstance(chunk, str):
                rewritten_chunks_gen.append(chunk)
                yield json.dumps({"type": "chunk", "data": chunk}) + "\n"
    except Exception as e:  
        print(f"Rewrite error: {e}")
        yield json.dumps({"type": "error", "data": str(e)}) + "\n"
    
    print(f"[TIMING] Rewriting (Streaming) took: {time.time() - t2:.2f}s")
        
    raw_rewritten_text = "".join(rewritten_chunks_gen)

    yield json.dumps({
        "type": "stage",
        "data": { "step": "humanizing" }
    }) + "\n"

    # 4. Humanization
    t3 = time.time()
    rewritten_text_final = await asyncio.to_thread(humanize, raw_rewritten_text, strength)
    print(f"[TIMING] Humanization (Post-processing) took: {time.time() - t3:.2f}s")

    yield json.dumps({
        "type": "stage",
        "data": { "step": "verifying" }
    }) + "\n"

    # 5. Verification
    t4 = time.time()
    rewritten_analysis = await asyncio.to_thread(
        llm_validator.verify_metrics_only, rewritten_text_final
    )
    print(f"[TIMING] Verification (Metrics) took: {time.time() - t4:.2f}s")

    final_changes = list(changes_list)
    final_changes.append({
        "description": "Applied AI Rewriting (Clean + Rewrite)  ",
        "text_before": clean_text_val,
        "text_after": rewritten_text_final
    })

    print(f"[TIMING] Results ready at: {time.time() - t0:.2f}s")

    # 6. History Saving
    if user:
        save_history_entry(
            db, user.id, "rewrite", request_text=raw_text, result_text=rewritten_text_final
        )
        # Note: 'request_text' argument name in save_history_entry might be 'text'.
        # Checking logic calls: save_history_entry(db, user.id, "rewrite", text, rewritten_text_final)
        # The original code passed 'text' (the original input). 
        # Here I passed 'clean_text_val'. Let me check the original code again.
        # Line 197: save_history_entry(db, user.id, "rewrite", text, rewritten_text_final)
        # It used 'text' (the raw input). 
        # I need to pass 'text' (raw input) to this function or handle it.
        # I should add 'raw_text' as argument to this function.

    yield json.dumps({
        "type": "done",
        "data": {
            "clean_text": clean_text_val,
            "rewritten_text": rewritten_text_final,
            "changes": final_changes,
            "rewritten_metrics": rewritten_analysis.get("statistical_metrics", {})
        }
    }) + "\n"

    t5 = time.time()
    try:
        llm_critique = await critique_task
    except Exception:
        llm_critique = {}
    ai_score = llm_critique.get("ai_score", 0.0)
    print(f"[TIMING] LLM Critique waited: {time.time() - t5:.2f}s")
    print(f"[TIMING] Total Process took: {time.time() - t0:.2f}s")

    yield json.dumps({
        "type": "ai_score",
        "data": {
            "score": ai_score,
            "critique": llm_critique
        }
    }) + "\n"
