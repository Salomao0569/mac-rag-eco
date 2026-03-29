"""Observability — structured logging for queries, tool calls, and latency."""

import functools
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
QUERY_LOG = os.path.join(LOG_DIR, 'queries.jsonl')


def _ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def _log_event(event: dict):
    """Append a JSON event to the query log file."""
    _ensure_log_dir()
    event['timestamp'] = datetime.now(timezone.utc).isoformat()
    try:
        with open(QUERY_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False, default=str) + '\n')
    except Exception as e:
        logger.warning(f"Failed to write query log: {e}")


def observe(func):
    """Decorator that logs function calls with timing and metadata.

    Works on tool functions (rag_search, pubmed_search, etc.) and
    on team_builder.ask() / build_single_agent.run().
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        event = {
            'function': getattr(func, '__name__', getattr(func, 'name', str(func))),
            'module': getattr(func, '__module__', ''),
            'args_summary': _summarize_args(args, kwargs),
        }

        try:
            result = func(*args, **kwargs)
            elapsed_ms = (time.perf_counter() - start) * 1000

            event['status'] = 'success'
            event['latency_ms'] = round(elapsed_ms, 1)
            event['result_summary'] = _summarize_result(result)

            _log_event(event)
            logger.debug(f"[observe] {func.__name__} completed in {elapsed_ms:.0f}ms")

            return result
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            event['status'] = 'error'
            event['latency_ms'] = round(elapsed_ms, 1)
            event['error'] = f"{type(e).__name__}: {e}"
            _log_event(event)
            raise

    return wrapper


def _summarize_args(args, kwargs):
    """Extract meaningful info from args without logging full content."""
    summary = {}
    # First positional arg is usually the query
    if args:
        first = args[0]
        if isinstance(first, str) and len(first) < 500:
            summary['query'] = first
        elif isinstance(first, str):
            summary['query'] = first[:200] + '...'
    # Named args
    for key in ('query', 'ano', 'sociedade', 'n_resultados', 'model_coord', 'model_agents', 'fonte'):
        if key in kwargs:
            summary[key] = kwargs[key]
    return summary


def _summarize_result(result):
    """Extract summary from result without logging full content."""
    if result is None:
        return {'type': 'none'}
    if isinstance(result, str):
        # Count RAG chunks in result
        chunk_count = result.count('[Trecho ')
        return {
            'type': 'str',
            'length': len(result),
            'chunks_found': chunk_count if chunk_count > 0 else None,
        }
    if hasattr(result, 'content'):
        # Agno response object
        return {
            'type': 'response',
            'length': len(result.content) if result.content else 0,
        }
    return {'type': type(result).__name__}


def get_query_stats(last_n: int = 100) -> dict:
    """Read the last N query log entries and compute basic stats."""
    if not os.path.exists(QUERY_LOG):
        return {'total': 0}

    entries = []
    with open(QUERY_LOG, 'r') as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    entries = entries[-last_n:]
    if not entries:
        return {'total': 0}

    latencies = [e['latency_ms'] for e in entries if 'latency_ms' in e]
    errors = [e for e in entries if e.get('status') == 'error']
    by_function = {}
    for e in entries:
        fn = e.get('function', '?')
        by_function[fn] = by_function.get(fn, 0) + 1

    return {
        'total': len(entries),
        'errors': len(errors),
        'error_rate': f"{len(errors)/len(entries)*100:.1f}%",
        'avg_latency_ms': round(sum(latencies) / len(latencies), 1) if latencies else 0,
        'p95_latency_ms': round(sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0, 1),
        'by_function': by_function,
    }
