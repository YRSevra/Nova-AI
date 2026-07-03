"""
main.py — Nova AI Assistant Entry Point
────────────────────────────────────────
This file starts everything. Run with:
    python main.py

What happens when you run this:
1. Config is loaded from config/config.yaml
2. All modules (wake word, STT, AI, TTS, memory) are initialized
3. Nova speaks a greeting
4. The main loop starts listening for the wake word
5. When "Hey Nova" is detected, Nova listens to your command
6. The command is processed and Nova responds
"""

import sys
import os

# ── Make sure we can import from the nova/ directory ────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel
from core.orchestrator import Orchestrator
from core.config_loader import load_config
from core.performance_monitor import PerformanceMonitor

console = Console()


def main():
    """Start Nova."""
    # ── Print startup banner ──────────────────────────────────────────────

    monitor = PerformanceMonitor()

    console.print(Panel.fit(
        "[bold purple]Nova AI Assistant[/bold purple]\n"
        "[dim]Personal macOS AI — Phase 1[/dim]",
        border_style="purple"
    ))

    # ── Load configuration ────────────────────────────────────────────────
    config_path = os.path.join(os.path.dirname(__file__), "config", "config.yaml")
    if not os.path.exists(config_path):
        console.print(
            "[red]ERROR:[/red] config/config.yaml not found.\n"
            "Run: [bold]cp config/config.example.yaml config/config.yaml[/bold]\n"
            "Then add your OpenAI API key."
        )
        sys.exit(1)

    config = load_config(config_path)
    console.print(f"[green]✓[/green] Config loaded")

    # ── Initialize and start Nova ─────────────────────────────────────────
    nova = Orchestrator(config)
    console.print(f"[green]✓[/green] Nova initialized — listening for wake word...")
    monitor.report()
    console.print(f'[dim]Say "[bold]Hey Nova[/bold]" to wake me up. Press Ctrl+C to quit.[/dim]\n')

    try:
        nova.run()
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye! Nova shutting down...[/dim]")
        nova.shutdown()


if __name__ == "__main__":
    main()
