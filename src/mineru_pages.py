"""Convert MinerU content lists to pages; internal page numbers are one-based."""
import json
from collections import defaultdict
from pathlib import Path


def _text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return '\n'.join(filter(None, (_text(item) for item in value)))
    return ''


def _middle_block_text(block):
    """Use final paragraph blocks once; retain HTML tables and nested captions."""
    if block.get('blocks'):
        return '\n\n'.join(filter(None, (_middle_block_text(child)
                                        for child in block['blocks'])))
    lines = []
    for line in block.get('lines', []):
        spans = []
        for span in line.get('spans', []):
            value = span.get('html') or span.get('content', '')
            if isinstance(value, str):
                spans.append(value)
        lines.append(''.join(spans))
    return '\n'.join(lines).strip()


def _middle_pages(data, source):
    pages = []
    seen = set()
    for item in data['pdf_info']:
        index = item.get('page_idx')
        if type(index) is not int or index < 0 or index in seen:
            raise ValueError(f'{source}: 无效或重复的 page_idx: {index!r}')
        seen.add(index)
        blocks = item.get('para_blocks')
        if blocks is None:
            blocks = item.get('preproc_blocks', [])
        text = '\n\n'.join(filter(None, (_middle_block_text(b) for b in blocks)))
        pages.append({'page': index + 1, 'text': text})
    if not pages or not any(p['text'].strip() for p in pages):
        raise ValueError(f'{source}: 没有可分块的带页码文本')
    return sorted(pages, key=lambda p: p['page'])


def load_mineru_parts(result_dir, parts):
    """parts explicitly specifies (filename, original PDF offset, page count)."""
    merged = []
    sources = []
    seen = set()
    for filename, offset, count in parts:
        if type(offset) is not int or offset < 0 or type(count) is not int or count < 1:
            raise ValueError('页码偏移必须为非负整数，页数必须为正整数')
        pages, source = load_mineru_pages(Path(result_dir) / filename)
        if [p['page'] for p in pages] != list(range(1, count + 1)):
            raise ValueError(f'{source}: 必须包含连续的 {count} 页，实际为 {len(pages)} 页')
        for page in pages:
            number = page['page'] + offset
            if number in seen:
                raise ValueError(f'分段页码重叠: {number}')
            seen.add(number)
            merged.append({'page': number, 'text': page['text']})
        sources.append({'file': str(source), 'page_offset': offset, 'page_count': count})
    if not merged or sorted(seen) != list(range(1, len(merged) + 1)):
        raise ValueError('合并后的 PDF 页码不连续或没有内容')
    return sorted(merged, key=lambda p: p['page']), sources


def load_mineru_pages(result_dir: Path):
    """Read the legacy content list emitted by MinerU (including current backends).

    Preserve reading order within pages and HTML tables. Never infer PDF page
    numbers from Markdown lines or printed page-number text.
    """
    result_dir = Path(result_dir)
    if not result_dir.exists():
        raise FileNotFoundError(f'MinerU 结果路径不存在: {result_dir}')
    candidates = ([result_dir] if result_dir.is_file() else
                  sorted(set(result_dir.rglob('*_content_list.json')) |
                         set(result_dir.rglob('content_list.json'))))
    if not candidates:
        candidates = [p for p in sorted(result_dir.rglob('*.json'))
                      if isinstance((data := json.loads(p.read_text(encoding='utf-8'))), dict)
                      and isinstance(data.get('pdf_info'), list)]
    if len(candidates) != 1:
        available = ', '.join(str(p.relative_to(result_dir))
                              for p in result_dir.rglob('*.json'))
        raise ValueError(
            f'{result_dir}: 需要唯一的内容列表或 pdf_info JSON；多段报告请显式指定文件和页码偏移，'
            f'找到 {len(candidates)} 个。请重新解析并保留完整结果。JSON 文件: {available}'
        )
    source = candidates[0]
    blocks = json.loads(source.read_text(encoding='utf-8'))
    if isinstance(blocks, dict) and isinstance(blocks.get('pdf_info'), list):
        return _middle_pages(blocks, source), source
    if not isinstance(blocks, list):
        raise ValueError(f'{source}: 内容列表必须是数组')
    pages = defaultdict(list)
    for block in blocks:
        if not isinstance(block, dict):
            raise ValueError(f'{source}: 内容块必须是对象')
        index = block.get('page_idx')
        if type(index) is not int or index < 0:
            raise ValueError(f'{source}: 内容块缺少有效的 page_idx: {index!r}')
        parts = pages[index + 1]
        fields = ('text', 'table_caption', 'table_body', 'table_footnote',
                  'image_caption', 'image_footnote', 'chart_caption', 'content',
                  'chart_footnote', 'code_caption', 'code_body', 'code_footnote',
                  'list_items')
        for field in fields:
            value = _text(block.get(field))
            if value.strip():
                parts.append(value)
    if not pages or not any(pages.values()):
        raise ValueError(f'{source}: 没有可分块的带页码文本')
    return [{'page': page, 'text': '\n\n'.join(parts)}
            for page, parts in sorted(pages.items())], source
