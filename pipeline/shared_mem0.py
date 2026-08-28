#!/usr/bin/env python3
"""Shared mem0 memory layer for clips-channel agents (Content Agent + Posting Agent).

Usage:
    from shared_mem0 import memory, add_memory, search_memory, add_posting_event, log_manual_intervention

Agents call these helpers to persist and retrieve memories across runs. The same
chroma store + anthropic LLM extracts facts from both agents' messages into one
shared vector store, scoped by user_id to keep agent memories separable but searchable.

Backend:
    LLM:      nous/upstage-solar-pro4:free, OpenAI-compatible endpoint
              (api_key + base_url from ~/.hermes/auth.json, free tier)
    Embedder: fastembed (local, no API key needed)
    Vector:   chroma at /tmp/mem0_chroma_mem0

User IDs:
    posting_agent  — posting events, platform status, manual interventions
    content_agent  — sourcing decisions, production notes, quality judgments
"""

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, '/home/leo/.hermes/hermes-agent/venv/lib/python3.11/site-packages')

# Load a Nous free-tier token once at import time. Hermes itself runs entirely
# on free models (see /home/leo/.hermes/coS/index.md) — this mirrors that,
# rather than depending on Anthropic credits/quota this pipeline doesn't have.
_AUTH_PATH = Path('/home/leo/.hermes/auth.json')
_AUTH_CACHE_TTL = 1800  # 30 min

cached_token = None
cached_base_url = None
cached_token_time = 0


def _load_nous_credential(force=False):
    """Load a working Nous api_key credential (stable, non-expiring) from auth.json."""
    global cached_token, cached_base_url, cached_token_time
    if cached_token and not force and (time.time() - cached_token_time) < _AUTH_CACHE_TTL:
        return cached_token, cached_base_url
    try:
        with open(_AUTH_PATH) as f:
            auth = json.load(f)
        # Prefer a manual api_key credential (stable) over the hourly-expiring
        # device_code OAuth one — avoids needing token-refresh logic here.
        best = None
        for c in auth['credential_pool'].get('nous', []):
            if c.get('auth_type') == 'api_key' and c.get('access_token'):
                best = c
                break
        if best is None:
            for c in auth['credential_pool'].get('nous', []):
                if c.get('access_token'):
                    best = c
                    break
        if best:
            cached_token = best['access_token']
            cached_base_url = best.get('base_url') or best.get('inference_base_url') \
                or 'https://inference-api.nousresearch.com/v1'
            cached_token_time = time.time()
            return cached_token, cached_base_url
    except Exception as e:
        raise RuntimeError(f'Failed to load Nous credential from {_AUTH_PATH}: {e}')
    raise RuntimeError('No working Nous credential found in auth.json')


from mem0.configs.base import MemoryConfig, VectorStoreConfig, LlmConfig, EmbedderConfig
from mem0 import Memory

_nous_key, _nous_base_url = _load_nous_credential()

# Singleton Memory instance — all agents share the same store
_config = MemoryConfig(
    vector_store=VectorStoreConfig(provider='chroma', config={'path': '/tmp/mem0_chroma_mem0'}),
    llm=LlmConfig(provider='openai', config={
        'model': 'upstage/solar-pro4:free',
        'api_key': _nous_key,
        'openai_base_url': _nous_base_url,
    }),
    embedder=EmbedderConfig(provider='fastembed'),
)
_memory = Memory(config=_config)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def memory():
    """Return the shared Memory instance (for advanced use)."""
    return _memory


def add_memory(messages, user_id='posting_agent', agent_id=None, metadata=None,
               infer=False):
    """Add a memory to the shared store.

    Args:
        messages: str or list of message dicts (same format as mem0.Memory.add)
        user_id:   'posting_agent' or 'content_agent' (scopes the memory)
        agent_id:  optional agent instance identifier
        metadata:  optional dict with clip_id, platform, event_type, etc.
        infer:     passed through to mem0's LLM fact-extraction step.
                   Defaults to False because the Nous inference API rejects
                   the configured model ('upstage/solar-pro4:free') with a
                   'missing tags' 400 error — raw text is stored verbatim when
                   infer=False, preserving semantic search via fastembed.
                   Set infer=True only if the LLM config is validated.
    """
    if not agent_id:
        agent_id = user_id
    kwargs = dict(
        messages=messages,
        user_id=user_id,
        agent_id=agent_id,
        metadata=metadata or {},
    )
    if 'infer' in _memory.add.__code__.co_varnames:
        kwargs['infer'] = infer
    return _memory.add(**kwargs)


def search_memory(query, user_id='posting_agent', top_k=10,
                  filters=None, threshold=0.1):
    """Search memories. By default scoped to one agent; pass filters={} for all."""
    if filters is None:
        filters = {'user_id': user_id}
    elif 'user_id' not in filters:
        filters = {'user_id': user_id, **filters}
    return _memory.search(
        query=query,
        filters=filters,
        top_k=top_k,
        threshold=threshold,
    )


def add_posting_event(clip_id, platform, status, url=None, post_id=None,
                      error=None, caption=None, retry_count=0):
    """Record a posting event (called by Posting Agent after each platform attempt).

    Args:
        clip_id:     e.g. 'tb004_c2_france_tornado'
        platform:    'youtube', 'tiktok', 'instagram', 'x'
        status:      'posted', 'failed', 'skipped', 'deleted'
        url:         public URL if available
        post_id:     platform post/video ID
        error:       error message if failed
        caption:     description used (first 300 chars)
        retry_count: number of retry attempts for this platform
    """
    lines = [
        f'POSTING EVENT: {clip_id}',
        f'Platform: {platform}',
        f'Status: {status}',
    ]
    if url:
        lines.append(f'URL: {url}')
    if post_id:
        id_label = 'Video ID' if platform == 'youtube' else 'Media ID'
        lines.append(f'{id_label}: {post_id}')
    if error:
        lines.append(f'Error: {error[:200]}')
    if caption:
        lines.append(f'Caption: {caption[:300]}')
    if retry_count:
        lines.append(f'Retry count: {retry_count}')

    content = '\n'.join(lines)

    metadata = {
        'clip_id': clip_id,
        'platform': platform,
        'event_type': 'posting_event',
        'status': status,
    }
    if post_id:
        metadata['post_id'] = post_id
    if url:
        metadata['url'] = url

    return add_memory(
        messages=[{'role': 'user', 'content': content}],
        user_id='posting_agent',
        agent_id='posting_agent',
        metadata=metadata,
    )


def log_manual_intervention(clip_id, platform, action, note, timestamp=None):
    """Record a manual intervention by Leo (deletion, unlisting, etc.).

    Called by the Posting Agent when it observes or is told about a manual change,
    OR called externally (e.g. from a webhook or Leo's command) to record it.

    Args:
        clip_id:     e.g. 'tb004_c2_france_tornado'
        platform:    'instagram', 'youtube', 'tiktok', 'x', 'all'
        action:      'deleted', 'unlisted', 're-listed', 'flagged', 'other'
        note:        free-form explanation (e.g. 'video too blurry')
        timestamp:   ISO timestamp or None (current time)
    """
    lines = [
        f'MANUAL INTERVENTION: {clip_id}',
        f'Platform: {platform}',
        f'Action: {action}',
        f'Note: {note}',
    ]
    if timestamp:
        lines.append(f'Timestamp: {timestamp}')

    content = '\n'.join(lines)

    return add_memory(
        messages=[{'role': 'user', 'content': content}],
        user_id='posting_agent',
        agent_id='posting_agent',
        metadata={
            'clip_id': clip_id,
            'platform': platform,
            'event_type': 'manual_intervention',
            'action': action,
        },
    )


def get_clip_context(clip_id, platforms=None):
    """Retrieve all stored context for a specific clip from both agents.

    Hard-filters on metadata['clip_id'] (set by add_posting_event/
    log_manual_intervention) rather than relying on semantic-search proximity
    alone — two clips about similar topics can otherwise rank in each other's
    top-20 results, causing a posting-status lookup for one clip to pick up
    another clip's history.

    Returns a dict with:
        posting_history:  list of posting event memories
        content_notes:    list of content agent production notes
        interventions:    list of manual intervention memories
    """
    all_results = {}
    for agent_id in ('posting_agent', 'content_agent'):
        results = _memory.search(
            query=f'{clip_id} posting history status platforms',
            filters={'user_id': agent_id, 'agent_id': agent_id},
            top_k=20,
        )
        all_results[agent_id] = results

    posting_history = []
    content_notes = []
    interventions = []

    for agent_id, results in all_results.items():
        for item in results.get('results', []):
            mem_text = item.get('memory', '')
            # mem0 can store/return an explicit `metadata: null`, not just an
            # absent key — `.get('metadata', {})` would still yield None in
            # that case since the key IS present, so fall back with `or {}`.
            metadata = item.get('metadata') or {}
            if not isinstance(mem_text, str):
                continue
            # Hard filter: only keep memories actually tagged for this clip.
            # Falls back to a text match only for older entries written before
            # metadata['clip_id'] was populated (or produced via a bare add_memory
            # call without metadata) — semantic-search proximity is not enough
            # on its own to scope this to one clip.
            if metadata.get('clip_id') != clip_id and clip_id not in mem_text:
                continue

            # Classify by metadata['event_type'] — NOT by searching mem_text for
            # literal marker strings like 'POSTING EVENT'. mem0 runs stored
            # content through an LLM fact-extraction step before saving, which
            # paraphrases it into natural language (e.g. "User posted a clip
            # named X to Instagram..." instead of the literal "POSTING EVENT:
            # X" that add_posting_event() originally wrote) — the literal
            # marker essentially never survives, so substring matching on
            # mem_text silently classified almost nothing. metadata is stored
            # structurally and is not touched by that rewrite, so it's the
            # only reliable signal here.
            event_type = metadata.get('event_type', '')
            if event_type == 'posting_event':
                posting_history.append({'agent': agent_id, 'memory': item})
            elif event_type == 'manual_intervention':
                interventions.append({'agent': agent_id, 'memory': item})
            elif event_type:
                # Any other explicit event_type (e.g. 'sourcing_candidate' from
                # the Content Agent) is treated as a content note.
                content_notes.append({'agent': agent_id, 'memory': item})
            elif 'POSTING EVENT' in mem_text or 'POSTING HISTORY' in mem_text:
                # Fallback for legacy entries with no event_type metadata.
                posting_history.append({'agent': agent_id, 'memory': item})
            elif 'MANUAL INTERVENTION' in mem_text:
                interventions.append({'agent': agent_id, 'memory': item})
            elif 'CONTENT AGENT NOTE' in mem_text or 'PRODUCTION' in mem_text:
                content_notes.append({'agent': agent_id, 'memory': item})

    return {
        'clip_id': clip_id,
        'posting_history': posting_history,
        'content_notes': content_notes,
        'interventions': interventions,
    }


def check_before_post(clip_id, platform):
    """Check if a clip has been posted, deleted, or failed on a platform.

    Returns a dict:
        { 'action': 'post' | 'skip' | 'investigate',
          'reason': str,
          'existing_post_url': str or None,
          'was_deleted': bool,
          'retry_count': int,
        }
    """
    context = get_clip_context(clip_id)

    was_deleted = False
    existing_url = None
    retry_count = 0
    last_error = None

    for entry in context['posting_history']:
        mem = entry['memory']
        mem_text = mem.get('memory', '')
        meta = mem.get('metadata') or {}  # metadata can be an explicit None, not just absent

        if meta.get('platform') != platform:
            continue

        if meta.get('status') == 'deleted' or 'deleted by Leo' in mem_text:
            was_deleted = True
        elif meta.get('status') == 'posted':
            existing_url = meta.get('url')
        elif meta.get('status') == 'failed':
            last_error = meta.get('error', '') or ''
            retry_count = max(retry_count, meta.get('retry_count', 0))

    if was_deleted:
        return {
            'action': 'investigate',
            'reason': f'This clip was previously posted to {platform} but Leo deleted it. '
                      f'Need to confirm whether to repost.',
            'existing_post_url': None,
            'was_deleted': True,
            'retry_count': retry_count,
        }

    if existing_url:
        return {
            'action': 'skip',
            'reason': f'Already posted to {platform}: {existing_url}',
            'existing_post_url': existing_url,
            'was_deleted': False,
            'retry_count': retry_count,
        }

    if last_error and retry_count >= 3:
        return {
            'action': 'skip',
            'reason': f'Failed to post to {platform} {retry_count} times. '
                      f'Last error: {last_error[:150]}. Needs manual review.',
            'existing_post_url': None,
            'was_deleted': False,
            'retry_count': retry_count,
        }

    return {
        'action': 'post',
        'reason': f'No successful post found for {platform}. Ready to post.',
        'existing_post_url': None,
        'was_deleted': False,
        'retry_count': retry_count,
    }


if __name__ == '__main__':
    # Self-test
    print('=== Shared mem0 self-test ===')
    print(f'Memory instance: {_memory}')
    print()

    print('Search for TB-004-C2 context:')
    ctx = get_clip_context('tb004_c2_france_tornado')
    print(f'  posting_history: {len(ctx["posting_history"])} entries')
    print(f'  content_notes:   {len(ctx["content_notes"])} entries')
    print(f'  interventions:   {len(ctx["interventions"])} entries')
    for entry in ctx['posting_history']:
        print(f'    - {entry["memory"].get("memory", "")[:100]}...')
    for entry in ctx['interventions']:
        print(f'    - {entry["memory"].get("memory", "")[:100]}...')
    print()

    print('check_before_post TB-004-C2 instagram:')
    check = check_before_post('tb004_c2_france_tornado', 'instagram')
    print(f'  {json.dumps(check, indent=2)}')
    print()

    print('check_before_post TB-004-C1 youtube:')
    check2 = check_before_post('tb004_c1_canada_tariffs', 'youtube')
    print(f'  {json.dumps(check2, indent=2)}')
