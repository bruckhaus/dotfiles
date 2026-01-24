#!/usr/bin/env python3
"""
Perplexity RAG CLI - True retrieval-augmented generation with Perplexity API
Integrates local knowledge base with Perplexity AI for personalized responses
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def run_command(cmd: List[str], capture: bool = True) -> tuple[int, str]:
    """Run command and return (exit_code, output)."""
    try:
        if capture:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True
            )
            return result.returncode, result.stdout
        else:
            result = subprocess.run(cmd, check=True)
            return result.returncode, ""
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout + e.stderr


def retrieve_relevant_context(query: str, limit: int = 3) -> str:
    """Retrieve relevant chunks from local knowledge base."""
    print(f"🔍 Searching local KB for: {query}")
    
    # Use perplexity rag to get relevant content
    cmd = ["perplexity", "rag", "--limit", str(limit), query]
    exit_code, output = run_command(cmd)
    
    if exit_code != 0 or not output.strip():
        return ""
    
    return output


def query_perplexity_with_context(query: str, context: str) -> str:
    """Send query and context to Perplexity API."""
    context_content = ""
    
    if context:
        # Extract actual content from rag output
        context_content = extract_context_from_rag_output(context)
        print(f"🔍 DEBUG: Extracted context length: {len(context_content)}")
        if context_content:
            augmented_query = f"""Based on the following context about me, please answer my question.

CONTEXT:
{context_content}

QUESTION: {query}

Please provide a personalized response using the context when relevant. If the context doesn't contain relevant information, just answer normally."""
        else:
            augmented_query = query
    else:
        augmented_query = query
    
    print("🤖 Querying Perplexity with context...")
    if context_content:
        print(f"📝 Context preview: {context_content[:100]}..." if len(context_content) > 100 else f"📝 Context: {context_content}")
    
    cmd = ["perplexity", "ask", "--save-history", augmented_query]
    exit_code, output = run_command(cmd, capture=False)
    
    return "" if exit_code != 0 else output


def extract_context_from_rag_output(rag_output: str) -> str:
    """Extract actual context content from rag command output."""
    lines = rag_output.split('\n')
    content_lines = []
    
    in_content_section = False
    for line in lines:
        line_stripped = line.strip()
        
        # Skip all empty lines and separators
        if not line_stripped or line_stripped in ['─', '==', '----------------------------']:
            continue
            
        # Skip metadata lines
        if any([
            line.startswith('🔎'),
            'Keyword search' in line,
            line.startswith('📋'),
            'results:' in line.lower(),
            line.startswith('[') and any(x in line for x in ['Score:', 'CHAT_MESSAGE', 'NOTE']),
            'Score:' in line,
            'User asked:' in line,
            'Based on these notes:' in line,
        ]):
            continue
        
        # Found actual content - add it
        if line_stripped and not line.startswith('Content:'):
            content_lines.append(line_stripped)
    
    context = '\n'.join(content_lines)
    return context


def save_interaction(query: str, response: str, context_used: bool) -> None:
    """Save interaction to local notes for future retrieval."""
    import tempfile
    import time
    
    timestamp = int(time.time())
    title = f"Interaction: {query[:50]}{'...' if len(query) > 50 else ''}"
    
    content = f"""Query: {query}

Response: {response}

Context used: {context_used}
Timestamp: {timestamp}"""
    
    cmd = [
        "perplexity", "note", 
        "--title", title,
        "--content", content,
        "--tag", "interaction"
    ]
    
    # Run in background to not block
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    parser = argparse.ArgumentParser(
        description="True RAG with Perplexity AI - local KB + Perplexity API"
    )
    parser.add_argument("query", help="Your question or query")
    parser.add_argument(
        "--context-limit", type=int, default=3,
        help="Number of context chunks to retrieve (default: 3)"
    )
    parser.add_argument(
        "--save", action="store_true", default=True,
        help="Save interaction to KB (default: True)"
    )
    parser.add_argument(
        "--no-save", dest="save", action="store_false",
        help="Don't save interaction to KB"
    )
    parser.add_argument(
        "--force-perplexity", action="store_true",
        help="Skip local search, go directly to Perplexity"
    )
    
    args = parser.parse_args()
    
    # Check API key
    if not os.environ.get("PERPLEXITY_API_KEY"):
        print("❌ PERPLEXITY_API_KEY not found. Please set it in your environment.")
        sys.exit(1)
    
    try:
        if args.force_perplexity:
            context = ""
            print("⚡ Skipping local KB (forced mode)")
        else:
            context = retrieve_relevant_context(args.query, args.context_limit)
        
        if context:
            print(f"📚 Found relevant context ({len(context)} chars)")
            print("-" * 50)
        else:
            print("🔍 No relevant context found, using pure Perplexity")
        
        response = query_perplexity_with_context(args.query, context)
        
        if args.save and response:
            save_interaction(args.query, response, bool(context))
            print("💾 Interaction saved to KB")
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()