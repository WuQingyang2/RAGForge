"""Unwrap provider answer envelopes without losing validated provenance."""
import json


def normalize_answer(answer):
    if isinstance(answer, str):
        answer = json.loads(answer)
    if not isinstance(answer, dict):
        raise ValueError('返回内容不是有效的结构化答案')
    result = dict(answer)
    # Outer provenance has already been validated by the application.
    provenance = {k: answer[k] for k in ('references', 'relevant_pages')
                  if k in answer} if 'references' in answer else {}
    for _ in range(10):
        nested = result.get('content')
        if nested is None:
            nested = result.get('final_answer')
        if isinstance(nested, str):
            raw = nested.strip()
            if raw.startswith('```') and raw.endswith('```'):
                raw = raw.split('\n', 1)[-1].rsplit('```', 1)[0].strip()
            try:
                nested = json.loads(raw)
            except (ValueError, TypeError):
                break
        if not isinstance(nested, dict) or not any(
            key in nested for key in ('final_answer', 'content', 'relevant_pages')
        ):
            break
        result.pop('content', None)
        result.update(nested)
    result.update(provenance)
    return result
