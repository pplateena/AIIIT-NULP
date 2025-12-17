#!/usr/bin/env python3
"""
Simple markdown renderer for CLI output
"""
import re

class SimpleMarkdownRenderer:
    """Simple markdown renderer for CLI output"""
    
    def render(self, text: str) -> str:
        """Render markdown text for CLI display"""
        # Don't render if text is too short or doesn't contain markdown
        if len(text) < 50 or not self._has_markdown(text):
            return text
        
        lines = text.split('\n')
        rendered_lines = []
        
        for line in lines:
            rendered_line = self._render_line(line)
            rendered_lines.append(rendered_line)
        
        return '\n'.join(rendered_lines)
    
    def _has_markdown(self, text: str) -> bool:
        """Check if text contains markdown formatting"""
        patterns = [
            r'\*\*.*?\*\*',  # Bold
            r'`.*?`',        # Code
            r'\[.*?\]\(.*?\)',  # Links
            r'^#{1,6}\s',    # Headers
            r'^\s*[-*+]\s',  # Lists
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.MULTILINE):
                return True
        return False
    
    def _render_line(self, line: str) -> str:
        """Render a single line of markdown"""
        # Headers
        line = re.sub(r'^(#{1,6})\s(.+)$', self._render_header, line)
        
        # Bold text
        line = re.sub(r'\*\*(.*?)\*\*', r'\033[1m\1\033[0m', line)
        
        # Inline code
        line = re.sub(r'`([^`]+)`', r'\033[96m\1\033[0m', line)
        
        # Links - extract URL and show it
        line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', self._render_link, line)
        
        # List items
        if re.match(r'^\s*[-*+]\s', line):
            line = re.sub(r'^(\s*)[-*+]\s(.+)$', r'\1• \2', line)
        
        return line
    
    def _render_header(self, match) -> str:
        """Render header with appropriate styling"""
        level = len(match.group(1))
        text = match.group(2)
        
        if level == 1:
            return f'\033[1;4m{text}\033[0m'  # Bold + underline
        elif level == 2:
            return f'\033[1;36m{text}\033[0m'  # Bold + cyan
        else:
            return f'\033[1m{text}\033[0m'  # Just bold
    
    def _render_link(self, match) -> str:
        """Render link with URL shown"""
        text = match.group(1)
        url = match.group(2)
        return f'\033[94m{text}\033[0m \033[90m({url})\033[0m'

def render_markdown(text: str) -> str:
    """Convenience function to render markdown"""
    renderer = SimpleMarkdownRenderer()
    return renderer.render(text)